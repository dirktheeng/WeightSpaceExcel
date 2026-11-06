"""DATEVALUE, TIMEVALUE and text-to-date coercion of date arguments through the ABI entry
(dt_abi 351 -> dt_coer 358 -> core), black box. Expected values stated by hand (2000-01-01 = 36526)."""
import abibb
from abibb import result, key

abibb.FID.update(DATEVALUE=114, TIMEVALUE=468)
V = (4, 3)
H1, H2 = 0x302100, 0x302200


def s(text, addr):
    """Memory words of a text-heap string at addr (length, refcount, packed code units)."""
    m = {addr: len(text), addr + 1: 1}
    for k in range(0, len(text), 3):
        m[addr + 2 + k // 3] = sum(ord(ch) * 2 ** (16 * j) for j, ch in enumerate(text[k:k + 3]))
    return m


def test_datevalue_timevalue():
    assert result("DATEVALUE", (2, H1), mem=s("1/2/2000", H1)) == (1, 36527.0)
    assert result("TIMEVALUE", (2, H1), mem=s("6:00 PM", H1)) == (1, 0.75)
    assert result("DATEVALUE", (2, H1), mem=s("1/2/2000 18:00", H1)) == (1, 36527.0)
    assert result("TIMEVALUE", (2, H1), mem=s("1/2/2000 18:00", H1)) == (1, 0.75)
    assert result("DATEVALUE", (2, H1), mem=s("2/30/2000", H1)) == V
    assert result("DATEVALUE", 36527) == V            # a number is not date text
    assert result("DATEVALUE", (4, 7)) == (4, 7)
    assert result("DATEVALUE") == V                    # argument count
    assert result("DATEVALUE", (2, H1), (2, H1), mem=s("1/2/2000", H1)) == V


def test_datevalue_of_referenced_text():
    cells = [((0, 0, 0), (2, H1))]
    assert result("DATEVALUE", (9, key(0, 0, 0)), cells=cells, mem=s("Jan 2, 2000", H1)) == (1, 36527.0)
    assert result("YEAR", (9, key(0, 0, 0)), cells=cells, mem=s("Jan 2, 2000", H1)) == (1, 2000.0)


def test_text_coercion_of_date_arguments():
    assert result("YEAR", (2, H1), mem=s("1/2/2000", H1)) == (1, 2000.0)
    assert result("DAY", (2, H1), mem=s("2000-01-02", H1)) == (1, 2.0)
    assert result("HOUR", (2, H1), mem=s("1/2/2000 18:30", H1)) == (1, 18.0)
    assert result("YEAR", (2, H1), mem=s("36527", H1)) == (1, 2000.0)
    assert result("YEAR", (2, H1), mem=s("hello", H1)) == V
    m = s("1/3/2000", H1)
    m.update(s("1/1/2000", H2))
    assert result("DAYS", (2, H1), (2, H2), mem=m) == (1, 2.0)
    assert result("DAYS", (2, H1), 36526, mem=m) == (1, 2.0)
    assert result("DAYS", 36528, (2, H2), mem=m) == (1, 2.0)
    assert result("EDATE", (2, H2), 1, mem=m) == (1, 36557.0)       # 2000-02-01
    assert result("DATE", (2, H1), 1, 1, mem=s("2000", H1)) == (1, 36526.0)


def test_datedif_unit_stays_text():
    m = s("1/1/2000", H1)
    m.update(s("M", H2))
    assert result("DATEDIF", (2, H1), 36617, (2, H2), mem=m) == (1, 3.0)   # 2000-04-01 is 36617
