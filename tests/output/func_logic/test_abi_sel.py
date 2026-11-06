"""IF, IFS, SWITCH, IFERROR, IFNA through the ABI: lg_arg (300) -> lg_csel (302) -> FN_RET.
Expected values by hand from Excel's documented behaviour."""
import pytest

from lgbb import BLANK, BOOL, ERR, MISS, NUM, TEXT, Abi

IF, IFERROR, IFNA, IFS, SWITCH = 218, 219, 220, 221, 449
T, F = (BOOL, 1), (BOOL, 0)
NA, DIV0, VAL = (ERR, 7), (ERR, 2), (ERR, 3)
S1, S2 = (TEXT, 0x300100), (TEXT, 0x300200)


@pytest.fixture(scope="module")
def abi():
    a = Abi()
    a.set_cell("A1", NUM, 1)
    a.set_cell("A2", NUM, 0)
    a.set_cell("A3", ERR, 7)
    a.set_cell("A4", ERR, 2)
    a.set_cell("A5", BOOL, 1)
    a.set_cell("A6", NUM, 3)
    return a


def R(a, c):
    return (9, a.key(c))


CASES = [
    # (fid, args builder, expected)
    (IF, lambda a: [T, (NUM, 10), (NUM, 20)], (NUM, 10)),
    (IF, lambda a: [F, (NUM, 10), (NUM, 20)], (NUM, 20)),
    (IF, lambda a: [(NUM, 0.5), S1, S2], S1),
    (IF, lambda a: [(NUM, 0), S1, S2], S2),
    (IF, lambda a: [F, (NUM, 10)], F),                      # no else: FALSE
    (IF, lambda a: [T, (NUM, 10)], (NUM, 10)),
    (IF, lambda a: [T, (MISS, 0), (NUM, 2)], (NUM, 0)),     # omitted branch is 0
    (IF, lambda a: [F, (NUM, 1), (MISS, 0)], (NUM, 0)),
    (IF, lambda a: [DIV0, (NUM, 1), (NUM, 2)], DIV0),       # error condition propagates
    (IF, lambda a: [T, (NUM, 1), NA], (NUM, 1)),            # unselected error ignored
    (IF, lambda a: [F, NA, (NUM, 2)], (NUM, 2)),
    (IF, lambda a: [S1, (NUM, 1), (NUM, 2)], VAL),          # text condition
    (IF, lambda a: [R(a, "A1"), (NUM, 1), (NUM, 2)], (NUM, 1)),
    (IF, lambda a: [R(a, "A2"), (NUM, 1), (NUM, 2)], (NUM, 2)),
    (IF, lambda a: [R(a, "Z9"), (NUM, 1), (NUM, 2)], (NUM, 2)),   # blank cell is FALSE
    (IF, lambda a: [R(a, "A3"), (NUM, 1), (NUM, 2)], NA),
    (IF, lambda a: [T, R(a, "A6"), (NUM, 2)], (9, 5 * 2**14)),  # A6: row 5, col 0   # branch returned as a reference
    (IFERROR, lambda a: [DIV0, (NUM, 9)], (NUM, 9)),
    (IFERROR, lambda a: [NA, S1], S1),
    (IFERROR, lambda a: [(NUM, 4), (NUM, 9)], (NUM, 4)),
    (IFERROR, lambda a: [R(a, "A4"), (NUM, 9)], (NUM, 9)),
    (IFERROR, lambda a: [R(a, "A1"), (NUM, 9)], (NUM, 1)),
    (IFERROR, lambda a: [(NUM, 4), NA], (NUM, 4)),
    (IFNA, lambda a: [NA, (NUM, 9)], (NUM, 9)),
    (IFNA, lambda a: [DIV0, (NUM, 9)], DIV0),
    (IFNA, lambda a: [S1, (NUM, 9)], S1),
    (IFNA, lambda a: [R(a, "A3"), (NUM, 5)], (NUM, 5)),
    (IFS, lambda a: [F, (NUM, 1), T, (NUM, 2), T, (NUM, 3)], (NUM, 2)),
    (IFS, lambda a: [T, (NUM, 1)], (NUM, 1)),
    (IFS, lambda a: [F, (NUM, 1), F, (NUM, 2)], NA),
    (IFS, lambda a: [F, (NUM, 1), DIV0, (NUM, 2)], DIV0),
    (IFS, lambda a: [R(a, "A2"), (NUM, 1), R(a, "A5"), S1], S1),
    (IFS, lambda a: [F, NA, (NUM, 7), (NUM, 2)], (NUM, 2)),
    (SWITCH, lambda a: [(NUM, 2), (NUM, 1), S1, (NUM, 2), S2], S2),
    (SWITCH, lambda a: [(NUM, 1), (NUM, 1), S1, (NUM, 2), S2], S1),
    (SWITCH, lambda a: [(NUM, 3), (NUM, 1), S1, (NUM, 2), S2], NA),
    (SWITCH, lambda a: [(NUM, 3), (NUM, 1), S1, (NUM, 2), S2, (NUM, 99)], (NUM, 99)),
    (SWITCH, lambda a: [(NUM, 1), (NUM, 1), S1, (NUM, 99)], S1),
    (SWITCH, lambda a: [T, (NUM, 1), S1, T, S2], S2),        # TRUE does not match 1
    (SWITCH, lambda a: [(NUM, 1), T, S1, (NUM, 1), S2], S2),
    (SWITCH, lambda a: [NA, (NUM, 1), S1, (NUM, 9)], NA),
    (SWITCH, lambda a: [R(a, "A6"), (NUM, 1), S1, (NUM, 3), S2], S2),
    (SWITCH, lambda a: [(NUM, 3), (NUM, 1), S1, R(a, "A6"), S2], S2),
    (SWITCH, lambda a: [(NUM, 0.1), (NUM, 0.2), S1, (NUM, 0.1), S2], S2),
    (SWITCH, lambda a: [S1, S1, (NUM, 5), (NUM, 6)], (NUM, 5)),   # same string
]


@pytest.mark.parametrize("k", range(len(CASES)))
def test_abi_sel(abi, k):
    fid, mk, want = CASES[k]
    got, steps = abi.call(300, fid, mk(abi), max_steps=2000)
    assert got == want
