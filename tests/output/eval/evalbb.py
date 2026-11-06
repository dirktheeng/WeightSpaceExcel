"""Black-box helpers for evaluator and recalculation output tests (weights/eval).

Token records and strings are test data written into memory; cells are committed through the
kernel's CELL_SET (id 16) with LR = 80 (hk_commit), exactly as the commit chain will call the hook.
Never opens weight files; expected values are stated by hand in the tests.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402
from blackbox import Harness  # noqa: E402

REC_BASE = 0x098000      # test formula records (inside FORMULA_STORE)
STR_BASE = 0x370000      # test strings (inside TEXT_HEAP, far above HEAP_TOP)
OPS = {"u-": 16, "u+": 17, "%": 18, "^": 19, "*": 20, "/": 21, "+": 22, "-": 23, "&": 24,
       "=": 25, "<>": 26, "<": 27, "<=": 28, ">": 29, ">=": 30,
       "union": 32, "isect": 33}
ERR = {"#NULL!": 1, "#DIV/0!": 2, "#VALUE!": 3, "#REF!": 4, "#NAME?": 5, "#NUM!": 6, "#N/A": 7}


def rc(a):
    return bb.parse_a1(a)


class Sheet:
    def __init__(self):
        self.h = Harness(bb.manifest_paths())
        self.h.trace = None
        self.h.run(0, np.zeros(65), max_steps=200000)   # BOOT (function table init and first frame), then halt on the empty queue
        self.rec = REC_BASE
        self.str = STR_BASE
        self.steps = 0

    def string(self, s):
        m, h = self.h.mem, self.str
        u = list(s.encode("utf-16-le"))
        units = [u[i] + 256 * u[i + 1] for i in range(0, len(u), 2)]
        m[h], m[h + 1] = len(units), 1
        for i in range(0, len(units), 3):
            w = units[i:i + 3] + [0, 0]
            m[h + 2 + i // 3] = w[0] + w[1] * 2**16 + w[2] * 2**32
        self.str += 2 + (len(units) + 2) // 3 + 1
        return h

    def tokens(self, home, toks):
        """toks: list of numbers, strings ("'text"), booleans, ("err", name), ("ref", "A1" or "$A$1"),
        ("fn", fid, argc) or operator names. Returns the formula record address."""
        hr, hc = rc(home)
        m = self.h.mem
        rec, ts = self.rec, self.rec + 8
        out = []
        for t in toks:
            if isinstance(t, bool):
                out.append((3, float(t)))
            elif isinstance(t, (int, float)):
                out.append((1, float(t)))
            elif isinstance(t, tuple) and t[0] == "err":
                out.append((4, ERR[t[1]]))
            elif isinstance(t, tuple) and t[0] == "sheet":
                out.append((8, t[1]))
            elif isinstance(t, tuple) and t[0] in ("ref", "rng"):
                for k, a in enumerate(t[1:]):
                    opc = 5 if t[0] == "ref" else 6 + k
                    ra, ca = "$" in a.lstrip("$")[1:] or a.count("$") == 2, a.startswith("$")
                    r, c = rc(a.replace("$", ""))
                    rf = r if ra else r - hr + 2**20
                    cf = c if ca else c - hc + 2**14
                    out.append((opc, (int(ra) + 2 * int(ca)) * 2**36 + rf * 2**15 + cf))
            elif isinstance(t, tuple) and t[0] == "fn":
                out.append((64 + t[1], t[2]))
            elif isinstance(t, str) and t.startswith("'"):
                out.append((2, self.string(t[1:])))
            else:
                out.append((OPS[t], 0))
        out.append((0, 0))
        for i, (o, v) in enumerate(out):
            m[ts + 2 * i], m[ts + 2 * i + 1] = o, v
        m[rec + 1], m[rec + 2] = ts, len(out) - 1
        self.rec = ts + 2 * len(out) + 8
        return rec

    def set(self, addr, value=None, formula=None, max_steps=200000, sheet=0):
        """Commit a constant (value: number, bool, str, None blank) or a token list (formula)."""
        r, c = rc(addr)
        tag, pay, p1 = 0, 0.0, 0
        if formula is not None:
            p1 = self.tokens(addr, formula)
        elif isinstance(value, bool):
            tag, pay = 3, float(value)
        elif isinstance(value, (int, float)):
            tag, pay = 1, float(value)
        elif isinstance(value, str):
            tag, pay = 2, self.string(value)
        elif isinstance(value, tuple):
            tag, pay = 4, ERR[value[1]]
        x = np.zeros(65)
        for w, v in ((30, 1), (19, sheet), (20, r), (21, c), (13, tag), (14, pay), (26, p1), (8, 80),
                     (10, 0x100), (11, 1)):
            x[w + 1] = v
        tr = []
        self.h.trace = tr
        self.h.run(16, x, max_steps=max_steps)
        self.h.trace = None
        self.steps = sum(t.startswith("step") for t in tr)
        return self.steps

    def value(self, addr):
        return bb.value(self.h, addr)

    def circ(self):
        return bb.peek(self.h, bb.CIRC_FLAG)

    def fault(self):
        return bb.peek(self.h, bb.FAULT)
