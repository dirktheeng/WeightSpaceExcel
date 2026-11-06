"""Black-box helpers for the VBA networks (weights/vba, encodings/vba.md).

Writes VBA source or hand-assembled bytecode into VBA_STATE, runs the documented entry
network through the harness, and decodes raw memory by the documented layout. Never opens
weight files: manifest paths go to the harness only.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402
from harness.harness import Harness  # noqa: E402

VGLOB, SRC, TOK, BC, PROCT = 0x380000, 0x380100, 0x388000, 0x390000, 0x398000
VSTR0, DOUT, MOUT, VSTACK = 0x399001, 0x39C000, 0x39E000, 0x3A0000
LEX_ENTRY, RUN_ENTRY = 399, 420


def lex(src, max_steps=200000):
    h = Harness(bb.manifest_paths())
    m = h.mem
    m[SRC] = len(src)
    for i, c in enumerate(src):
        m[SRC + 1 + i] = ord(c)
    h.run(LEX_ENTRY, np.zeros(65), max_steps=max_steps)
    n = int(m[VGLOB + 5])
    toks = [(int(m[TOK + 2 * j]), float(m[TOK + 2 * j + 1])) for j in range(n)]
    return h, toks


def vstr(h, handle):
    n = int(h.mem[handle])
    return "".join(chr(int(c)) for c in h.mem[handle + 1:handle + 1 + n])


def run(prog, procs, strings=(), max_steps=50000):
    """prog: list of (OP, ARG); procs: PROCT records; strings placed as VSTR records first."""
    h = Harness(bb.manifest_paths())
    m = h.mem
    for i, (o, a) in enumerate(prog):
        m[BC + 2 * i], m[BC + 2 * i + 1] = o, a
    for i, r in enumerate(procs):
        m[PROCT + 4 * i:PROCT + 4 * i + 4] = r
    vht, handles = VSTR0, []
    for s in strings:
        handles.append(vht)
        m[vht] = len(s)
        for j, c in enumerate(s):
            m[vht + 1 + j] = ord(c)
        vht += 1 + len(s)
    x = np.zeros(65)
    x[1 + 43] = vht          # VHT
    x[1 + 23] = 0x302002     # XHT: TEXT_HEAP top for ev_totext
    h.run(RUN_ENTRY, x, max_steps=max_steps)
    d, k = int(m[VGLOB]), int(m[VGLOB + 1])
    dbg = "".join(chr(int(c)) for c in m[DOUT:DOUT + d])
    msg = "".join(chr(int(c)) for c in m[MOUT:MOUT + k])
    return h, dbg, msg, int(m[VGLOB + 2])


def run_src(src, max_steps=400000):
    """VBA source end to end: lexer (CHAIN = 1) -> parser -> interpreter. Procedure 0 runs."""
    h = Harness(bb.manifest_paths())
    m = h.mem
    m[SRC] = len(src)
    for i, c in enumerate(src):
        m[SRC + 1 + i] = ord(c)
    x = np.zeros(65)
    x[1 + 38] = 1            # CHAIN: lexer -> parser (400) -> interpreter (420)
    x[1 + 23] = 0x302002     # XHT: TEXT_HEAP top for ev_totext
    h.run(LEX_ENTRY, x, max_steps=max_steps)
    d, k = int(m[VGLOB]), int(m[VGLOB + 1])
    dbg = "".join(chr(int(c)) for c in m[DOUT:DOUT + d])
    msg = "".join(chr(int(c)) for c in m[MOUT:MOUT + k])
    return h, dbg, msg, int(m[VGLOB + 2])
