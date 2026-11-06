"""Stage 1 black-box output tests (docs/RULES.md rule 2, permitted test code).

Feeds cell inputs to the engine through the harness and compares evaluated values
with expected values written in stage1/cases.yaml. This file never opens, reads or
inspects weight files, and contains no application logic: it computes no expected
values and suggests no fixes.

Assumed harness entry point (to be confirmed against harness/ once it exists):
    harness.run_workbook(cells: dict[str, str], edits: list[dict[str, str]] | None = None) -> dict
returning {address: value} where a value is a Python number, str, bool,
{"error": "#X"}, or {"blank": True}, plus optional keys
"__circular__": list of addresses and "__rejected__": list of addresses.
"""
import math
from pathlib import Path

import pytest
import yaml

CASES = yaml.safe_load((Path(__file__).parent / "stage1" / "cases.yaml").read_text())["cases"]
REL_TOL = 1e-12  # docs/ACCEPTANCE.md: reals within 1 part in 10^12 relative

try:
    import harness  # noqa: F401
    ENGINE = hasattr(harness, "run_workbook")
except ImportError:
    ENGINE = False


def _same(actual, expected):
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(actual) is bool and actual is expected
    if isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)):
            return False
        if expected == 0:
            return abs(actual) <= 1e-300 or actual == 0
        return math.isclose(actual, expected, rel_tol=REL_TOL, abs_tol=0.0)
    return actual == expected  # text, error dicts and blank dicts match exactly


@pytest.mark.xfail(not ENGINE, reason="Stage 1 engine not built yet", strict=False)
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case(case):
    import harness
    out = harness.run_workbook(dict(case["cells"]), edits=case.get("edits"))
    for addr, exp in case["expect"].items():
        got = out.get(addr, {"blank": True})
        assert _same(got, exp), f"{case['id']} {addr}: expected {exp!r}, got {got!r}"
    if "circular" in case:
        assert sorted(out.get("__circular__", [])) == sorted(case["circular"])
    if "rejected" in case:
        assert sorted(out.get("__rejected__", [])) == sorted(case["rejected"])
