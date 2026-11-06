"""DATE, EDATE, EOMONTH (dt_date, id 345; EDATE and EOMONTH also run dt_ymd, 344).
Expected serials stated by hand: 45658 = 2025-01-01 (36526 = 2000-01-01, plus 25 years of 365 days
plus 7 leap days = 9132), 45292 = 2024-01-01, 60 = 1900-02-29 (Excel's fictitious day)."""
import pytest
from dtbb import result, NUM, TEXT, BOOL, ERR, MISSING, BLANK, VALUE, NUMERR

DT = 345
EDATE, EOMONTH = {"PC": 3}, {"PC": 4}


@pytest.mark.parametrize("y,m,d,want", [
    (2025, 1, 1, 45658), (2024, 1, 1, 45292), (2024, 2, 29, 45351), (2024, 3, 1, 45352),
    (2023, 2, 29, 44986),                           # 2023-03-01
    (1900, 1, 1, 1), (1900, 2, 28, 59), (1900, 2, 29, 60), (1900, 3, 1, 61), (1900, 3, 0, 60),
    (1900, 1, 0, 0), (1900, 2, 30, 61), (1900, 1, 61, 61),
    (0, 1, 1, 1), (99, 12, 31, 36525), (100, 1, 1, 36526),  # 100 -> 2000
    (1899, 1, 1, 693598),  # 3799-01-01: 3600-01-01 = 36526 + 4*146097 = 620914; +200 years with
    # 49 leap days = 73049 -> 3800-01-01 = 693963; minus 365 -> 693598
    (2024, 14, 1, 45689), (2024, 0, 1, 45261), (2024, -12, 1, 44896), (2024, 13, 0, 45657),
    (2025, 1, -5, 45652), (2025, 1, 366, 46023),    # 2025-12-31 + 1 = 2026-01-01
    (9999, 12, 31, 2958465), (2000, 1, 1.9, 36526), (2000.7, 1.9, 1, 36526), (1999, 12, 32, 36526),
    ((BOOL, 1), 1, 1, 367),                          # TRUE -> year 1 -> 1901
    (2000, (BOOL, 1), (BOOL, 1), 36526)])
def test_date(y, m, d, want):
    assert result(DT, y, m, d) == (NUM, want)


@pytest.mark.parametrize("y,m,d,err", [
    (10000, 1, 1, NUMERR), (-1, 1, 1, NUMERR), (1900, 1, -1, NUMERR), (9999, 12, 32, NUMERR),
    (1e300, 1, 1, NUMERR), (2000, 1e300, 1, NUMERR), (2000, 1, -1e300, NUMERR),
    ((TEXT, 0x302000), 1, 1, VALUE), (2000, (TEXT, 0x302000), 1, VALUE),
    ((ERR, 7), (ERR, 2), 1, 7), (2000, (ERR, 2), (ERR, 7), 2), (2000, 1, (ERR, 4), 4),
    (2000, 1, (TEXT, 1), VALUE), (10000, (ERR, 2), 1, 2), (10000, 1, (TEXT, 1), VALUE)])
def test_date_errors(y, m, d, err):
    assert result(DT, y, m, d) == (ERR, err)


@pytest.mark.parametrize("s,k,ed,eo", [
    (45688, 1, 45716, 45716),        # 2025-01-31 + 1 -> 2025-02-28; end of Feb 2025
    (45322, 1, 45351, 45351),        # 2024-01-31 + 1 -> 2024-02-29
    (45658, -1, 45627, 45657),       # 2025-01-01 - 1 -> 2024-12-01; 2024-12-31
    (45688, 0, 45688, 45688),
    (45658, 12, 46023, 46053),       # 2026-01-01; 2026-01-31
    (45351, 12, 45716, 45716),       # 2024-02-29 + 12 -> 2025-02-28
    (45351, 48, 46812, 46812),       # 2028-02-29
    (45658, 1.9, 45689, 45716),      # months truncated to 1
    (45658, -1.9, 45627, 45657),     # truncated toward zero: -1
    (31, 1, 60, 60),                 # 1900-01-31 + 1 -> 1900-02-29 (fictitious day kept)
    (45658.75, 0, 45658, 45688)])    # time part dropped
def test_edate_eomonth(s, k, ed, eo):
    assert result(DT, s, k, regs=EDATE) == (NUM, ed)
    assert result(DT, s, k, regs=EOMONTH) == (NUM, eo)


def test_edate_errors():
    for r in (EDATE, EOMONTH):
        assert result(DT, -1, 1, regs=r) == (ERR, NUMERR)
        assert result(DT, 2958465, 1, regs=r) == (ERR, NUMERR)
        assert result(DT, 10, -1, regs=r) == (ERR, NUMERR)   # 1899-12 is before serial 1
        assert result(DT, (ERR, 7), (ERR, 2), regs=r) == (ERR, 7)
        assert result(DT, 45658, (ERR, 2), regs=r) == (ERR, 2)
        assert result(DT, 45658, (TEXT, 9), regs=r) == (ERR, VALUE)
        assert result(DT, (TEXT, 9), 1, regs=r) == (ERR, VALUE)
