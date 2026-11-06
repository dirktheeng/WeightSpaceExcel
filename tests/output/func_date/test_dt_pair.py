"""DAYS, DAYS360, DATEDIF through dt_pair (347) -> dt_ymd (344, twice) -> dt_fin2 (348).
Serials stated by hand: 44927 = 2023-01-01, 45292 = 2024-01-01, 45658 = 2025-01-01, 46023 = 2026-01-01;
others are offsets from these by the month lengths."""
import pytest
from dtbb import result, NUM, TEXT, BOOL, ERR, MISSING, BLANK, VALUE, NUMERR

PAIR = 347
DAYS, D360, DIF = {"N1": 0}, {"N1": 1}, {"N1": 2}
H = 0x302010  # a text heap string written by the test (encodings/memory-map.md section 9)


def text(t):
    w = 0
    for i, ch in enumerate(t):
        w += ord(ch) * 65536 ** i
    return {H: len(t), H + 2: w}


@pytest.mark.parametrize("end,start,want", [
    (45658, 45292, 366), (45292, 45658, -366), (45658.9, 45658.1, 0), (61, 59, 2), (1, 0, 1),
    (2958465, 1, 2958464)])
def test_days(end, start, want):
    assert result(PAIR, end, start, regs=DAYS) == (NUM, want)


def test_days_errors():
    assert result(PAIR, -1, 5, regs=DAYS) == (ERR, NUMERR)
    assert result(PAIR, 5, 2958466, regs=DAYS) == (ERR, NUMERR)
    assert result(PAIR, (ERR, 7), (ERR, 2), regs=DAYS) == (ERR, 7)
    assert result(PAIR, 5, (ERR, 2), regs=DAYS) == (ERR, 2)
    assert result(PAIR, (TEXT, 9), 5, regs=DAYS) == (ERR, VALUE)


# 45322 = 2024-01-31, 45351 = 2024-02-29, 45382 = 2024-03-31, 45716 = 2025-02-28, 45747 = 2025-03-31
@pytest.mark.parametrize("s,e,method,want", [
    (45292, 45658, None, 360), (45322, 45351, None, 29), (45351, 45382, None, 30),
    (45351, 45382, (BOOL, 1), 31), (45322, 45382, None, 60), (45322, 45382, (BOOL, 1), 60),
    (45716, 45747, None, 30), (45716, 45747, (BOOL, 1), 32),
    (45293, 45382, None, 89),            # 2024-01-02 to 03-31: d2 = 31 kept since d1 < 30: 60 + 31 - 2
    (45293, 45382, (BOOL, 1), 88),       # European: 31 -> 30
    (45658, 45292, None, -360), (45292, 45292, (BOOL, 0), 0), (45292, 45293, 1, 1)])
def test_days360(s, e, method, want):
    c = (MISSING, 0) if method is None else method
    assert result(PAIR, s, e, c, regs=D360) == (NUM, want)


def test_days360_errors():
    assert result(PAIR, 45292, 45658, (ERR, 7), regs=D360) == (ERR, 7)
    assert result(PAIR, 45292, 45658, (TEXT, H), regs=D360, mem=text("x")) == (ERR, VALUE)
    assert result(PAIR, -1, 45658, regs=D360) == (ERR, NUMERR)


# 44957 = 2023-01-31, 46143 = 2026-05-01, 45337 = 2024-02-15, 45366 = 2024-03-15
@pytest.mark.parametrize("s,e,unit,want", [
    (44957, 46143, "Y", 3), (44957, 46143, "M", 39), (44957, 46143, "D", 1186),
    (44957, 46143, "MD", 0), (44957, 46143, "YM", 3), (44957, 46143, "YD", 90),
    (44957, 46143, "y", 3), (44957, 46143, "md", 0), (44957, 46143, "Ym", 3), (44957, 46143, "yD", 90),
    (44957, 44986, "MD", -2),            # 2023-01-31 to 2023-03-01: Excel's documented MD quirk
    (45337, 45366, "M", 1), (45337, 45365, "M", 0), (45337, 45365, "MD", 28),
    (45292, 45658, "Y", 1), (45292, 45657, "Y", 0), (45292, 45657, "YD", 365),
    (45351, 45716, "Y", 0), (45351, 45716, "YD", 365),   # 2024-02-29 to 2025-02-28
    (45351, 45717, "Y", 1), (45351, 45717, "YD", 0),     # to 2025-03-01 (DATE(2025,2,29))
    (45658, 45658, "D", 0), (45658, 45658, "Y", 0)])
def test_datedif(s, e, unit, want):
    assert result(PAIR, s, e, (TEXT, H), regs=DIF, mem=text(unit)) == (NUM, want)


def test_datedif_errors():
    assert result(PAIR, 45658, 45292, (TEXT, H), regs=DIF, mem=text("D")) == (ERR, NUMERR)
    assert result(PAIR, 45292, 45658, (TEXT, H), regs=DIF, mem=text("X")) == (ERR, NUMERR)
    assert result(PAIR, 45292, 45658, (TEXT, H), regs=DIF, mem=text("YY")) == (ERR, NUMERR)
    assert result(PAIR, 45292, 45658, (TEXT, H), regs=DIF, mem=text("")) == (ERR, NUMERR)
    assert result(PAIR, 45292, 45658, 1, regs=DIF) == (ERR, NUMERR)
    assert result(PAIR, 45292, 45658, (ERR, 7), regs=DIF) == (ERR, 7)
    assert result(PAIR, (ERR, 2), 45658, (ERR, 7), regs=DIF) == (ERR, 2)
