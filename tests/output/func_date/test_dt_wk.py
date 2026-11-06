"""WEEKNUM and ISOWEEKNUM (dt_wk, 350, which calls dt_ymd 344). Stated by hand from calendars:
2025-01-01 (45658) is a Wednesday, 2024-01-01 (45292) a Monday, 2023-01-01 (44927) a Sunday.
Excel counts 1900-01-01 (serial 1) as a Sunday."""
import pytest
from dtbb import result, NUM, TEXT, ERR, MISSING, BLANK, VALUE, NUMERR

WK = 350


def wn(s, t=None):
    return result(WK, s, (MISSING, 0) if t is None else t, regs={"N1": 0})


def iso(s):
    return result(WK, s, regs={"N1": 1})


@pytest.mark.parametrize("s,t,want", [
    (45658, None, 1), (45661, None, 1), (45662, None, 2), (45662, 1, 2), (45662, 2, 1), (45663, 2, 2),
    (45662, 11, 1), (45662, 17, 2),
    (45659, 12, 1), (45660, 12, 1),       # 2025-01-02 Thu, 01-03 Fri; Tuesday start: Jan 7 opens week 2
    (45664, 12, 2), (45663, 12, 1),       # 01-07 Tue -> 2, 01-06 Mon -> 1
    (45660, 14, 2), (45659, 14, 2), (45658, 14, 1),   # Thursday start: Jan 2 opens week 2
    (45660, 15, 2), (45661, 16, 2), (45660, 16, 1),   # Friday start: Jan 3; Saturday start: Jan 4
    (45657, None, 53), (45657, 2, 53), (45291, None, 53), (45291, 2, 53), (45292, 2, 1), (45298, None, 2),
    (60, None, 9), (60, 2, 10), (1, None, 1),
    (0, None, 0),                         # "1900-01-00" lies before week 1 (Excel value not verified)
    (45658, 21, 1), (45657, 21, 1), (45291, 21, 52)])
def test_weeknum(s, t, want):
    assert wn(s, t) == (NUM, want)


@pytest.mark.parametrize("s,want", [
    (45658, 1), (45662, 1), (45663, 2), (45657, 1), (45656, 1),  # 2024-12-30 Mon starts 2025-W01
    (45655, 52), (45291, 52), (45292, 1), (44927, 52),           # 2023-01-01 Sunday is 2022-W52
    (44928, 1), (46022, 1),                                      # 2025-12-31 Wed is 2026-W01
    (46385, 53),                                                  # 2026-12-31 Thu: 2026 has 53 weeks
    (1, 52), (2, 1)])                                            # Excel's Sunday 1900-01-01; Monday the 2nd
def test_isoweeknum(s, want):
    assert iso(s) == (NUM, want)


def test_week_errors():
    for t in (0, 3, 10, 18, 20, 22, -1, (BLANK, 0)):
        assert wn(45658, t) == (ERR, NUMERR)
    assert wn(45658, (ERR, 7)) == (ERR, 7)
    assert wn(45658, (TEXT, 5)) == (ERR, VALUE)
    assert wn((ERR, 2), (ERR, 7)) == (ERR, 2)
    assert wn(-1) == (ERR, NUMERR)
    assert iso(-1) == (ERR, NUMERR)
    assert iso((TEXT, 5)) == (ERR, VALUE)
    assert result(WK, 45658, (TEXT, 5), regs={"N1": 1}) == (NUM, 1)   # ISOWEEKNUM ignores B
