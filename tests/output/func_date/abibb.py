"""ABI-level driver: enters dt_abi (351) the way FN_CALL does (encodings/functions.md section 2)
and stops at FN_RET, which is replaced by HALT_OK (3) in this test's network list so the result
can be read. Cells for reference arguments are stored by running CELL_SET (kernel id 16) first.
Paths only; no weight file is opened here (docs/RULES.md rule 2)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "output"))
from harness.harness import Harness  # noqa: E402
import blackbox  # noqa: E402

FID = dict(DATE=112, DATEDIF=113, DAY=116, DAYS=117, DAYS360=118, EDATE=147, EOMONTH=150, HOUR=213,
           ISOWEEKNUM=270, MINUTE=307, MONTH=315, NOW=335, SECOND=413, TIME=467, TODAY=474,
           WEEKDAY=502, WEEKNUM=503, YEAR=515, YEARFRAC=516)
SP0 = 0x1000 + 40          # some operand stack depth
PRESERVE = [10, 11, 22, 23, 24, 26, 27] + list(range(40, 64))
_H = None


def harness():
    global _H
    if _H is None:
        p = blackbox.manifest_paths()
        p[257] = os.path.join(ROOT, "weights", "kernel", "halt_ok.wt")
        _H = Harness(p)
    _H.mem[:] = 0
    return _H


def key(sheet, row, col):
    return sheet * 2 ** 34 + row * 2 ** 14 + col


def set_cell(h, sheet, row, col, val):
    x = np.zeros(65)
    x[9], x[10] = 3, 0                 # LR = HALT_OK
    x[20], x[21], x[22] = sheet, row, col
    x[31] = 1                          # T1 = 1: set
    x[14], x[15] = val
    x[27] = 0                          # P1 = 0: constant
    h.run(16, x, max_steps=1000)


def call(name, *args, cells=(), mem=None):
    """args: (tag, pay) tuples or numbers. cells: ((sheet, row, col), (tag, pay)) stored first."""
    h = harness()
    for (s, r, c), v in cells:
        set_cell(h, s, r, c, v)
    for addr, v in (mem or {}).items():
        h.mem[addr] = v
    args = [a if isinstance(a, tuple) else (1, float(a)) for a in args]
    n = len(args)
    x = np.zeros(65)
    for w in range(7, 64):
        x[w + 1] = 1000 + w            # recognisable words, checked for the preserve set
    x[8] = 0                           # PC 0
    x[28] = n                          # N0
    x[32] = 64 + FID[name]             # T2
    sp = SP0 + 2 * max(n - 1, 0)
    x[54] = sp                         # SP
    for i, (t, p) in enumerate(args[:-1]):
        h.mem[sp - 2 * (n - 1) + 2 * i] = t
        h.mem[sp - 2 * (n - 1) + 2 * i + 1] = p
    if n:
        x[16], x[17] = args[-1]        # B = last argument
    else:
        x[16], x[17] = 1, 77.0         # previous top of stack, must survive
    before = x.copy()
    out = h.run(351, x, max_steps=200000)
    return out, before


def result(name, *args, **kw):
    out, before = call(name, *args, **kw)
    for w in PRESERVE:
        assert out[w] == before[w + 1], (name, "preserve set word", w)
    assert int(out[7]) == 0            # FN_RET entered at PC 0
    return (int(out[13]), float(out[14]))
