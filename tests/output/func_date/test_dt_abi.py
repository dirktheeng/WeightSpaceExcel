"""Date functions through the function ABI (encodings/functions.md): dt_abi (351) entered as from
FN_CALL with n in N0, T2 = 64 + fid, arguments on the operand stack and the last in B; the run ends
at FN_RET (replaced by HALT_OK here). abibb.result also checks the ABI preserve set on every call.
Expected values stated by hand (45658 = 2025-01-01, 45292 = 2024-01-01)."""
import pytest
from abibb import key
import abibb

NUM, TEXT, ERR, MISSING = 1, 2, 4, 8
H = 0x302000 + 64


@pytest.mark.parametrize("name,args,want", [
    ("YEAR", (45658,), 2025), ("MONTH", (45351,), 2), ("DAY", (45351,), 29), ("HOUR", (0.75,), 18),
    ("MINUTE", (0.521527777777778,), 31), ("SECOND", (0.6044560185185185,), 25),
    ("WEEKDAY", (45658,), 4), ("WEEKDAY", (45658, 2), 3), ("WEEKNUM", (45662,), 2),
    ("WEEKNUM", (45662, 2), 1), ("ISOWEEKNUM", (45657,), 1),
    ("DATE", (2025, 1, 1), 45658), ("DATE", (2024, 14, 1), 45689), ("TIME", (12, 0, 0), 0.5),
    ("EDATE", (45688, 1), 45716), ("EOMONTH", (45658, -1), 45657),
    ("DAYS", (45658, 45292), 366), ("DAYS360", (45292, 45658), 360), ("DAYS360", (45351, 45382, (3, 1)), 31),
    ("YEARFRAC", (45292, 45474), 0.5), ("YEARFRAC", (45292, 45658, 1), 1.0),
    ("DATE", (2024, (MISSING, 0), 1), 45261)])        # DATE(2024,,1): month 0 = 2023-12-01
def test_values(name, args, want):
    assert abibb.result(name, *args) == (NUM, want)


def test_datedif_text_unit():
    unit = {H: 1, H + 2: 77}                            # "M"
    assert abibb.result("DATEDIF", 44957, 46143, (TEXT, H), mem=unit) == (NUM, 39)
    unit = {H: 2, H + 2: 89 + 68 * 65536}              # "YD"
    assert abibb.result("DATEDIF", 44957, 46143, (TEXT, H), mem=unit) == (NUM, 90)
    assert abibb.result("DATEDIF", 44957, 46143, (TEXT, H)) == (ERR, 6)   # empty string


def test_references_are_dereferenced():
    c = [((0, 0, 0), (NUM, 2024.0)), ((0, 1, 0), (NUM, 2.0)), ((0, 2, 3), (NUM, 29.0))]
    assert abibb.result("DATE", (9, key(0, 0, 0)), (9, key(0, 1, 0)), (9, key(0, 2, 3)), cells=c) == (NUM, 45351)
    assert abibb.result("YEAR", (9, key(0, 4, 2)), cells=[((0, 4, 2), (NUM, 45658.0))]) == (NUM, 2025)
    assert abibb.result("YEAR", (9, key(0, 9, 9))) == (NUM, 1900)          # empty cell is 0
    assert abibb.result("DAYS", (9, key(1, 3, 3)), 45292, cells=[((1, 3, 3), (NUM, 45658.0))]) == (NUM, 366)
    assert abibb.result("WEEKDAY", 45658, (9, key(0, 7, 1)), cells=[((0, 7, 1), (NUM, 2.0))]) == (NUM, 3)
    assert abibb.result("YEAR", (9, key(0, 5, 5)), cells=[((0, 5, 5), (ERR, 7))]) == (ERR, 7)


def test_now_today_and_zero_arguments():
    out, before = abibb.call("NOW")
    assert int(out[13]) == NUM and 45658 < out[14] < 73051
    assert (out[15], out[16]) == (1, 77.0)             # n = 0: the previous top of stack is left alone
    tag, d = abibb.result("TODAY")
    assert tag == NUM and d == int(d)


def test_argument_count_errors():
    assert abibb.result("YEAR") == (ERR, 3)
    assert abibb.result("YEAR", 1, 2) == (ERR, 3)
    assert abibb.result("DATE", 2025, 1) == (ERR, 3)
    assert abibb.result("NOW", 1) == (ERR, 3)
    assert abibb.result("DAYS360", 1, 2, 3, 4) == (ERR, 3)
