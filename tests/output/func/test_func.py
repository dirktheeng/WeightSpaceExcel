"""End-to-end function tests through the full application (boot, keystrokes, recalculation).

Cases: tests/output/func/cases.yaml (this suite) and the Stage 1 SUM cases. Expected values are
Excel's documented results, typed in the yaml files. Black box: runs the manifest, decodes cells.
"""
import os
import sys

import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sumrun  # noqa: E402

FUNC_CASES_PATH = os.path.join(HERE, "cases.yaml")
with open(FUNC_CASES_PATH) as _f:
    FUNC_CASES = yaml.safe_load(_f)["cases"]
ALL = FUNC_CASES + sumrun.SUM_CASES


@pytest.mark.parametrize("case", ALL, ids=[c["id"] for c in ALL])
def test_case(case):
    errs = sumrun.check(case, sumrun.run_case(case))
    assert not errs, errs
