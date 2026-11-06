"""YEAR MONTH DAY HOUR MINUTE SECOND WEEKDAY core (dt_ymd, id 344). Expected values stated by hand
from Excel's documented 1900 date system: serial 1 = 1900-01-01, serial 60 = the fictitious
1900-02-29, serial 61 = 1900-03-01, 2958465 = 9999-12-31; 1900-01-01 counts as a Sunday."""
import pytest
from dtbb import result, call, W, NUM, TEXT, BOOL, ERR, MISSING, BLANK, VALUE, NUMERR

YMD = 344
YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, WEEKDAY = range(7)

DATES = [  # serial, y, m, d
    (0, 1900, 1, 0), (1, 1900, 1, 1), (31, 1900, 1, 31), (32, 1900, 2, 1), (59, 1900, 2, 28),
    (60, 1900, 2, 29), (61, 1900, 3, 1), (366, 1900, 12, 31), (367, 1901, 1, 1),
    (36526, 2000, 1, 1), (36585, 2000, 2, 29), (36586, 2000, 3, 1), (44927, 2023, 1, 1),
    (45292, 2024, 1, 1), (45351, 2024, 2, 29), (45658, 2025, 1, 1), (45657, 2024, 12, 31),
    (73050, 2099, 12, 31), (73051, 2100, 1, 1), (73109, 2100, 2, 28), (73110, 2100, 3, 1), (2958465, 9999, 12, 31), (45658.99, 2025, 1, 1)]


@pytest.mark.parametrize("s,y,m,d", DATES)
def test_ymd(s, y, m, d):
    assert result(YMD, s, sel=YEAR) == (NUM, y)
    assert result(YMD, s, sel=MONTH) == (NUM, m)
    assert result(YMD, s, sel=DAY) == (NUM, d)


TIMES = [  # serial, h, mi, s
    (0.5, 12, 0, 0), (0.75, 18, 0, 0), (0.25, 6, 0, 0), (45658.5, 12, 0, 0),
    (0.999988425925926, 23, 59, 59), (0.0000115740740740741, 0, 0, 1),
    (0.521527777777778, 12, 31, 0), (0.6044560185185185, 14, 30, 25),
    (0.99999999, 0, 0, 0)]  # rounds to 24:00:00, which wraps to 0


@pytest.mark.parametrize("s,h,mi,se", TIMES)
def test_hms(s, h, mi, se):
    assert result(YMD, s, sel=HOUR) == (NUM, h)
    assert result(YMD, s, sel=MINUTE) == (NUM, mi)
    assert result(YMD, s, sel=SECOND) == (NUM, se)


# 45658 = 2025-01-01, a Wednesday; 1 = 1900-01-01, Sunday in Excel; 36526 = Saturday
@pytest.mark.parametrize("s,rt,want", [
    (45658, None, 4), (45658, 1, 4), (45658, 2, 3), (45658, 3, 2), (45658, 11, 3),
    (45658, 12, 2), (45658, 13, 1), (45658, 14, 7), (45658, 15, 6), (45658, 16, 5),
    (45658, 17, 4), (1, None, 1), (0, None, 7), (36526, None, 7), (36526, 2, 6), (36526, 3, 5),
    (45292, 2, 1), (45292, 3, 0), (45292, 1.9, 4 - 2), (60, 1, 4), (61, 1, 5)])
def test_weekday(s, rt, want):
    b = (MISSING, 0) if rt is None else rt
    assert result(YMD, s, b, sel=WEEKDAY) == (NUM, want)


@pytest.mark.parametrize("rt", [0, 4, 10, 18, -1, 1e300, (BLANK, 0)])
def test_weekday_bad_type(rt):
    assert result(YMD, 45658, rt, sel=WEEKDAY) == (ERR, NUMERR)


def test_errors():
    for sel in range(7):
        assert result(YMD, -1, sel=sel) == (ERR, NUMERR)
        assert result(YMD, 2958466, sel=sel) == (ERR, NUMERR)
        assert result(YMD, 1e308, sel=sel) == (ERR, NUMERR)
        assert result(YMD, (TEXT, 0x302000), sel=sel) == (ERR, VALUE)
        assert result(YMD, (ERR, 7), sel=sel) == (ERR, 7)
    assert result(YMD, (ERR, 2), (TEXT, 5), sel=WEEKDAY) == (ERR, 2)
    assert result(YMD, 45658, (ERR, 7), sel=WEEKDAY) == (ERR, 7)
    assert result(YMD, 45658, (TEXT, 5), sel=WEEKDAY) == (ERR, VALUE)
    assert result(YMD, -5, (ERR, 7), sel=WEEKDAY) == (ERR, 7)


def test_coercion():
    assert result(YMD, (BOOL, 1), sel=YEAR) == (NUM, 1900)
    assert result(YMD, (BOOL, 1), sel=DAY) == (NUM, 1)
    assert result(YMD, (BLANK, 0), sel=DAY) == (NUM, 0)
    assert result(YMD, (BLANK, 0), sel=MONTH) == (NUM, 1)


def test_parts_registers_and_return():
    out, _ = call(YMD, 45658.6044560185185185, sel=YEAR, regs={"LR": 3, "LP": 5})
    assert [float(out[W[k]]) for k in ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8")] == \
        [2025, 1, 1, 14, 30, 25, 4, 45658]
