"""AND / OR / XOR through the ABI: lg_arg (300) -> lg_cfold (301) -> lg_fold (297) -> FN_RET.
Expected values by hand (Excel: text and blanks in referenced cells are ignored, direct text is
#VALUE!, no logical values is #VALUE!, first error in argument order is returned)."""
import pytest

from lgbb import BLANK, BOOL, ERR, MISS, NUM, TEXT, Abi

AND, OR, XOR = 12, 348, 514
T, F = (BOOL, 1), (BOOL, 0)


@pytest.fixture(scope="module")
def abi():
    a = Abi()
    a.set_cell("A1", BOOL, 1)
    a.set_cell("A2", BOOL, 0)
    a.set_cell("A3", NUM, 5)
    a.set_cell("A4", TEXT, 0x300100)
    a.set_cell("A5", ERR, 2)
    return a


def R(abi, c):
    return (9, abi.key(c))


CASES = [
    # args, AND, OR, XOR
    (lambda a: [T, T], T, T, F),
    (lambda a: [T, F, T], F, T, F),
    (lambda a: [F, F], F, F, F),
    (lambda a: [(NUM, 2)], T, T, T),
    (lambda a: [(NUM, 0), T], F, T, T),
    (lambda a: [T, (MISS, 0)], F, T, T),
    (lambda a: [R(a, "A1"), R(a, "A3")], T, T, F),
    (lambda a: [R(a, "A1"), R(a, "A2")], F, T, T),
    (lambda a: [R(a, "A4"), R(a, "A1")], T, T, T),          # referenced text ignored
    (lambda a: [R(a, "A4"), R(a, "Z9")], (ERR, 3), (ERR, 3), (ERR, 3)),  # no logical values
    (lambda a: [(TEXT, 0x300100), T], (ERR, 3), (ERR, 3), (ERR, 3)),     # direct text
    (lambda a: [T, R(a, "A5"), (ERR, 7)], (ERR, 2), (ERR, 2), (ERR, 2)),
    (lambda a: [(ERR, 7), R(a, "A5")], (ERR, 7), (ERR, 7), (ERR, 7)),
    (lambda a: [T, T, T, R(a, "A1"), R(a, "A2"), (NUM, -1)], F, T, T),
]


@pytest.mark.parametrize("k", range(len(CASES)))
def test_abi_fold(abi, k):
    mk, wa, wo, wx = CASES[k]
    args = mk(abi)
    for fid, want in ((AND, wa), (OR, wo), (XOR, wx)):
        got, steps = abi.call(300, fid, args, max_steps=2000)
        assert got == want, (fid, args)
        nref = sum(1 for t, _ in args if t == 9)
        # entry 1, 3 per argument (fetch, consume, fold), finish 3, FN_RET 1; a reference adds
        # CELL_GET (3 or 5 steps) plus write-back and refetch (2)
        base = 1 + 3 * len(args) + 3 + 1
        assert base + 5 * nref <= steps <= base + 7 * nref


def test_zero_args(abi):
    got, _ = abi.call(300, AND, [], max_steps=50)
    assert got == (ERR, 3)
