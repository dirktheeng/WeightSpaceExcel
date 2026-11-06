"""Network id table for kernel output tests (encodings/control.md section 5, weights/MANIFEST.txt).

Paths only: the weight files are passed to the harness and never opened here.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402,F401

K = os.path.join(ROOT, "weights", "kernel")
NAMES = {
    0: "boot", 1: "trap", 2: "ret", 3: "halt_ok",
    4: "main_poll", 5: "main_count", 6: "main_first", 7: "ev_decode", 8: "ev_next",
    9: "c_len", 10: "c_rc", 11: "c_top", 12: "c_parse", 13: "c_set", 14: "c_done_rd", 15: "c_done",
    16: "cs_hash", 17: "cs_probe", 18: "cs_ltag", 19: "cs_lpay", 20: "cs_cntr", 21: "cs_cntw",
    22: "cs_wtag", 23: "cs_wpay", 24: "cs_wform", 25: "cs_genr", 26: "cs_wcalc",
    27: "parse_stub", 28: "rej_rd", 29: "rej_wr",
    # c_parse now routes to the real parser at id 78; kernel tests stay isolated
    # from the parser by placing parse_stub there.
    78: "parse_stub",
}


def paths(n=118, override=None):
    """Kernel ids 0..n-1; unused ids are TRAP. override: {id: path} for other agents' networks.

    Ids 80..117 (the evaluator and recalculation hooks the kernel now calls after
    CELL_SET and Delete) are taken from weights/MANIFEST.txt, paths only."""
    sys.path.insert(0, os.path.dirname(HERE))
    import blackbox as bb
    man = bb.manifest_paths()
    n = max(n, len(man))
    out = []
    for i in range(n):
        # The kernel's own ids (0..29) and the parse stub at 78 come from NAMES so
        # these tests stay isolated from the parser; every other network the kernel
        # now reaches (evaluator, UI redraw, FT_INIT and the function core) comes
        # from the manifest.
        if i not in NAMES and i < len(man):
            out.append(man[i])
            continue
        f = os.path.join(K, NAMES.get(i, "trap") + ".wt")
        out.append(f if os.path.exists(f) else os.path.join(K, "trap.wt"))
    for i, p in (override or {}).items():
        while len(out) <= i:
            out.append(os.path.join(K, "trap.wt"))
        out[i] = p
    return out


def state(**words):
    """Input vector (65) for starting a network directly: words given by register index."""
    x = np.zeros(65)
    for i, v in words.items():
        x[int(i[1:]) + 1] = v
    return x


# register indices (encodings/control.md section 2)
PC, LR, LP, RSP, MODE, STATUS = 7, 8, 9, 10, 11, 12
ATAG, APAY, AS, AR1, AC1, P0, P1, T0, T1 = 13, 14, 19, 20, 21, 25, 26, 29, 30
CELL_BASE = 0x010000


def regs(**kv):
    x = np.zeros(65)
    for name, v in kv.items():
        x[globals()[name] + 1] = v
    return x


def slot_of(mem, sheet, row, col):
    s = (40503 * row + 65599 * col + 1000003 * sheet) % 65536
    want = sheet * 2**34 + row * 2**14 + col + 1
    for _ in range(65536):
        k = mem[CELL_BASE + 8 * s]
        if k == want:
            return s
        if k == 0:
            return None
        s = (s + 1) % 65536
    return None
