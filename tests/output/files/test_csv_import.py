"""Output tests for CSV import: csv_scan (448) then csv_imp (453) -> csv_pack / csv_commit loop.

Black box: the full manifest is booted (empty event queue, so BOOT initialises the zero page
and halts). Then hand-written CSV bytes are placed in the file transfer region, the scanner
is run into FILE_SCRATCH (0x3B0000, decision F2) and the importer is called with LR = HALT_OK.
Expected cell values are stated by hand from Excel's CSV open behaviour (each field is
treated as typed into its cell; empty fields leave the cell blank).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from blackbox import boot, value, peek  # noqa: E402

XFER = 0x201000
FILE_SCRATCH = 0x3B0000


def import_csv(data, row=0, col=0):
    h = boot([])
    h.mem[XFER] = len(data)
    h.mem[XFER + 1:XFER + 1 + len(data)] = list(data)
    x = np.zeros(65)
    x[9], x[11], x[27] = 3, 0x100, FILE_SCRATCH
    h.run(448, x, max_steps=100000)
    x = np.zeros(65)
    x[9], x[10], x[11] = 3, 0, 0x100        # LR = HALT_OK, LP, RSP
    x[22], x[23] = row, col                  # AR1, AC1 = top left target
    x[26] = FILE_SCRATCH                     # P0 = token stream
    for i in range(12):
        x[41 + i] = 500 + i                  # caller locals L0..L11, must come back
    trace = []
    h.trace = trace
    out = h.run(453, x, max_steps=2_000_000)
    return h, out, trace


def test_constants_text_numbers_booleans():
    h, out, _ = import_csv(b"a,1,TRUE\r\n2.5,,x y\r\n")
    assert value(h, "A1") == "a"
    assert value(h, "B1") == 1.0
    assert value(h, "C1") is True
    assert value(h, "A2") == 2.5
    assert value(h, "B2") == {"blank": True}
    assert value(h, "C2") == "x y"


def test_return_restores_locals_and_stack():
    h, out, trace = import_csv(b"7\n")
    assert value(h, "A1") == 7.0
    last = [t for t in trace if t.startswith("step") and " net 454 " in t][-1]
    words = eval(last.split(" out ")[1], {"np": np})
    assert words[0] == 3 and words[7] == 0
    assert words[10] == 0x100
    assert words[12] == 0
    assert list(words[40:52]) == [500 + i for i in range(12)]


def test_formula_recalculates_against_later_cells():
    # A1 refers to B1, which is imported after it
    h, _, _ = import_csv(b"=B1*2,21\n")
    assert value(h, "B1") == 21.0
    assert value(h, "A1") == 42.0


def test_quoted_fields_long_text_and_target_offset():
    # starts at C3; the second field is 7 characters (spans three packed words)
    h, _, _ = import_csv(b'"x,y","abcdefg"\nz\n', row=2, col=2)
    assert value(h, "C3") == "x,y"
    assert value(h, "D3") == "abcdefg"
    assert value(h, "C4") == "z"
    assert value(h, "A1") == {"blank": True}


def test_utf8_and_bom():
    # BOM, then e-acute (C3 A9), euro sign (E2 82 AC), and a 4-byte emoji (F0 9F 98 80)
    data = b"\xef\xbb\xbf" + b"caf\xc3\xa9,\xe2\x82\xac5,\xf0\x9f\x98\x80\n"
    h, _, _ = import_csv(data)
    assert value(h, "A1") == "café"
    assert value(h, "B1") == "€5"
    # supplementary characters are not decoded yet: U+FFFD (documented limit)
    assert value(h, "C1") == "�"


def test_rejected_formula_is_kept_as_text():
    h, _, _ = import_csv(b"=1+,ok\n")
    assert value(h, "A1") == "=1+"
    assert value(h, "B1") == "ok"
