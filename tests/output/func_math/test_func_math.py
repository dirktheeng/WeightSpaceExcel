"""Output tests for weights/func/math (func math agent). Black box: networks are loaded by
path, given a 65-word register input (encodings/control.md), run one step, and the result
register A is compared with values stated by hand from Excel's documented behaviour.
Weight files are never opened here."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402

MATH = os.path.join(ROOT, "weights", "func", "math")
LR_IN, LP_IN, A_TAG, A_PAY, T0_IN = 9, 10, 14, 15, 30
NUM, BLANK, TEXT, BOOL, ERR = 1, 0, 2, 3, 4
ABS, SIGN, INT, TRUNC, PI, EVEN, ODD, DEGREES, RADIANS = range(9)


def call(name, sel, tag, pay):
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[LR_IN], x[LP_IN] = 77.0, 5.0
    x[A_TAG], x[A_PAY], x[T0_IN] = float(tag), float(pay), float(sel)
    # the network returns to LR (not a halt), so take the single forward pass directly
    out = list(Harness([os.path.join(MATH, name + ".wt")]).nets[0].forward(np.array(x)))
    assert len(out) == 64
    assert list(out[:8]) == [77, 0, 0, 0, 0, 0, 0, 5]
    assert out[12] == 0
    for w in list(range(8, 12)) + list(range(15, 64)):
        assert out[w] == x[w + 1], w
    return (float(out[13]), float(out[14]))


def close15(a, b):
    return a == b or abs(a - b) <= 5e-15 * max(abs(a), abs(b))


U = [  # (sel, tag, pay, expected (tag, pay))
    (ABS, NUM, -3.5, (1, 3.5)), (ABS, NUM, 2, (1, 2)), (ABS, NUM, 0, (1, 0)),
    (ABS, NUM, -1e308, (1, 1e308)), (ABS, BOOL, 1, (1, 1)), (ABS, BLANK, 0, (1, 0)),
    (ABS, TEXT, 12345, (4, 3)), (ABS, ERR, 7, (4, 7)), (ABS, ERR, 2, (4, 2)),
    (SIGN, NUM, -0.001, (1, -1)), (SIGN, NUM, 0, (1, 0)), (SIGN, NUM, 5e-324, (1, 1)),
    (SIGN, NUM, 42, (1, 1)),
    (INT, NUM, 8.9, (1, 8)), (INT, NUM, -8.9, (1, -9)), (INT, NUM, -2.5, (1, -3)),
    (INT, NUM, 2.5, (1, 2)), (INT, NUM, -3, (1, -3)), (INT, NUM, 0.5, (1, 0)),
    (INT, NUM, -0.0000001, (1, -1)), (INT, NUM, 1e20, (1, 1e20)), (INT, NUM, -1e300, (1, -1e300)),
    (INT, NUM, 123456789012345.5, (1, 123456789012345)),
    (TRUNC, NUM, 8.9, (1, 8)), (TRUNC, NUM, -8.9, (1, -8)), (TRUNC, NUM, -0.5, (1, 0)),
    (TRUNC, NUM, -2.5, (1, -2)), (TRUNC, NUM, 1e20, (1, 1e20)), (TRUNC, BOOL, 1, (1, 1)),
    (PI, BLANK, 0, (1, 3.141592653589793)), (PI, ERR, 7, (1, 3.141592653589793)),
    (EVEN, NUM, 1.5, (1, 2)), (EVEN, NUM, 3, (1, 4)), (EVEN, NUM, 2, (1, 2)),
    (EVEN, NUM, -1, (1, -2)), (EVEN, NUM, 0, (1, 0)), (EVEN, NUM, -2.0001, (1, -4)),
    (ODD, NUM, 1.5, (1, 3)), (ODD, NUM, 3, (1, 3)), (ODD, NUM, 2, (1, 3)),
    (ODD, NUM, -1, (1, -1)), (ODD, NUM, -2, (1, -3)), (ODD, NUM, 0, (1, 1)),
    (ODD, NUM, -1.5, (1, -3)), (ODD, NUM, 0.0001, (1, 1)),
    (DEGREES, NUM, 3.141592653589793, (1, 180)), (DEGREES, NUM, 1, (1, 57.2957795130823)),
    (DEGREES, NUM, 1e308, (4, 6)), (DEGREES, TEXT, 9, (4, 3)),
    (RADIANS, NUM, 270, (1, 4.71238898038469)), (RADIANS, NUM, 180, (1, 3.141592653589793)),
    (RADIANS, NUM, -45, (1, -0.785398163397448)),
]


@pytest.mark.parametrize("sel,tag,pay,want", U)
def test_unary(sel, tag, pay, want):
    t, p = call("fm_unary", sel, tag, pay)
    assert t == want[0] and close15(p, want[1]), (t, p)
