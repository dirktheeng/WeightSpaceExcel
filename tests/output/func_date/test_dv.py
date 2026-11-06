"""DATEVALUE / TIMEVALUE / date text coercion core (dv_ent 354 .. dv_rest 357). Black box.
Expected serials are stated by hand (Excel 1900 system, en-US forms): 2000-01-01 = 36526,
1930-01-01 = 10959 (30 * 365 + 8 leap days counting Excel's 1900-02-29, + 1), 1999-01-01 = 36161."""
import pytest

from dvbb import run, DV, TV, CO

V = (4, 3)
DATES = [
    ("1/1/1900", 1), ("2/29/1900", 60), ("3/1/1900", 61), ("12/31/9999", 2958465),
    ("1/1/2000", 36526), ("1/2/2000", 36527), ("01/02/2000", 36527), ("2000-01-02", 36527),
    ("2000/1/2", 36527), ("1-2-2000", 36527), ("2-Jan-2000", 36527), ("2 Jan 2000", 36527),
    ("Jan 2, 2000", 36527), ("January 2, 2000", 36527), ("jan 2 2000", 36527), ("  1/2/2000  ", 36527),
    ("1/2/00", 36527), ("1/2/99", 36162), ("1/2/30", 10960), ("2/29/2000", 36585),
    ("Jan 2000", 36526), ("Jan-2000", 36526), ("1/2000", 36526), ("1/2/2000 6:00", 36527),
    ("Feb 3 2000", 36559), ("3-Mar-2000", 36588), ("Dec 31, 1999", 36525),
]
BAD_DATES = ["2/30/2000", "2/29/2001", "4/31/2000", "13/1/2000", "0/1/2000", "1/0/2000", "1/2/1899",
             "hello", "", "   ", "1/2", "Jan", "1.2.2000", "1/2/2000/3", "Foo 2 2000", "6:00",
             "36527", "1/2/10000"]
TIMES = [
    ("6:00", 0.25), ("18:00", 0.75), ("6:00 PM", 0.75), ("6:00 am", 0.25), ("12:00 AM", 0.0),
    ("12:30 PM", 0.5208333333333334), ("8:00", 1 / 3), ("3 PM", 0.625), ("13:45:30", 49530 / 86400),
    ("0:00", 0.0), ("25:00", 1 / 24), ("1/2/2000", 0.0), ("1/2/2000 6:00", 0.25), ("6:00:00 PM", 0.75),
    ("Jan 2 2000 3 PM", 0.625),
]
BAD_TIMES = ["1:60", "1:00:60", "13:00 PM", "PM", "6:", "x6:00", "", "5", "6:00 PM PM"]


@pytest.mark.parametrize("s,serial", DATES)
def test_datevalue(s, serial):
    assert run(s, DV) == (1, float(serial))


@pytest.mark.parametrize("s", BAD_DATES)
def test_datevalue_rejects(s):
    assert run(s, DV) == V


@pytest.mark.parametrize("s,frac", TIMES)
def test_timevalue(s, frac):
    t, p = run(s, TV)
    assert t == 1 and abs(p - frac) <= 1e-15


@pytest.mark.parametrize("s", BAD_TIMES)
def test_timevalue_rejects(s):
    assert run(s, TV) == V


@pytest.mark.parametrize("s,val", [("1/2/2000", 36527), ("36527", 36527), ("1/2/2000 6:00", 36527.25),
                                   ("6:00", 0.25), ("0", 0), ("2-Jan-2000 18:00", 36527.75)])
def test_coercion(s, val):
    assert run(s, CO) == (1, float(val))


@pytest.mark.parametrize("s", ["hello", "", "1/2", "36527.5", "1/32/2000"])
def test_coercion_rejects(s):
    assert run(s, CO) == V


def test_non_text_arguments():
    assert run((1, 5.0), DV) == V
    assert run((3, 1.0), TV) == V
    assert run((4, 7.0), DV) == (4, 7)
    assert run((4, 2.0), CO) == (4, 2)
    assert run((1, 1e300), CO) == V


def test_too_long():
    assert run("1/2/2000" + " " * 33, DV) == V
    assert run("1/2/2000" + " " * 32, DV) == (1, 36527.0)


def test_step_count():
    (_, n) = run("1/2/2000", CO, steps=True)
    assert n == 19      # dv_ent 1, length 2, 9 character steps, dv_fin 3 + dt_time 1 + dt_date 1, dv_rest 1 = 18 + HALT
