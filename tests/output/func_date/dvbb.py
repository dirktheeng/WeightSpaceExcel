"""Black-box driver for the date/time text parser chain (dv_ent 354 .. dv_rest 357).

Places a string in the text heap (encodings/memory-map.md section 9: length, refcount, packed words
c0 + c1 2^16 + c2 2^32), calls dv_ent as a leaf subroutine with A = (2, handle), T0 = mode and LR = HALT_OK,
and checks that every word except A and STATUS comes back unchanged. Paths only; no weight file is read.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "output"))
from harness.harness import Harness  # noqa: E402
import blackbox  # noqa: E402

DV, TV, CO = 0, 1, 2
HANDLE = 0x302100
_H = None


def harness():
    global _H
    if _H is None:
        p = blackbox.manifest_paths()
        trap = p[1]
        keep = {1, 2, 3} | set(range(344, 360))
        _H = Harness([q if i in keep else trap for i, q in enumerate(p)])
    _H.mem[:] = 0
    return _H


def put_string(h, addr, s):
    h.mem[addr] = len(s)
    h.mem[addr + 1] = 1
    for k in range(0, len(s), 3):
        w = 0
        for j, ch in enumerate(s[k:k + 3]):
            w += ord(ch) * 2 ** (16 * j)
        h.mem[addr + 2 + k // 3] = w


def run(arg, mode, steps=False):
    """arg: a str (text argument) or a (tag, pay) tuple. Returns ((tag, pay), steps)."""
    h = harness()
    x = np.zeros(65)
    for w in range(7, 64):
        x[w + 1] = 1000 + w
    x[8] = 0          # PC
    x[9], x[10] = 3, 0   # LR = HALT_OK
    x[11] = 0x200     # RSP
    if isinstance(arg, str):
        put_string(h, HANDLE, arg)
        x[14], x[15] = 2, HANDLE
    else:
        x[14], x[15] = arg
    x[30] = mode      # T0
    before = x.copy()
    trace = []
    h.trace = trace
    try:
        out = h.run(354, x, max_steps=5000)
    finally:
        h.trace = None
    for w in list(range(8, 12)) + list(range(15, 64)):
        if w in (8, 9):
            continue
        assert out[w] == before[w + 1], ("word", w, out[w], before[w + 1])
    assert out[12] == 0
    n = sum(1 for t in trace if t.startswith("step"))
    r = (int(out[13]), float(out[14]))
    return (r, n) if steps else r
