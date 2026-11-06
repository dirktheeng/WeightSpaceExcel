"""TIME (dt_time, id 346). Expected values stated by hand: TIME(h, m, s) is
MOD(3600 h + 60 m + s, 86400) / 86400 with truncated arguments (Excel documents wrap past 24 hours,
#NUM! for an argument above 32767 or a negative time)."""
import pytest
from dtbb import result, NUM, TEXT, BOOL, ERR, MISSING, BLANK, VALUE, NUMERR

TM = 346


@pytest.mark.parametrize("h,m,s,want", [   # exact binary fractions
    (12, 0, 0, 0.5), (6, 0, 0, 0.25), (18, 0, 0, 0.75), (3, 0, 0, 0.125), (0, 0, 0, 0.0),
    (24, 0, 0, 0.0), (36, 0, 0, 0.5), (0, 720, 0, 0.5), (0, 0, 21600, 0.25), (11, 0, 3600, 0.5),
    (12, -60, 3600, 0.5), (12.9, 0.5, 0.99, 0.5), (32766, 0, 0, 0.25)])  # 32766 h = 1365 d + 6 h
def test_time_exactish(h, m, s, want):
    tag, v = result(TM, h, m, s)
    assert tag == NUM
    assert v == want


@pytest.mark.parametrize("h,m,s,want", [   # stated decimals, compared to 1e-15 relative
    (0, 0, 1, 0.0000115740740740741), (8, 0, 0, 0.333333333333333), (16, 0, 0, 0.666666666666667),
    (14, 30, 25, 0.6044560185185185), (23, 59, 59, 0.999988425925926), (1, 2, 3, 0.0430902777777778),
    (11, 59, 3600, 0.540972222222222),            # 12:59
    (32767, 0, 0, 0.291666666666667),             # 32767 h = 1365 d + 7 h
    (0, 32767, 0, 0.754861111111111),             # 32767 min = 22 d 18 h 7 min = 1087 / 1440
    ((BOOL, 1), (BLANK, 0), (MISSING, 0), 0.0416666666666667)])
def test_time_values(h, m, s, want):
    tag, v = result(TM, h, m, s)
    assert tag == NUM and abs(v - want) <= 1e-14 * want


def test_time_correctly_rounded_thirds():
    # 8:00 is 1/3: the correctly rounded double is 0.333333333333333314829616256247...; its
    # neighbours differ by 5.55e-17, so a 1e-17 window pins the exact double.
    tag, v = result(TM, 8, 0, 0)
    assert abs(v - 0.3333333333333333148) < 1e-17


@pytest.mark.parametrize("h,m,s,err", [
    (32768, 0, 0, NUMERR), (0, 32768, 0, NUMERR), (0, 0, 32768, NUMERR), (-1, 0, 0, NUMERR), (0, 0, 43200, NUMERR),
    (0, 0, -1, NUMERR), (1e300, 0, 0, NUMERR), (-1e300, 0, 0, NUMERR),
    ((TEXT, 5), 0, 0, VALUE), (0, (TEXT, 5), 0, VALUE), (0, 0, (TEXT, 5), VALUE),
    ((ERR, 7), (ERR, 2), 0, 7), (1, (ERR, 2), (ERR, 7), 2), (1, 0, (ERR, 4), 4),
    (32768, (ERR, 2), 0, 2), (32768, 0, (TEXT, 1), VALUE)])
def test_time_errors(h, m, s, err):
    assert result(TM, h, m, s) == (ERR, err)
