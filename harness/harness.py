"""Frozen generic harness (docs/HARNESS.md). No application logic lives here.

It loads networks, runs forward passes, and obeys the fixed output fields.
Weight file format: harness/FORMAT.md. Version 2 (log/WORKLOG.md, decision H2):
block memory operations (mem_op 3 and 4) and a preparsed forward pass.
"""
import itertools
import random
import time

import numpy as np

# ---- Step protocol: fixed output fields (indices into every network output) ----
F_NEXT, F_MEMOP, F_ADDR, F_VALUE, F_IO, F_IOARG, F_HALT = range(7)
N_FIELDS = 7
MEM_NONE, MEM_READ, MEM_WRITE, MEM_BWRITE, MEM_BREAD = range(5)
BLOCK_SPLIT = 1 << 20  # block ops: value = K * BLOCK_SPLIT + N (K forwarded words, N block words)
IO_NONE, IO_DISPLAY, IO_FILE_IN, IO_FILE_OUT, IO_CLOCK, IO_ENTROPY, IO_EVENTS, IO_LOAD_NET = range(8)

# ---- Memory map: fixed designated regions (base, size) in words ----
MEM_SIZE = 1 << 22
FRAMEBUFFER = (0x100000, 0x100000)   # raw pixel words, presented as-is
INPUT_EVENTS = (0x200000, 0x1000)     # word 0: count of words that follow, then raw event words
FILE_XFER = (0x201000, 0x100000)      # word 0: byte count, then one byte per word
CLOCK = (0x301000, 1)                 # seconds since the Unix epoch
ENTROPY = (0x301001, 64)              # random bytes, one per word

ACTS = {
    "relu": lambda x: np.maximum(x, 0.0),
    "step": lambda x: (x > 0).astype(float),
    "identity": lambda x: x,
}

# Numeric codes for layer types when a generator network writes a network into memory.
MEM_CODES = {0: "end", 1: "dense", 2: "relu", 3: "step", 4: "identity", 5: "mul", 6: "slice", 7: "concat"}
# Preparsed opcodes used by the forward pass (same layer types, compact form).
OP = {"dense": 0, "relu": 1, "step": 2, "identity": 3, "mul": 4, "slice": 5, "concat": 6}


class Network:
    """A list of layers. Layer k reads the output of an earlier layer (0 = network input).

    The layers are preparsed once into tuples (opcode, src, params) of numpy arrays and ints.
    Each layer computes exactly the same numpy expression as harness v1, so results are
    bit-identical (docs/HARNESS.md, "Engine and bit-identity").
    """

    def __init__(self, n_in, layers):
        self.n_in, self.layers = n_in, layers
        prog = []
        for kind, a in layers:
            if kind == "dense":
                prog.append((0, a["src"], np.ascontiguousarray(a["W"], dtype=float),
                             np.ascontiguousarray(a["b"], dtype=float)))
            elif kind == "mul":
                prog.append((4, a["src"], (slice(a["a"], a["b"]), slice(a["c"], a["d"])), None))
            elif kind == "slice":
                prog.append((5, a["src"], slice(a["a"], a["b"]), None))
            elif kind == "concat":
                prog.append((6, a["src"], a["src2"], None))  # leaves filled in below
            elif kind in ACTS:
                prog.append((OP[kind], a["src"], None, None))
            else:
                raise ValueError(f"unknown layer type {kind}")
        # A concat of concats is one copy of its leaf pieces (concat only copies, so this is
        # exact). A concat whose value only feeds other concats is never materialised (op 7).
        # Only done when every source names an earlier value directly (0 <= src < k).
        self.prog = prog
        if not all(0 <= u < k for k, (op, src, p, b) in enumerate(prog, 1)
                   for u in ((src, p) if op == 6 else (src,))):
            self.prog = [(op, src, (src, p), b) if op == 6 else (op, src, p, b)
                         for op, src, p, b in prog]
            return
        leaves, users = {}, {}
        for k, (op, src, p, b) in enumerate(prog, 1):
            for u in ((src, p) if op == 6 else (src,)):
                users.setdefault(u, set()).add(op)
            if op == 6:
                leaves[k] = [q for u in (src, p) for q in leaves.get(u, [u])]
        last = len(prog)
        for k, (op, src, p, b) in enumerate(prog, 1):
            if op == 6:
                lazy = k != last and users.get(k, {6}) == {6}
                prog[k - 1] = (7 if lazy else 6, src, tuple(leaves[k]), None)
        self.prog = prog

    def forward(self, x):
        x = np.asarray(x, dtype=float)
        if x.shape != (self.n_in,):
            raise ValueError(f"input length {x.shape} != {self.n_in}")
        vals = [x]
        put = vals.append
        for op, src, p, b in self.prog:
            s = vals[src]
            if op == 0:            # dense: W @ v + b (one BLAS matvec, then one IEEE add per row)
                v = p @ s
                v += b
            elif op == 5:          # slice
                v = s[p]
            elif op == 1:          # relu
                v = np.maximum(s, 0.0)
            elif op == 6:          # concat (of all leaf pieces at once)
                v = np.concatenate([vals[q] for q in p])
            elif op == 7:          # concat consumed only by concats: not materialised
                v = None
            elif op == 4:          # mul (gating)
                v = s[p[0]] * s[p[1]]
            elif op == 2:          # step
                v = (s > 0).astype(float)
            else:                  # identity
                v = s
            put(v)
        return vals[-1]


def _build(tokens):
    """Build a Network from a flat token stream (shared by text files and memory)."""
    it = iter(tokens)
    nxt = lambda: next(it)
    assert str(nxt()) == "input"
    n_in, layers = int(nxt()), []
    for kind in it:
        kind = kind if isinstance(kind, str) else MEM_CODES[int(round(kind))]
        if kind == "end":
            break
        src = int(nxt())
        if kind == "dense":
            r, c = int(nxt()), int(nxt())
            W = np.array([float(nxt()) for _ in range(r * c)]).reshape(r, c)
            b = np.array([float(nxt()) for _ in range(r)])
            layers.append((kind, {"src": src, "W": W, "b": b}))
        elif kind in ACTS:
            layers.append((kind, {"src": src}))
        elif kind == "mul":
            a, b, c, d = (int(nxt()) for _ in range(4))
            layers.append((kind, {"src": src, "a": a, "b": b, "c": c, "d": d}))
        elif kind == "slice":
            layers.append((kind, {"src": src, "a": int(nxt()), "b": int(nxt())}))
        elif kind == "concat":
            layers.append((kind, {"src": src, "src2": int(nxt())}))
        else:
            raise ValueError(f"unknown layer type {kind}")
    return Network(n_in, layers)


_FILE_CACHE = {}  # file bytes -> Network. Networks are never mutated, so they can be shared.


def load_file(path):
    with open(path, "rb") as f:
        data = f.read()
    net = _FILE_CACHE.get(data)
    if net is None:
        text = data.decode()
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")  # as text-mode open
        toks = [t for line in lines for t in line.split("#")[0].split()]
        net = _FILE_CACHE[data] = _build(toks)
    return net


def load_memory(mem, addr):
    """Memory form: n_in, then per layer: type code, src, params..., then code 0 (end)."""
    return _build(itertools.chain(["input"], iter(mem[addr:])))


def _fields(out):
    """Fields 0 to 6 as Python ints, rounded half to even exactly as int(round(v)) in v1."""
    return [int(round(v)) for v in out[:N_FIELDS].tolist()]


def _block(f, out):
    """Bound-checked (addr, K, N) of a block op. value = K * BLOCK_SPLIT + N, both < BLOCK_SPLIT."""
    addr, v = f[F_ADDR], f[F_VALUE]
    if not 0 <= v < BLOCK_SPLIT * BLOCK_SPLIT:
        raise ValueError(f"block op value field {v} out of range")
    k, n = divmod(v, BLOCK_SPLIT)
    if addr < 0 or addr + n > MEM_SIZE:
        raise IndexError(f"block op range {addr}..{addr + n} outside memory")
    if k > len(out) or (f[F_MEMOP] == MEM_BWRITE and k + n > len(out)):
        raise IndexError(f"block op K={k} N={n} beyond output length {len(out)}")
    return addr, k, n


class Harness:
    def __init__(self, networks, files=(), events=(), display=None, trace=None):
        """networks: list of weight file paths (id = index). files: list of file paths (id = index)."""
        self.nets = [load_file(p) for p in networks]
        self.files, self.events = list(files), list(events)
        self.display, self.trace = display, trace
        self.mem = np.zeros(MEM_SIZE)

    def _log(self, *msg):
        if self.trace is not None:
            self.trace.append(" ".join(str(m) for m in msg))

    def run(self, net_id, x, max_steps=None):
        """Run requested steps until a network sets halt. max_steps is only a safety stop for tests."""
        steps = 0
        mem = self.mem
        while True:
            out = self.nets[net_id].forward(x)
            f = _fields(out)
            tracing = self.trace is not None
            if tracing:
                self._log("step", steps, "net", net_id, "out", list(out))
            read, fwd, block = 0.0, out, None
            op = f[F_MEMOP]
            if op == MEM_READ:
                read = mem[f[F_ADDR]]
                if tracing:
                    self._log("read", f[F_ADDR], read)
            elif op == MEM_WRITE:
                mem[f[F_ADDR]] = out[F_VALUE]
                if tracing:
                    self._log("write", f[F_ADDR], out[F_VALUE])
            elif op == MEM_BWRITE:
                a, k, n = _block(f, out)
                mem[a:a + n] = out[k:k + n]
                fwd = out[:k]
                if tracing:
                    self._log("bwrite", a, k, n)
            elif op == MEM_BREAD:
                a, k, n = _block(f, out)
                block = mem[a:a + n]
                fwd = out[:k]
                if tracing:
                    self._log("bread", a, k, n)
            if f[F_IO] != IO_NONE:
                self._io(f[F_IO], f[F_IOARG], f[F_ADDR], f[F_VALUE])
            steps += 1
            if f[F_HALT] > 0:
                return out
            if max_steps is not None and steps >= max_steps:
                raise RuntimeError("max_steps reached without halt")
            net_id = f[F_NEXT]
            if block is None:
                x = np.concatenate([[read], fwd])
            else:
                x = np.concatenate([[0.0], fwd, block])

    def _io(self, io, arg, addr, value):
        m = self.mem
        if io == IO_NONE:
            return
        self._log("io", io, arg)
        if io == IO_DISPLAY and self.display is not None:
            b, n = FRAMEBUFFER
            self.display(m[b:b + n].copy())
        elif io == IO_FILE_IN:
            b, _ = FILE_XFER
            with open(self.files[arg], "rb") as fh:
                data = fh.read()
            m[b] = len(data)
            m[b + 1:b + 1 + len(data)] = list(data)
        elif io == IO_FILE_OUT:
            b, _ = FILE_XFER
            n = int(m[b])
            with open(self.files[arg], "wb") as fh:
                fh.write(bytes(int(v) for v in m[b + 1:b + 1 + n]))
        elif io == IO_CLOCK:
            m[CLOCK[0]] = time.time()
        elif io == IO_ENTROPY:
            b, n = ENTROPY
            m[b:b + n] = list(random.SystemRandom().randbytes(n))
        elif io == IO_EVENTS:
            b, n = INPUT_EVENTS
            ev = self.events[:n - 1]
            del self.events[:len(ev)]
            m[b] = len(ev)
            m[b + 1:b + 1 + len(ev)] = ev
        elif io == IO_LOAD_NET:
            net = load_memory(m, addr)
            if arg < len(self.nets):
                self.nets[arg] = net
            else:
                self.nets.append(net)
