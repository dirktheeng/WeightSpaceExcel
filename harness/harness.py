"""Frozen generic harness (docs/HARNESS.md). No application logic lives here.

It loads networks, runs forward passes, and obeys the fixed output fields.
Weight file format: harness/FORMAT.md.
"""
import itertools
import random
import time

import numpy as np

# ---- Step protocol: fixed output fields (indices into every network output) ----
F_NEXT, F_MEMOP, F_ADDR, F_VALUE, F_IO, F_IOARG, F_HALT = range(7)
N_FIELDS = 7
MEM_NONE, MEM_READ, MEM_WRITE = 0, 1, 2
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


class Network:
    """A list of layers. Layer k reads the output of an earlier layer (0 = network input)."""

    def __init__(self, n_in, layers):
        self.n_in, self.layers = n_in, layers

    def forward(self, x):
        vals = [np.asarray(x, dtype=float)]
        if vals[0].shape != (self.n_in,):
            raise ValueError(f"input length {vals[0].shape} != {self.n_in}")
        for kind, a in self.layers:
            if kind == "dense":
                v = a["W"] @ vals[a["src"]] + a["b"]
            elif kind in ACTS:
                v = ACTS[kind](vals[a["src"]])
            elif kind == "mul":
                s = vals[a["src"]]
                v = s[a["a"]:a["b"]] * s[a["c"]:a["d"]]
            elif kind == "slice":
                v = vals[a["src"]][a["a"]:a["b"]]
            elif kind == "concat":
                v = np.concatenate([vals[a["src"]], vals[a["src2"]]])
            else:
                raise ValueError(f"unknown layer type {kind}")
            vals.append(v)
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


def load_file(path):
    with open(path) as f:
        toks = [t for line in f for t in line.split("#")[0].split()]
    return _build(toks)


def load_memory(mem, addr):
    """Memory form: n_in, then per layer: type code, src, params..., then code 0 (end)."""
    return _build(itertools.chain(["input"], iter(mem[addr:])))


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
        while True:
            out = self.nets[net_id].forward(x)
            f = [int(round(v)) for v in out[:N_FIELDS]]
            self._log("step", steps, "net", net_id, "out", list(out))
            read = 0.0
            if f[F_MEMOP] == MEM_READ:
                read = self.mem[f[F_ADDR]]
                self._log("read", f[F_ADDR], read)
            elif f[F_MEMOP] == MEM_WRITE:
                self.mem[f[F_ADDR]] = out[F_VALUE]
                self._log("write", f[F_ADDR], out[F_VALUE])
            self._io(f[F_IO], f[F_IOARG], f[F_ADDR], f[F_VALUE])
            steps += 1
            if f[F_HALT] > 0:
                return out
            if max_steps is not None and steps >= max_steps:
                raise RuntimeError("max_steps reached without halt")
            net_id = f[F_NEXT]
            x = np.concatenate([[read], out])

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
