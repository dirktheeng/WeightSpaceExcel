"""Black-box helpers for format engine output tests (docs/RULES.md rule 2).

Runs format networks through the frozen harness from register states and reads memory
by the documented layouts (weights/format/README.md). Never opens weight files.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402

HALT_OK = 3
REG = dict(PC=7, LR=8, LP=9, RSP=10, MODE=11, STATUS=12, ATAG=13, APAY=14, BTAG=15, BPAY=16,
           CTAG=17, CPAY=18, AS=19, AR1=20, AC1=21, AR2=22, AC2=23, AS2=24, P0=25, P1=26,
           N0=27, N1=28, **{f"T{i}": 29 + i for i in range(11)}, **{f"L{i}": 40 + i for i in range(24)})

_H = None


def harness():
    global _H
    if _H is None:
        _H = bb.Harness(bb.manifest_paths())
    _H.mem[:] = 0
    return _H


def regs(**kv):
    x = np.zeros(65)
    for k, v in kv.items():
        x[REG[k] + 1] = v
    return x


def reg(out, name):
    return out[REG[name]]


def put_str(h, addr, s):
    """Heap string record (encodings/memory-map.md section 9) at addr."""
    u = s.encode("utf-16-le")
    cs = [u[i] + 256 * u[i + 1] for i in range(0, len(u), 2)]
    h.mem[addr] = len(cs)
    cs = cs + [0, 0]
    for i in range(0, len(cs) - 2, 3):
        h.mem[addr + 2 + i // 3] = cs[i] + cs[i + 1] * 65536 + cs[i + 2] * 2**32
    return addr


def get_str(h, addr):
    n = int(h.mem[addr])
    out = []
    for i in range(n):
        w = int(h.mem[addr + 2 + i // 3])
        out.append(chr((w >> (16 * (i % 3))) & 0xFFFF))
    return "".join(out)
