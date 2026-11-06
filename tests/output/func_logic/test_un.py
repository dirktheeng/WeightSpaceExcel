"""lg_un (id 299): ABI entry for one-argument Information functions. Arguments arrive as
values or as undereferenced cell references (tag 9, PAY = packed key). Expected values by hand."""
import pytest

from lgbb import BLANK, BOOL, ERR, NUM, TEXT, Abi

FID = {"ISBLANK": 256, "ISERR": 257, "ISERROR": 258, "ISEVEN": 259, "ISFORMULA": 260, "ISLOGICAL": 261,
       "ISNA": 262, "ISNONTEXT": 263, "ISNUMBER": 264, "ISODD": 265, "ISREF": 267, "ISTEXT": 268,
       "N": 319, "NA": 320, "TYPE": 485, "ERROR.TYPE": 155, "NOT": 334, "TRUE": 481, "FALSE": 165}
T, F = (BOOL, 1), (BOOL, 0)


@pytest.fixture(scope="module")
def abi():
    a = Abi()
    a.set_cell("A1", NUM, 42)
    a.set_cell("B2", TEXT, 0x300100)
    a.set_cell("C3", BOOL, 1)
    a.set_cell("D4", ERR, 7)
    a.set_cell("E5", NUM, 7, formula=0x98000)   # a formula cell (formula record address nonzero)
    a.set_cell("F6", NUM, 0)
    return a


def ref(abi, a1):
    return (9, abi.key(a1))


VALS = [  # direct values
    ("ISNUMBER", (NUM, 1.5), T), ("ISTEXT", (TEXT, 0x300100), T), ("ISLOGICAL", (BOOL, 0), T),
    ("ISERROR", (ERR, 2), T), ("ISERR", (ERR, 7), F), ("ISNA", (ERR, 7), T), ("ISNONTEXT", (NUM, 1), T),
    ("ISREF", (NUM, 1), F), ("N", (BOOL, 1), (NUM, 1)), ("TYPE", (TEXT, 0x300100), (NUM, 2)),
    ("ERROR.TYPE", (ERR, 3), (NUM, 3)), ("NOT", (BOOL, 1), F), ("ISEVEN", (NUM, -4), T),
    ("ISODD", (NUM, 3), T), ("ISFORMULA", (NUM, 1), (ERR, 3)), ("ISBLANK", (NUM, 0), F),
]


@pytest.mark.parametrize("fn,arg,want", VALS)
def test_direct(abi, fn, arg, want):
    got, steps = abi.call(299, FID[fn], [arg])
    assert got == want
    assert steps <= 3


REFS = [  # through a cell reference
    ("ISBLANK", "Z99", T), ("ISBLANK", "A1", F), ("ISNUMBER", "A1", T), ("ISNUMBER", "B2", F),
    ("ISTEXT", "B2", T), ("ISLOGICAL", "C3", T), ("ISNA", "D4", T), ("ISERROR", "D4", T), ("ISERR", "D4", F),
    ("ISREF", "A1", T), ("ISREF", "Z99", T), ("N", "A1", (NUM, 42)), ("N", "B2", (NUM, 0)),
    ("N", "D4", (ERR, 7)), ("TYPE", "C3", (NUM, 4)), ("TYPE", "Z99", (NUM, 1)), ("TYPE", "D4", (NUM, 16)),
    ("ERROR.TYPE", "D4", (NUM, 7)), ("ERROR.TYPE", "A1", (ERR, 7)), ("NOT", "Z99", T), ("NOT", "F6", T),
    ("NOT", "A1", F), ("ISEVEN", "A1", T), ("ISODD", "E5", T), ("ISEVEN", "Z99", T),
    ("ISFORMULA", "E5", T), ("ISFORMULA", "A1", F), ("ISFORMULA", "Z99", F), ("ISNONTEXT", "B2", F),
]


@pytest.mark.parametrize("fn,cell,want", REFS)
def test_ref(abi, fn, cell, want):
    got, steps = abi.call(299, FID[fn], [ref(abi, cell)])
    assert got == want


@pytest.mark.parametrize("fn,want", [("NA", (ERR, 7)), ("TRUE", T), ("FALSE", F)])
def test_nullary(abi, fn, want):
    got, steps = abi.call(299, FID[fn], [])
    assert got == want
