"""lg_fold (id 297): AND / OR / XOR folds. Expected values by hand from Excel docs:
AND is TRUE when every logical value is TRUE, OR when any is, XOR when an odd number are.
Numbers count as TRUE when nonzero. Text and blanks inside references are ignored; a text
argument given directly is #VALUE!. No logical values at all gives #VALUE!. The first error
met is returned. A missing argument counts as FALSE."""
import pytest

from lgbb import BLANK, BOOL, ERR, MISS, NUM, TEXT, W, call, check_pass

INIT, DIRECT, FROMREF, F_AND, F_OR, F_XOR = 1, 2, 3, 4, 5, 6


def fold(args, fin):
    """args: list of (mode, tag, pay). Threads the accumulator (C, N0, N1) through calls."""
    regs = {"T0": INIT, "CT": 77, "CP": 88, "T3": 5, "T4": 9}
    seq = [(INIT, NUM, 0)] + list(args) + [(fin, NUM, 0)]
    acc = None
    for mode, tag, pay in seq:
        r = dict(T0=mode, AT=tag, AP=pay)
        if acc:
            r.update(CT=acc[0], CP=acc[1], T3=acc[2], T4=acc[3])
        else:
            r.update(CT=77, CP=88, T3=5, T4=9)
        out, x = call("lg_fold", **r)
        changed = {12, 13, 14, 17, 18, 32, 33}
        check_pass(out, x, changed)
        if mode not in (F_AND, F_OR, F_XOR):
            assert (out[13], out[14]) == (tag, pay)  # A untouched
        acc = (out[17], out[18], out[32], out[33])
    return (out[13], out[14])


T, F = (BOOL, 1), (BOOL, 0)
D = lambda t, p: (DIRECT, t, p)  # noqa: E731
R = lambda t, p: (FROMREF, t, p)  # noqa: E731
CASES = [
    ([D(BOOL, 1), D(BOOL, 1)], T, T, F),
    ([D(BOOL, 1), D(BOOL, 0)], F, T, T),
    ([D(BOOL, 0), D(BOOL, 0)], F, F, F),
    ([D(BOOL, 1), D(BOOL, 1), D(BOOL, 1)], T, T, T),
    ([D(NUM, 5), D(NUM, -0.25)], T, T, F),
    ([D(NUM, 0), D(NUM, 2)], F, T, T),
    ([D(NUM, 1e300)], T, T, T),
    ([D(BOOL, 1), D(MISS, 0)], F, T, T),
    ([R(TEXT, 0x300000), R(BOOL, 1), R(BLANK, 0)], T, T, T),
    ([R(TEXT, 0x300000), R(BLANK, 0)], (ERR, 3), (ERR, 3), (ERR, 3)),
    ([D(TEXT, 0x300000), D(BOOL, 1)], (ERR, 3), (ERR, 3), (ERR, 3)),
    ([D(BOOL, 1), D(ERR, 2), D(ERR, 7)], (ERR, 2), (ERR, 2), (ERR, 2)),
    ([R(ERR, 7), R(BOOL, 1)], (ERR, 7), (ERR, 7), (ERR, 7)),
    ([], (ERR, 3), (ERR, 3), (ERR, 3)),
    ([R(BOOL, 1), R(NUM, 3), R(BOOL, 1), R(NUM, 0), R(BOOL, 0)], F, T, T),
    ([R(BOOL, 1), R(NUM, 3), R(BOOL, 1), R(NUM, 4)], T, T, F),
]


@pytest.mark.parametrize("args,a,o,x", CASES)
def test_fold(args, a, o, x):
    assert fold(args, F_AND) == a
    assert fold(args, F_OR) == o
    assert fold(args, F_XOR) == x
