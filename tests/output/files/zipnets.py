"""Shared loader for the CRC, inflate, deflate and ZIP output tests (black box, weights/files).
Loads the files networks by path at their ids; every other id is HALT_OK, so a return to LR = 3 halts.
Never opens weight files (paths only). Counts steps from the harness trace ("step" lines)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402

W = os.path.join(ROOT, "weights", "files")
HALT = os.path.join(ROOT, "weights", "kernel", "halt_ok.wt")
NETS = {
    461: "crc", 462: "x32", 463: "crcg", 464: "brd", 465: "bz", 466: "ifx", 467: "ifb", 468: "itab",
    469: "ihd2", 470: "ibe", 471: "ist1", 472: "stw", 473: "ifl", 474: "iset", 475: "ibc", 476: "ibo",
    477: "ibs", 478: "hb", 479: "hdec", 480: "ilit", 481: "xb", 482: "xe", 483: "icp", 484: "iy1",
    485: "iy3", 486: "iy5", 487: "iy6", 488: "iy7", 489: "zr0", 490: "zr1", 491: "zr3", 492: "zr4",
    493: "zr6", 495: "zr8", 497: "zcp", 498: "dzb", 499: "dfa", 500: "df2",
    501: "df3", 502: "df4", 503: "df5", 504: "df6", 505: "dpk", 506: "dpw", 494: "zwl", 496: "zwm",
    507: "zwa", 508: "zwb", 509: "zwc", 510: "zwd", 511: "zwe",
}
FS = 0x3B0000


def harness(trace=False):
    paths = [HALT] * 512
    for i, n in NETS.items():
        p = os.path.join(W, n + ".wt")
        if os.path.exists(p):
            paths[i] = p
    return Harness(paths, trace=[] if trace else None)


def state(**regs):
    """65-word input with words given by name: word i is input index i + 1."""
    x = np.zeros(65)
    names = {"PC": 7, "LR": 8, "LP": 9, "RSP": 10, "STATUS": 12, "ATAG": 13, "A": 14, "B": 16,
             "P0": 25, "P1": 26, "N0": 27, "N1": 28, "T0": 29, "T1": 30, "T2": 31, "T3": 32, "T4": 33, "T5": 34}
    x[9] = 3  # LR = HALT_OK
    for k, v in regs.items():
        x[names[k] + 1] = v
    return x


def run(h, net, x, max_steps=2_000_000):
    out = h.run(net, x, max_steps=max_steps)
    # minus the final HALT_OK step, so the count is the steps of the networks under test
    steps = sum(1 for t in h.trace if t.startswith("step")) - 1 if h.trace is not None else None
    return out, steps


def inflate(data, src=FS, dst=FS + 0x4000, bits=FS + 0x8000, trace=False):
    h = harness(trace)
    h.mem[src:src + len(data)] = list(data)
    out, steps = run(h, 466, state(P0=src, N0=len(data), P1=dst, N1=bits, LP=0))
    n = int(out[14])
    return bytes(int(v) for v in h.mem[dst:dst + max(n, 0)]), int(out[12]), steps


def deflate(data, mode=1, src=FS, dst=FS + 0x4000, bits=FS + 0x8000, trace=False):
    h = harness(trace)
    h.mem[src:src + len(data)] = list(data)
    out, steps = run(h, 499, state(P0=src, N0=len(data), P1=dst, N1=bits, B=mode, LP=0))
    n = int(out[14])
    return bytes(int(v) for v in h.mem[dst:dst + max(n, 0)]), int(out[12]), steps


TABLE = FS + 0x1000  # entry records for the ZIP writer tests
FX = 0x201001        # file transfer region, byte 0


def put(h, addr, data):
    h.mem[addr:addr + len(data)] = list(data)


def zip_write(h, parts, out=FX, bits=FS + 0x8000):
    """parts: list of (name bytes, data bytes). Names and data are placed in FILE_SCRATCH."""
    a = FS + 0x2000
    for k, (name, data) in enumerate(parts):
        put(h, a, name)
        put(h, a + len(name), data)
        h.mem[TABLE + 8 * k:TABLE + 8 * k + 8] = [a, len(name), a + len(name), len(data), 0, 0, 0, 0]
        a += len(name) + len(data)
    o, steps = run(h, 507, state(P0=TABLE, N0=len(parts), P1=out, N1=bits, RSP=0x100))
    n = int(o[14])
    return bytes(int(v) for v in h.mem[out:out + n]), o, steps


def zip_read(h, z, name, out=FS + 0xC000, bits=FS + 0x8000, src=FX):
    put(h, src, z)
    put(h, FS, name)
    o, steps = run(h, 489, state(P0=src, N0=len(z), P1=FS, N1=len(name), A=out, B=bits, RSP=0x100))
    n = int(o[14]) if o[12] == 0 else 0
    return bytes(int(v) for v in h.mem[out:out + n]), int(o[12]), steps
