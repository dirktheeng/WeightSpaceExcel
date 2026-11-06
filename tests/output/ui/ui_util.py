"""Black-box helpers for UI output tests (docs/RULES.md rule 2).

Runs UI networks through the frozen harness, reads framebuffer words, and dumps the
framebuffer to PNG for visual review (observation only). Never opens weight files.
"""
import os
import pathlib
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402

OUT = os.path.join(HERE, "out")
FB, W, H = 0x100000, 1280, 800
HALT_OK = 3

# register indices (encodings/control.md section 2)
REG = dict(PC=7, LR=8, LP=9, RSP=10, MODE=11, STATUS=12, ATAG=13, APAY=14, BTAG=15, BPAY=16,
           CTAG=17, CPAY=18, AS=19, AR1=20, AC1=21, AR2=22, AC2=23, AS2=24, P0=25, P1=26,
           N0=27, N1=28, **{f"T{i}": 29 + i for i in range(11)}, **{f"L{i}": 40 + i for i in range(24)})


def regs(**kv):
    x = np.zeros(65)
    for k, v in kv.items():
        x[REG[k] + 1] = v
    return x


def harness(events=()):
    return bb.Harness(bb.manifest_paths(), events=list(events))


def run_counted(h, net, x, max_steps=5_000_000):
    """Run and return (output, steps). Steps counted from the trace of step lines only."""
    n = [0]

    class Counter(list):
        def append(self, s):
            if s.startswith("step"):
                n[0] += 1
    h.trace = Counter()
    out = h.run(net, x, max_steps=max_steps)
    h.trace = None
    return out, n[0]


def pixel(h, x, y):
    return int(h.mem[FB + W * y + x])


def rgb(word):
    return (word >> 16) & 255, (word >> 8) & 255, word & 255


def dump_png(h, name):
    os.makedirs(OUT, exist_ok=True)
    px = h.mem[FB:FB + W * H].astype(np.int64).reshape(H, W)
    rgbarr = np.stack([(px >> 16) & 255, (px >> 8) & 255, px & 255], axis=-1).astype(np.uint8)
    raw = b"".join(b"\0" + rgbarr[y].tobytes() for y in range(H))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    path = pathlib.Path(OUT) / name   # write only (observation output); nothing is read
    path.write_bytes(data)
    return str(path)
