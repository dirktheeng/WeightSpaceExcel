"""SHEET / SHEETS (lg_sheet, 303). Expected values by hand: SHEET() is the formula's sheet number
(1, sheet 0 only for now), SHEET(ref) is the referenced sheet's number (index + 1), SHEETS() is
the number of sheets in the workbook (1 after boot), SHEETS(ref) is 1 for a one-sheet reference."""
import pytest

from lgbb import ERR, NUM, Abi

SHEET, SHEETS = 416, 417


@pytest.fixture(scope="module")
def abi():
    a = Abi()
    rec = 0xB0100            # a reference record in EVAL_SCRATCH: [SHEET, R1, C1, R2, C2, SHEET2, NEXT, 0]
    for i, w in enumerate([1, 0, 0, 4, 2, 1, 0, 0]):
        a.h.mem[rec + i] = w
    return a


@pytest.mark.parametrize("fid,args,want", [
    (SHEETS, [], (NUM, 1)),
    (SHEET, [], (NUM, 1)),
    (SHEET, [(9, 5 * 2**14 + 2)], (NUM, 1)),
    (SHEET, [(9, 2 * 2**34 + 1048575 * 2**14 + 16383)], (NUM, 3)),
    (SHEET, [(5, 0xB0100)], (NUM, 2)),
    (SHEETS, [(9, 7)], (NUM, 1)),
    (SHEETS, [(5, 0xB0100)], (NUM, 1)),
    (SHEET, [(ERR, 2)], (ERR, 2)),
])
def test_sheet(abi, fid, args, want):
    got, steps = abi.call(303, fid, args)
    assert got == want
    assert steps <= 3
