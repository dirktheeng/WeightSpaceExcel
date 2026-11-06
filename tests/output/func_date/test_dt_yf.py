"""YEARFRAC through dt_pair (347) -> dt_ymd (344) twice -> dt_yf (353). Expected values stated by hand
from Excel's documented bases (0 US 30/360, 1 actual/actual, 2 actual/360, 3 actual/365, 4 European 30/360)
and the published reconstruction of Excel's basis 0 and 1 rules (D. A. Wheeler, "YEARFRAC")."""
import pytest
from dtbb import result, NUM, TEXT, ERR, MISSING, BLANK, VALUE, NUMERR

PAIR = 347


def yf(s, e, b=None):
    return result(PAIR, s, e, (MISSING, 0) if b is None else b, regs={"N1": 3})


# 45292 = 2024-01-01, 45474 = 2024-07-01 (182 days later), 45658 = 2025-01-01, 44927 = 2023-01-01
@pytest.mark.parametrize("s,e,b,want", [
    (45292, 45658, None, 1.0), (45292, 45658, 0, 1.0), (45292, 45474, 0, 0.5), (45292, 45474, 4, 0.5),
    (45292, 45292, 1, 0.0), (45658, 45292, 0, 1.0),
    (45322, 45382, 0, 60 / 360), (45322, 45382, 4, 60 / 360),          # 01-31 to 03-31
    (45351, 45716, 0, 1.0),          # 2024-02-29 to 2025-02-28: both last of February -> 30, 30
    (45292, 45351, 0, 58 / 360),     # to 2024-02-29: end of February kept (start is not)
    (45351, 45382, 0, 31 / 360),     # 2024-02-29 to 03-31: start -> 30 but end 31 kept (basis 0 rule
    #                                  "start last of Feb -> 30" is the last case; DAYS360 differs)
    (45351, 45382, 4, 31 / 360),     # European: 29 stays, 31 -> 30
    (45293, 45382, 0, 89 / 360)])    # 2024-01-02 to 03-31
def test_yearfrac_30_360(s, e, b, want):
    tag, v = yf(s, e, b)
    assert tag == NUM and abs(v - want) <= 1e-15 * max(1, abs(want))


@pytest.mark.parametrize("s,e,b,num,den", [
    (45292, 45474, 1, 182, 366), (45292, 45474, 2, 182, 360), (45292, 45474, 3, 182, 365),
    (45658, 45839, 1, 181, 365),     # 2025-01-01 to 2025-07-01, non-leap year
    (45292, 45658, 1, 366, 366),     # one year spanning a Feb 29 at the start
    (45658, 45292, 1, 366, 366),     # reversed arguments give the same positive result
    (45351, 45716, 1, 365, 366),     # 2024-02-29 to 2025-02-28
    (45474, 45839, 1, 365, 365),     # 2024-07-01 to 2025-07-01: no Feb 29 inside
    (45657, 46022, 1, 365, 365),     # 2024-12-31 to 2025-12-31
    (45566, 45932, 1, 366, 366),     # 2024-10-01 to 2025-10-02: more than a year -> average
    #   the line above is not within a year (months equal, d1 < d2), average of 2024 and 2025
    #   = (366 + 365) / 2 = 365.5: 366 / 365.5 is checked separately below
    (44927, 46023, 1, 1096 * 4, 1461),   # 2023-01-01 to 2026-01-01: 4 years averaging 365.25
    (45292, 45474, 0, 180, 360)])
def test_yearfrac_actual(s, e, b, num, den):
    tag, v = yf(s, e, b)
    if (s, e) == (45566, 45932):
        num, den = 366, 365.5
    assert tag == NUM and abs(v - num / den) <= 1e-15 * (num / den)


def test_yearfrac_errors():
    for b in (5, -1, 1e300, 4.9 + 0.2):
        assert yf(45292, 45658, b) == (ERR, NUMERR)
    assert yf(45292, 45658, 4.9) == (NUM, 1.0)          # truncated to 4
    assert yf(45292, 45658, (ERR, 7)) == (ERR, 7)
    assert yf(45292, 45658, (TEXT, 5)) == (ERR, VALUE)
    assert yf(-1, 45658) == (ERR, NUMERR)
    assert yf((ERR, 2), 45658, (ERR, 7)) == (ERR, 2)
    assert yf(45292, 45658, (BLANK, 0)) == (NUM, 1.0)
