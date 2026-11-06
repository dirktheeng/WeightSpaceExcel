"""Black-box helpers for the lookup and reference function tests (weights/func/lookup, ids 360..383).

Cells are written through the kernel's CELL_SET network (id 16) run by the harness, strings are
placed in the text heap by the documented layout (encodings/memory-map.md section 9) as test input,
and the networks under test are started with registers set by encodings/control.md and
weights/func/lookup/core.md. Weight files are never opened; expected values are stated by hand
in the test modules from Excel's documented behaviour.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from blackbox import manifest_paths, text_at, ROOT  # noqa: E402
from harness.harness import Harness  # noqa: E402

HALT_OK = 3
FN_RET = 257
TEXT_EMPTY = 0x302000
STR_BASE = 0x340000          # where tests place strings (inside TEXT_HEAP, far above HEAP_TOP)
HT0 = 0x360000               # heap top handed to functions that build strings
RSP0 = 0x100

_paths = None


def paths():
    global _paths
    if _paths is None:
        p = list(manifest_paths())
        # FN_RET (257) may not exist yet; a function's return is observed by halting there.
        p[FN_RET] = os.path.join(ROOT, "weights", "kernel", "halt_ok.wt")
        _paths = p
    return _paths


class Sheet:
    """A harness with cells set through CELL_SET. Values: float/int number, str text,
    bool boolean, ('err', code) error, None for nothing."""

    def __init__(self):
        self.h = Harness(paths())
        self.h.trace = None
        self.next_str = STR_BASE

    def string(self, s):
        if s == "":
            return TEXT_EMPTY
        b = s.encode("utf-16-le")
        u = [b[i] + 256 * b[i + 1] for i in range(0, len(b), 2)]
        a = self.next_str
        m = self.h.mem
        m[a] = len(u)
        m[a + 1] = 1
        for j in range(0, len(u), 3):
            c = (u[j:j + 3] + [0, 0])[:3]
            m[a + 2 + j // 3] = c[0] + c[1] * 2**16 + c[2] * 2**32
        self.next_str = a + 2 + (len(u) + 2) // 3 + 1
        return a

    def val(self, v):
        if isinstance(v, bool):
            return 3.0, float(v)
        if isinstance(v, (int, float)):
            return 1.0, float(v)
        if isinstance(v, str):
            return 2.0, float(self.string(v))
        if isinstance(v, tuple) and v[0] == "err":
            return 4.0, float(v[1])
        if v is None:
            return 0.0, 0.0
        raise ValueError(v)

    def set(self, row, col, v, sheet=0):
        t, p = self.val(v)
        x = np.zeros(65)
        x[8 + 1], x[9 + 1], x[10 + 1] = HALT_OK, 0, RSP0
        x[13 + 1], x[14 + 1] = t, p
        x[19 + 1], x[20 + 1], x[21 + 1] = sheet, row, col
        x[30 + 1] = 1
        self.h.run(16, x, max_steps=200)

    def column(self, col, values, row0=0, sheet=0):
        for i, v in enumerate(values):
            if v is not None:
                self.set(row0 + i, col, v, sheet)

    def row(self, row, values, col0=0, sheet=0):
        for i, v in enumerate(values):
            if v is not None:
                self.set(row, col0 + i, v, sheet)

    def decode(self, t, p):
        t = int(t)
        if t == 0:
            return None
        if t == 1:
            return p
        if t == 2:
            return text_at(self.h, int(p))
        if t == 3:
            return bool(p)
        if t == 4:
            return ("err", int(p))
        return ("tag", t, p)


# ---- search core (lk_start, 360)
M_FWD, M_FWD_SMALLER, M_FWD_LARGER = 1, 2, 3
M_REV, M_REV_SMALLER, M_REV_LARGER = 4, 5, 6
M_ASC_LAST_LE, M_DESC_LAST_GE, M_ASC_FIRST_GE, M_DESC_FIRST_LE = 7, 8, 9, 10
M_ASC_EXACT, M_DESC_EXACT = 11, 12


def search(sh, v, r0, c0, n, mode, horizontal=False, wild=False, sheet=0, max_steps=200000):
    """Runs the core with LR = HALT_OK. Returns (found, index, out, steps)."""
    t, p = sh.val(v)
    x = np.zeros(65)
    x[8 + 1], x[9 + 1], x[10 + 1] = HALT_OK, 0, RSP0
    x[15 + 1], x[16 + 1] = t, p
    x[19 + 1], x[20 + 1], x[21 + 1] = sheet, r0, c0
    x[28 + 1] = n
    x[31 + 1] = 1 if horizontal else 0
    x[32 + 1] = mode
    x[36 + 1] = 1 if wild else 0
    # words the core must restore (caller locals and evaluator registers)
    for w in (22, 23, 24, 26, 27):
        x[w + 1] = 1000 + w
    for w in range(40, 48):
        x[w + 1] = 2000 + w
    sh.h.trace = []
    out = sh.h.run(360, x, max_steps=max_steps)
    steps = sum(1 for s in sh.h.trace if s.startswith("step"))
    sh.h.trace = None
    for w in (22, 23, 24, 26, 27):
        assert out[w] == 1000 + w, ("not restored", w)
    for w in range(40, 48):
        assert out[w] == 2000 + w, ("not restored", w)
    assert out[10] == RSP0
    found = out[12] == 0
    return found, int(out[32]) if found else None, out, steps


# ---- function ABI calls (encodings/functions.md section 2)
FID = {"ADDRESS": 9, "AREAS": 14, "CHOOSE": 65, "COLUMN": 70, "COLUMNS": 71, "HLOOKUP": 212,
       "INDEX": 248, "INDIRECT": 249, "LOOKUP": 291, "MATCH": 295, "OFFSET": 347, "ROW": 403,
       "ROWS": 404, "TRANSPOSE": 476, "VLOOKUP": 499, "XLOOKUP": 511, "XMATCH": 512}
ENTRY = 375
SP_BASE = 0x1040            # operand stack pointer used by the tests (inside OPER_STACK)
SCR0 = 0x0B0400             # EVAL_SCRATCH bump pointer handed to the function
REC0 = 0x0B0100             # where tests place reference records (tag 5) and union nodes (tag 10)
TP0 = 0x090100
HOME = (20, 10)             # HR, HC of the "evaluating cell" (K21)


def a1(addr):
    """'B3' -> (row, col) 0-based; '$' ignored."""
    addr = addr.replace("$", "")
    i = 0
    while addr[i].isalpha():
        i += 1
    col = 0
    for ch in addr[:i].upper():
        col = col * 26 + ord(ch) - 64
    return int(addr[i:]) - 1, col - 1


def ref(addr, sheet=0):
    return ("ref", addr, sheet)


def rng(addr, sheet=0):
    return ("rng", addr, sheet)


MISSING = ("missing",)


class Call:
    def __init__(self, sh):
        self.sh = sh
        self.rec = REC0

    def arg(self, v):
        m = self.sh.h.mem
        if isinstance(v, tuple) and v and v[0] == "ref":
            r, c = a1(v[1])
            return 9.0, float(v[2] * 2**34 + r * 2**14 + c)
        if isinstance(v, tuple) and v and v[0] == "rng":
            p, q = v[1].split(":")
            r1, c1 = a1(p)
            r2, c2 = a1(q)
            a = self.rec
            for k, w in enumerate((v[2], min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2), v[2])):
                m[a + k] = w
            self.rec += 8
            return 5.0, float(a)
        if isinstance(v, tuple) and v and v[0] == "union":
            lt, lp = self.arg(v[1])
            rt, rp = self.arg(v[2])
            a = self.rec
            m[a:a + 4] = [lt, lp, rt, rp]
            self.rec += 8
            return 10.0, float(a)
        if v == MISSING:
            return 8.0, 0.0
        return self.sh.val(v)


def union(x, y):
    return ("union", x, y)


def call(sh, name, *args, max_steps=300000):
    """Calls function `name` through its FUNC_TABLE entry network with the ABI entry state.
    FN_RET (257) is HALT_OK here, so the run stops at the function's return; returns
    (value, out, steps) with value decoded from A."""
    c = Call(sh)
    vals = [c.arg(a) for a in args]
    n = len(vals)
    m = sh.h.mem
    sp = SP_BASE
    for i, (t, p) in enumerate(vals[:-1]):
        m[sp - 2 * (n - 1 - i)] = t
        m[sp - 2 * (n - 1 - i) + 1] = p
    x = np.zeros(65)
    x[10 + 1] = RSP0
    x[11 + 1] = 3
    if n:
        x[15 + 1], x[16 + 1] = vals[-1]
    else:
        x[15 + 1], x[16 + 1] = 1.0, 12345.0      # previous top of stack, must be left alone
    x[27 + 1] = n
    x[31 + 1] = 64 + FID[name]
    x[52 + 1] = TP0
    x[53 + 1] = sp
    x[56 + 1] = SCR0
    x[23 + 1] = HT0
    x[54 + 1], x[55 + 1] = HOME
    pres = {22: 7.0, 24: 0.0, 26: 0x090200, 40: 4040, 41: 4041, 47: 4047, 51: 4051, 57: 4057, 63: 4063}
    for w, v in pres.items():
        x[w + 1] = v
    sh.h.trace = []
    out = sh.h.run(ENTRY, x, max_steps=max_steps)
    st = [s for s in sh.h.trace if s.startswith("step")]
    steps = len(st)
    sh.h.trace = None
    assert st[-1].split()[3] == str(FN_RET), ("did not return through FN_RET", st[-1][:40])
    for w, v in pres.items():
        assert out[w] == v, ("preserve set", w)
    assert out[10] == RSP0 and out[27] == n and out[53] == sp and out[52] == TP0
    return sh.decode_ref(out[13], out[14]), out, steps


def _decode_ref(self, t, p):
    t = int(t)
    if t == 9:
        k = int(p)
        return ("ref", k >> 34, (k >> 14) % 2**20, k % 2**14)
    if t == 5:
        m = self.h.mem
        a = int(p)
        return ("rng",) + tuple(int(m[a + i]) for i in range(6))
    if t == 10:
        return ("union", int(p))
    if t == 8:
        return ("missing",)
    return self.decode(t, p)


Sheet.decode_ref = _decode_ref
