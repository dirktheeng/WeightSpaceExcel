"""End-to-end math function cases through the whole application (keystrokes in, cell values out),
via tests/output/blackbox.py. Black box. Each case is skipped while the function's name still
evaluates to #NAME? (FUNC_TABLE entry not yet pointing at fm_ent, id 277)."""
import math
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402
from harness.harness import Harness  # noqa: E402

CASES = [  # (cells, cell to read, expected), expected values hand-stated from Excel
    ({"A1": "-3", "B1": "=ABS(A1)"}, "B1", 3),
    ({"A1": "'16", "B1": "=SQRT(A1)"}, "B1", 4),               # text in a referenced cell coerces
    ({"B1": '=SQRT("16")'}, "B1", 4),                          # direct text coerces
    ({"B1": '=SQRT("x")'}, "B1", {"error": "#VALUE!"}),
    ({"A1": "2.675", "B1": "=ROUND(A1,2)"}, "B1", 2.68),
    ({"A1": "8", "A2": "2", "B1": "=LOG(A1,A2)"}, "B1", 3),
    ({"B1": "=MOD(-3,2)+INT(-2.5)"}, "B1", -2),
    ({"B1": "=DEGREES(ATAN2(1,1))"}, "B1", 45),
    ({"B1": "=COMBIN(8,2)*FACT(3)"}, "B1", 168),
    ({"B1": "=POWER(2,10)"}, "B1", 1024),
    ({"B1": "=SIN(PI()/2)"}, "B1", 1),
    ({"B1": "=GCD(24,36)"}, "B1", 12),
    ({"B1": "=SQRT(-1)"}, "B1", {"error": "#NUM!"}),
    ({"A1": "=1/0", "B1": "=ABS(A1)"}, "B1", {"error": "#DIV/0!"}),
    ({"B1": "=ABS(C9)"}, "B1", 0),                              # blank cell
]


@pytest.mark.parametrize("cells,cell,want", CASES)
def test_e2e(cells, cell, want):
    h = Harness(bb.manifest_paths(), events=bb.script(cells))
    h.run(0, np.zeros(65), max_steps=5_000_000)
    got = bb.value(h, cell)
    if got == {"error": "#NAME?"}:
        pytest.skip("function not mapped to fm_ent (277) in FUNC_TABLE yet")
    assert bb.peek(h, bb.FAULT) == 0
    if isinstance(want, (int, float)):
        assert isinstance(got, float) and math.isclose(got, want, rel_tol=5e-15, abs_tol=0), got
    else:
        assert got == want
