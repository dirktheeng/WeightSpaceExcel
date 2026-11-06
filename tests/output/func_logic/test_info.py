"""lg_info (id 296): unary Information / Logical functions. Expected values by hand from Excel docs."""
import pytest

from lgbb import ARR, BLANK, BOOL, E, ERR, LAM, MISS, NUM, REF, TEXT, W, call, check_pass

SEL = {"ISBLANK": 1, "ISNUMBER": 2, "ISTEXT": 3, "ISLOGICAL": 4, "ISERROR": 5, "ISERR": 6,
       "ISNA": 7, "ISNONTEXT": 8, "ISREF": 9, "N": 10, "TYPE": 11, "ERROR.TYPE": 12, "NOT": 13,
       "ISEVEN": 14, "ISODD": 15, "NA": 16, "TRUE": 17, "FALSE": 18}
T, F = (BOOL, 1), (BOOL, 0)
V = {
    "blank": (BLANK, 0), "num": (NUM, 3.5), "neg": (NUM, -7.25), "zero": (NUM, 0), "text": (TEXT, 0x300010),
    "true": (BOOL, 1), "false": (BOOL, 0), "na": (ERR, 7), "div0": (ERR, 2), "ref": (REF, 0xB0010),
    "arr": (ARR, 0xB0020),
}
CASES = [
    # (function, argument, expected (tag, pay))
    ("ISBLANK", "blank", T), ("ISBLANK", "zero", F), ("ISBLANK", "text", F), ("ISBLANK", "na", F),
    ("ISNUMBER", "num", T), ("ISNUMBER", "zero", T), ("ISNUMBER", "true", F), ("ISNUMBER", "blank", F), ("ISNUMBER", "text", F),
    ("ISTEXT", "text", T), ("ISTEXT", "num", F), ("ISTEXT", "blank", F),
    ("ISLOGICAL", "true", T), ("ISLOGICAL", "false", T), ("ISLOGICAL", "zero", F),
    ("ISERROR", "na", T), ("ISERROR", "div0", T), ("ISERROR", "num", F),
    ("ISERR", "div0", T), ("ISERR", "na", F), ("ISERR", "num", F), ("ISERR", "neg", F),
    ("ISNA", "na", T), ("ISNA", "div0", F), ("ISNA", "num", F),
    ("ISNONTEXT", "text", F), ("ISNONTEXT", "blank", T), ("ISNONTEXT", "na", T), ("ISNONTEXT", "num", T),
    ("ISREF", "ref", T), ("ISREF", "num", F), ("ISREF", "text", F),
    ("N", "num", (NUM, 3.5)), ("N", "neg", (NUM, -7.25)), ("N", "true", (NUM, 1)), ("N", "false", (NUM, 0)),
    ("N", "text", (NUM, 0)), ("N", "blank", (NUM, 0)), ("N", "div0", (ERR, 2)),
    ("TYPE", "num", (NUM, 1)), ("TYPE", "blank", (NUM, 1)), ("TYPE", "text", (NUM, 2)), ("TYPE", "true", (NUM, 4)),
    ("TYPE", "na", (NUM, 16)), ("TYPE", "arr", (NUM, 64)),
    ("ERROR.TYPE", "na", (NUM, 7)), ("ERROR.TYPE", "div0", (NUM, 2)), ("ERROR.TYPE", "num", (ERR, 7)),
    ("ERROR.TYPE", "text", (ERR, 7)),
    ("NOT", "true", F), ("NOT", "false", T), ("NOT", "zero", T), ("NOT", "num", F), ("NOT", "neg", F),
    ("NOT", "blank", T), ("NOT", "text", (ERR, 3)), ("NOT", "na", (ERR, 7)),
    ("ISEVEN", "zero", T), ("ISEVEN", "blank", T), ("ISEVEN", "true", (ERR, 3)), ("ISEVEN", "text", (ERR, 3)),
    ("ISEVEN", "div0", (ERR, 2)),
    ("ISODD", "zero", F), ("ISODD", "blank", F), ("ISODD", "text", (ERR, 3)),
    ("NA", "num", (ERR, 7)), ("TRUE", "num", T), ("FALSE", "text", F),
]
NUMS = [  # ISEVEN / ISODD truncate toward zero
    (2, 1), (3, 0), (2.5, 1), (3.9, 0), (-3, 0), (-2.5, 1), (-0.5, 1), (0.5, 1), (1, 0), (1.5, 0),
    (5, 0), (7.5, 0), (1e14, 1), (99999999999999.0, 0), (123456789.75, 0), (2**49 + 1, 0),
]


def run(fn, tag, pay):
    out, x = call("lg_info", T0=SEL[fn], AT=tag, AP=pay)
    check_pass(out, x, {W["STATUS"], W["AT"], W["AP"]})
    assert out[W["STATUS"]] == 0
    return (out[W["AT"]], out[W["AP"]])


@pytest.mark.parametrize("fn,arg,want", CASES)
def test_info(fn, arg, want):
    assert run(fn, *V[arg]) == want


@pytest.mark.parametrize("x,even", NUMS)
def test_parity(x, even):
    assert run("ISEVEN", NUM, x) == (BOOL, even)
    assert run("ISODD", NUM, x) == (BOOL, 1 - even)


def test_parity_too_large():
    # documented limit: |x| > 2^50 gives #NUM! (Excel's exact limit is an open question)
    assert run("ISEVEN", NUM, 1e20) == (ERR, 6)
