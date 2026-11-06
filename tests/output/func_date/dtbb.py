"""Black-box driver for the date and time networks (weights/func/date, ids 344 to 359).

Loads the networks by path at their ids (weights/MANIFEST.txt ids), puts the kernel TRAP at every
other id and HALT_OK (id 3) at 3, sets LR = 3 so the subroutine returns into a clean halt, and
reads registers from the final state. Weight files are never opened here (docs/RULES.md rule 2).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402

K = os.path.join(ROOT, "weights", "kernel")
D = os.path.join(ROOT, "weights", "func", "date")
NETS = {344: "dt_ymd", 345: "dt_date", 346: "dt_time", 347: "dt_days", 348: "dt_now",
        349: "dt_now", 350: "dt_wk", 351: "dt_edate", 352: "dt_dif", 353: "dt_yf",
        354: "dt_wk", 347: "dt_pair", 348: "dt_fin2"}

# output word -> input index is word + 1
W = dict(PC=7, LR=8, LP=9, STATUS=12, A_TAG=13, A_PAY=14, B_TAG=15, B_PAY=16, C_TAG=17, C_PAY=18,
         N0=27, N1=28, T0=29, T1=30, T2=31, T3=32, T4=33, T5=34, T6=35, T7=36, T8=37, T9=38, T10=39)
NUM, TEXT, BOOL, ERR, MISSING, BLANK = 1, 2, 3, 4, 8, 0
VALUE, NUMERR, DIV0 = 3, 6, 2


def paths():
    p = [os.path.join(K, "trap.wt")] * 360
    p[3] = os.path.join(K, "halt_ok.wt")
    for i, n in NETS.items():
        f = os.path.join(D, n + ".wt")
        if os.path.exists(f):
            p[i] = f
    return p


_H = None


def harness():
    global _H
    if _H is None:
        _H = Harness(paths())
    _H.mem[:] = 0
    return _H


def call(net, a=None, b=None, c=None, sel=0, regs=None, mem=None, max_steps=20000):
    """a, b, c: (tag, pay) or a number (tag 1). Returns (final state words, harness)."""
    h = harness()
    for addr, v in (mem or {}).items():
        h.mem[addr] = v
    x = np.zeros(65)
    for i in range(1, 65):
        x[i] = 0.0
    x[W["LR"] + 1] = 3
    x[W["LP"] + 1] = 0
    x[W["T0"] + 1] = sel
    for name, v in (("A", a), ("B", b), ("C", c)):
        if v is None:
            v = (MISSING, 0)
        if not isinstance(v, tuple):
            v = (NUM, float(v))
        x[W[name + "_TAG"] + 1], x[W[name + "_PAY"] + 1] = v
    for k, v in (regs or {}).items():
        x[W[k] + 1] = v
    out = h.run(net, x, max_steps=max_steps)
    return out, h


def result(net, *args, **kw):
    out, _ = call(net, *args, **kw)
    assert out[W["STATUS"]] == 0
    return (int(out[W["A_TAG"]]), float(out[W["A_PAY"]]))
