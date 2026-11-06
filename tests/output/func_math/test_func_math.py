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
    x[LR_IN], x[LP_IN] = 3.0, 5.0
    x[A_TAG], x[A_PAY], x[T0_IN] = float(tag), float(pay), float(sel)
    out = run_single(name, x)
    for w in list(range(8, 12)) + list(range(15, 64)):
        assert out[w] == x[w + 1], w
    return (float(out[13]), float(out[14]))


_single = {}


def run_single(name, x):
    """Run a one-step network at id 4 through Harness.run; it returns to LR = 3 (HALT_OK, which
    copies words 7..63 and halts). Black box: only the run's output vector and trace are read."""
    if name not in _single:
        paths = [os.path.join(ROOT, "weights", "kernel", "trap.wt")] * 5
        paths[3] = os.path.join(ROOT, "weights", "kernel", "halt_ok.wt")
        paths[4] = os.path.join(MATH, name + ".wt")
        _single[name] = Harness(paths)
    h = _single[name]
    h.trace = []
    out = list(h.run(4, np.array(x), max_steps=2))
    route = [ln.split()[3] for ln in h.trace if ln.startswith("step")]
    assert route == ["4", "3"], route
    assert len(out) == 64 and out[7] == 5 and out[12] == 0
    return out


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


B_TAG, B_PAY = 16, 17
RND, RUP, RDN = 0, 1, 2


def call2(name, sel, a, b):
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[LR_IN], x[LP_IN] = 3.0, 5.0
    x[A_TAG], x[A_PAY] = float(a[0]), float(a[1])
    x[B_TAG], x[B_PAY] = float(b[0]), float(b[1])
    x[T0_IN] = float(sel)
    out = run_single(name, x)
    for w in list(range(8, 12)) + list(range(15, 64)):
        assert out[w] == x[w + 1], w
    return (float(out[13]), float(out[14]))


def n(v):
    return (NUM, v)


R = [  # Excel documentation examples and hand-stated values
    (RND, n(2.15), n(1), (1, 2.2)), (RND, n(2.149), n(1), (1, 2.1)),
    (RND, n(-1.475), n(2), (1, -1.48)), (RND, n(21.5), n(-1), (1, 20)),
    (RND, n(626.3), n(-3), (1, 1000)), (RND, n(1.98), n(-1), (1, 0)),
    (RND, n(-50.55), n(-2), (1, -100)), (RND, n(2.675), n(2), (1, 2.68)),
    (RND, n(2.5), n(0), (1, 3)), (RND, n(-2.5), n(0), (1, -3)), (RND, n(0.5), n(0), (1, 1)),
    (RND, n(1e20), n(2), (1, 1e20)), (RND, n(1e300), n(15), (1, 1e300)),
    (RND, n(5.55), n(1.9), (1, 5.6)), (RND, n(5.55), n(-0.9), (1, 6)),
    (RND, n(1234.5678), n(-2), (1, 1200)), (RND, n(0.1 + 0.2), n(15), (1, 0.3)),
    (RND, n(123456.789), n(20), (1, 123456.789)),
    (RUP, n(3.2), n(0), (1, 4)), (RUP, n(76.9), n(0), (1, 77)),
    (RUP, n(3.14159), n(3), (1, 3.142)), (RUP, n(-3.14159), n(1), (1, -3.2)),
    (RUP, n(31415.92654), n(-2), (1, 31500)), (RUP, n(3), n(0), (1, 3)),
    (RUP, n(0.1 * 3), n(1), (1, 0.3)),
    (RDN, n(3.2), n(0), (1, 3)), (RDN, n(76.9), n(0), (1, 76)),
    (RDN, n(3.14159), n(3), (1, 3.141)), (RDN, n(-3.14159), n(1), (1, -3.1)),
    (RDN, n(31415.92654), n(-2), (1, 31400)), (RDN, n(4.35 * 100), n(0), (1, 435)),
    (RND, (BOOL, 1), n(0), (1, 1)), (RND, (BLANK, 0), n(2), (1, 0)), (RND, n(7.25), (BLANK, 0), (1, 7)),
    (RND, (ERR, 7), (ERR, 2), (4, 7)), (RND, n(1), (ERR, 2), (4, 2)),
    (RND, (TEXT, 99), (ERR, 2), (4, 3)), (RND, n(1), (TEXT, 99), (4, 3)),
    (RND, (ERR, 6), (TEXT, 99), (4, 6)),
]


@pytest.mark.parametrize("sel,a,b,want", R)
def test_round(sel, a, b, want):
    t, p = call2("fm_round", sel, a, b)
    assert t == want[0] and close15(p, want[1]), (t, p)


C_TAG, C_PAY = 18, 19
MISS = 8
QUO, MOD, MRD, CEIL, FLR, CEILP, FLRP, CEILM, FLRM = range(9)
KERNEL = os.path.join(ROOT, "weights", "kernel")
_chain = {}


def chain():
    """Network list with fm_dv0 at 266, fm_dv1 at 267, HALT_OK at 3, TRAP elsewhere."""
    if "h" not in _chain:
        paths = [os.path.join(KERNEL, "trap.wt")] * 268
        paths[3] = os.path.join(KERNEL, "halt_ok.wt")
        paths[266] = os.path.join(MATH, "fm_dv0.wt")
        paths[267] = os.path.join(MATH, "fm_dv1.wt")
        _chain["h"] = Harness(paths)
    return _chain["h"]


def call3(sel, a, b, c=(MISS, 0)):
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[LR_IN], x[LP_IN] = 3.0, 5.0
    x[A_TAG], x[A_PAY] = float(a[0]), float(a[1])
    x[B_TAG], x[B_PAY] = float(b[0]), float(b[1])
    x[C_TAG], x[C_PAY] = float(c[0]), float(c[1])
    x[T0_IN] = float(sel)
    trace = []
    h = chain()
    h.trace = trace
    out = h.run(266, np.array(x), max_steps=3)
    route = [ln.split()[3] for ln in trace if ln.startswith("step")]
    assert route == ["266", "267", "3"], route
    assert out[7] == 5 and out[12] == 0
    return (float(out[13]), float(out[14]))


D = [  # Excel documentation examples and hand-stated values
    (QUO, n(5), n(2), (1, 2)), (QUO, n(4.5), n(3.1), (1, 1)), (QUO, n(-10), n(3), (1, -3)),
    (QUO, n(5), n(0), (4, 2)), (QUO, n(1e308), n(1e-10), (4, 6)), (QUO, n(7), (BLANK, 0), (4, 2)),
    (MOD, n(3), n(2), (1, 1)), (MOD, n(-3), n(2), (1, 1)), (MOD, n(3), n(-2), (1, -1)),
    (MOD, n(-3), n(-2), (1, -1)), (MOD, n(5.5), n(2), (1, 1.5)), (MOD, n(3), n(0), (4, 2)),
    (MOD, n(10), n(3), (1, 1)), (MOD, n(1e300), n(3), (4, 6)), (MOD, n(-7.5), n(2), (1, 0.5)),
    (MRD, n(10), n(3), (1, 9)), (MRD, n(-10), n(-3), (1, -9)), (MRD, n(1.3), n(0.2), (1, 1.4)),
    (MRD, n(5), n(-2), (4, 6)), (MRD, n(5), n(0), (1, 0)), (MRD, n(7.5), n(5), (1, 10)),
    (MRD, n(0), n(-2), (1, 0)),
    (CEIL, n(2.5), n(1), (1, 3)), (CEIL, n(-2.5), n(-2), (1, -4)), (CEIL, n(-2.5), n(2), (1, -2)),
    (CEIL, n(1.5), n(0.1), (1, 1.5)), (CEIL, n(0.234), n(0.01), (1, 0.24)),
    (CEIL, n(2.5), n(-2), (4, 6)), (CEIL, n(4.42), n(0.05), (1, 4.45)),
    (FLR, n(3.7), n(2), (1, 2)), (FLR, n(-2.5), n(-2), (1, -2)), (FLR, n(2.5), n(-2), (4, 6)),
    (FLR, n(1.58), n(0.1), (1, 1.5)), (FLR, n(0.234), n(0.01), (1, 0.23)),
    (FLR, n(-2.5), n(2), (1, -4)), (FLR, n(3), n(0), (4, 2)),
    (CEILP, n(4.3), (MISS, 0), (1, 5)), (CEILP, n(-4.3), (MISS, 0), (1, -4)),
    (CEILP, n(4.3), n(2), (1, 6)), (CEILP, n(4.3), n(-2), (1, 6)), (CEILP, n(-4.3), n(2), (1, -4)),
    (CEILP, n(-4.3), n(-2), (1, -4)), (CEILP, n(4.3), n(0), (1, 0)),
    (FLRP, n(-3.2), n(-1), (1, -4)), (FLRP, n(3.2), n(1), (1, 3)), (FLRP, n(-3.2), n(1), (1, -4)),
    (FLRP, n(3.2), n(-1), (1, 3)), (FLRP, n(3.2), (MISS, 0), (1, 3)),
    (CEILM, n(24.3), n(5), (1, 25)), (CEILM, n(6.7), (MISS, 0), (1, 7)),
    (CEILM, n(-8.1), n(2), (1, -8)), (CEILM, n(-5.5), n(2), n(-1), (1, -6)),
    (CEILM, n(5.5), n(2), n(-1), (1, 6)),
    (FLRM, n(24.3), n(5), (1, 20)), (FLRM, n(6.7), (MISS, 0), (1, 6)),
    (FLRM, n(-8.1), n(2), (1, -10)), (FLRM, n(-5.5), n(2), n(-1), (1, -4)),
    (QUO, (ERR, 7), (ERR, 2), (4, 7)), (MOD, n(1), (ERR, 5), (4, 5)), (MOD, (TEXT, 9), n(2), (4, 3)),
    (MOD, n(1), (TEXT, 9), (4, 3)), (CEILM, n(1), n(1), (ERR, 7), (4, 7)),
    (CEILM, n(1), n(1), (TEXT, 9), (4, 3)), (FLR, (BOOL, 1), n(1), (1, 1)),
    (CEILM, (ERR, 2), n(1), (ERR, 7), (4, 2)), (MOD, (TEXT, 9), (ERR, 2), (4, 3)),
]


@pytest.mark.parametrize("case", D)
def test_divfam(case):
    if len(case) == 4:
        sel, a, b, want = case
        t, p = call3(sel, a, b)
    else:
        sel, a, b, c, want = case
        t, p = call3(sel, a, b, c)
    assert t == want[0] and close15(p, want[1]), (t, p)


EXP, LN, LOG10, POWER, SQRT, SQRTPI = range(6)
_pchain = {}


def pchain():
    if "h" not in _pchain:
        paths = [os.path.join(KERNEL, "trap.wt")] * 270
        paths[3] = os.path.join(KERNEL, "halt_ok.wt")
        paths[268] = os.path.join(MATH, "fm_pw0.wt")
        paths[269] = os.path.join(MATH, "fm_pw1.wt")
        _pchain["h"] = Harness(paths)
    return _pchain["h"]


def callp(sel, a, b=(MISS, 0)):
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[LR_IN], x[LP_IN] = 3.0, 5.0
    x[A_TAG], x[A_PAY] = float(a[0]), float(a[1])
    x[B_TAG], x[B_PAY] = float(b[0]), float(b[1])
    x[T0_IN] = float(sel)
    trace = []
    h = pchain()
    h.trace = trace
    out = h.run(268, np.array(x), max_steps=3)
    route = [ln.split()[3] for ln in trace if ln.startswith("step")]
    assert route == ["268", "269", "3"], route
    assert out[7] == 5 and out[12] == 0
    return (float(out[13]), float(out[14]))


P = [  # hand-stated: Excel documentation examples and standard constants to 15+ digits
    (EXP, n(1), (1, 2.718281828459045)), (EXP, n(2), (1, 7.38905609893065)),
    (EXP, n(0), (1, 1)), (EXP, n(-1), (1, 0.36787944117144233)),
    (EXP, n(709), (1, 8.218407461554972e307)), (EXP, n(710), (4, 6)), (EXP, n(-800), (1, 0)),
    (EXP, n(10), (1, 22026.465794806718)), (EXP, n(-20), (1, 2.061153622438558e-09)),
    (LN, n(86), (1, 4.454347296253507)), (LN, n(2.7182818), (1, 0.9999999895305024)),
    (LN, n(1), (1, 0)), (LN, n(10), (1, 2.302585092994046)), (LN, n(0), (4, 6)),
    (LN, n(-1), (4, 6)), (LN, n(1e300), (1, 690.7755278982137)),
    (LOG10, n(86), (1, 1.934498451243568)), (LOG10, n(10), (1, 1)), (LOG10, n(1e5), (1, 5)),
    (LOG10, n(1000), (1, 3)), (LOG10, n(0.001), (1, -3)), (LOG10, n(2), (1, 0.3010299956639812)),
    (LOG10, n(0), (4, 6)),
    (POWER, n(5), n(2), (1, 25)), (POWER, n(98.6), n(3.2), (1, 2401077.2220695773)),
    (POWER, n(4), n(5 / 4), (1, 5.656854249492381)), (POWER, n(2), n(10), (1, 1024)),
    (POWER, n(2), n(0.5), (1, 1.4142135623730951)), (POWER, n(-2), n(3), (1, -8)),
    (POWER, n(-2), n(2), (1, 4)), (POWER, n(-8), n(1 / 3), (4, 6)), (POWER, n(0), n(0), (4, 6)),
    (POWER, n(0), n(-1), (4, 2)), (POWER, n(0), n(2), (1, 0)), (POWER, n(10), n(-2), (1, 0.01)),
    (POWER, n(10), n(309), (4, 6)), (POWER, n(9), n(0.5), (1, 3)),
    (SQRT, n(16), (1, 4)), (SQRT, n(-16), (4, 6)), (SQRT, n(2), (1, 1.4142135623730951)),
    (SQRT, n(0), (1, 0)), (SQRT, n(1e10), (1, 1e5)), (SQRT, n(0.25), (1, 0.5)),
    (SQRTPI, n(1), (1, 1.772453850905516)), (SQRTPI, n(2), (1, 2.5066282746310002)),
    (SQRTPI, n(-1), (4, 6)),
    (EXP, (ERR, 7), (4, 7)), (LN, (TEXT, 5), (4, 3)), (POWER, n(2), (ERR, 2), (4, 2)),
    (POWER, (TEXT, 5), (ERR, 2), (4, 3)), (EXP, (BOOL, 1), (1, 2.718281828459045)),
    (POWER, n(2), (BLANK, 0), (1, 1)),
]


@pytest.mark.parametrize("case", P)
def test_powfam(case):
    if len(case) == 3:
        sel, a, want = case
        t, p = callp(sel, a)
    else:
        sel, a, b, want = case
        t, p = callp(sel, a, b)
    assert t == want[0] and close15(p, want[1]), (t, p)


SIN, COS, TAN, SEC, CSC, COT = range(6)
_tchain = {}


def tchain():
    if "h" not in _tchain:
        paths = [os.path.join(KERNEL, "trap.wt")] * 271
        paths[3] = os.path.join(KERNEL, "halt_ok.wt")
        paths[267] = os.path.join(MATH, "fm_dv1.wt")
        paths[270] = os.path.join(MATH, "fm_trig.wt")
        _tchain["h"] = Harness(paths)
    return _tchain["h"]


def callt(sel, a):
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[LR_IN], x[LP_IN] = 3.0, 5.0
    x[A_TAG], x[A_PAY] = float(a[0]), float(a[1])
    x[T0_IN] = float(sel)
    trace = []
    h = tchain()
    h.trace = trace
    out = h.run(270, np.array(x), max_steps=3)
    route = [ln.split()[3] for ln in trace if ln.startswith("step")]
    # SIN, COS and errors return directly; TAN, SEC, CSC, COT divide in fm_dv1 (267)
    assert route in (["270", "3"], ["270", "267", "3"]), route
    if sel in (TAN, SEC, CSC, COT) and out[13] == 1:
        assert route[1] == "267"
    assert out[7] == 5 and out[12] == 0
    return (float(out[13]), float(out[14]))


PI_D = 3.141592653589793
TR = [  # hand-stated: Excel documentation examples and standard values
    (SIN, n(PI_D), (1, 1.2246467991473532e-16)), (SIN, n(PI_D / 2), (1, 1)),
    (SIN, n(30 * PI_D / 180), (1, 0.5)), (SIN, n(1), (1, 0.8414709848078965)),
    (SIN, n(-1), (1, -0.8414709848078965)), (SIN, n(10), (1, -0.5440211108893698)),
    (SIN, n(1000), (1, 0.8268795405320025)), (SIN, n(0), (1, 0)), (SIN, n(1e-20), (1, 1e-20)),
    (SIN, n(134217728), (4, 6)), (SIN, n(-134217728), (4, 6)),
    (COS, n(1.047), (1, 0.5001710745970701)), (COS, n(60 * PI_D / 180), (1, 0.5)),
    (COS, n(1), (1, 0.5403023058681398)), (COS, n(3), (1, -0.9899924966004454)),
    (COS, n(0), (1, 1)), (COS, n(PI_D), (1, -1)),
    (TAN, n(0.785), (1, 0.9992039901050428)), (TAN, n(45 * PI_D / 180), (1, 1)),
    (TAN, n(1), (1, 1.5574077246549023)), (TAN, n(-2), (1, 2.185039863261519)),
    (SEC, n(1), (1, 1.8508157176809255)), (SEC, n(45 * PI_D / 180), (1, 1.414213562373095)),
    (CSC, n(1), (1, 1.1883951057781212)), (CSC, n(0), (4, 2)),
    (COT, n(1), (1, 0.6420926159343306)), (COT, n(0), (4, 2)), (COT, n(PI_D / 4), (1, 1)),
    (SIN, (ERR, 7), (4, 7)), (COS, (TEXT, 3), (4, 3)), (TAN, (ERR, 2), (4, 2)),
    (COS, (BOOL, 1), (1, 0.5403023058681398)), (SIN, (BLANK, 0), (1, 0)),
]


@pytest.mark.parametrize("sel,a,want", TR)
def test_trig(sel, a, want):
    t, p = callt(sel, a)
    assert t == want[0] and close15(p, want[1]), (t, p)


ATAN, ATAN2, ACOT, ASIN, ACOS = range(5)
_achain = {}


def achain():
    if "h" not in _achain:
        paths = [os.path.join(KERNEL, "trap.wt")] * 273
        paths[3] = os.path.join(KERNEL, "halt_ok.wt")
        for i, nm in ((267, "fm_dv1"), (268, "fm_pw0"), (269, "fm_pw1"), (271, "fm_at0"), (272, "fm_at1")):
            paths[i] = os.path.join(MATH, nm + ".wt")
        _achain["h"] = Harness(paths)
    return _achain["h"]


def calla(sel, a, b=(MISS, 0)):
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[8] = 0.0  # PC 0 on entry
    x[LR_IN], x[LP_IN] = 3.0, 5.0
    x[A_TAG], x[A_PAY] = float(a[0]), float(a[1])
    x[B_TAG], x[B_PAY] = float(b[0]), float(b[1])
    x[T0_IN] = float(sel)
    trace = []
    h = achain()
    h.trace = trace
    out = h.run(271, np.array(x), max_steps=8)
    route = [ln.split()[3] for ln in trace if ln.startswith("step")]
    assert route[0] == "271" and route[-1] == "3", route
    assert out[7] == 5 and out[12] == 0
    return (float(out[13]), float(out[14])), route


AT = [  # hand-stated: Excel documentation examples and standard values
    (ATAN, n(1), (1, 0.7853981633974483)), (ATAN, n(-1), (1, -0.7853981633974483)),
    (ATAN, n(0), (1, 0)), (ATAN, n(1e10), (1, 1.5707963266948965)), (ATAN, n(0.5), (1, 0.4636476090008061)),
    (ATAN, n(2), (1, 1.1071487177940904)), (ATAN, n(-0.3), (1, -0.2914567944778671)),
    (ATAN, n(1e-20), (1, 1e-20)),
    (ATAN2, n(1), n(1), (1, 0.7853981633974483)), (ATAN2, n(-1), n(-1), (1, -2.356194490192345)),
    (ATAN2, n(1), n(0), (1, 0)), (ATAN2, n(0), n(1), (1, 1.5707963267948966)),
    (ATAN2, n(-1), n(0), (1, 3.141592653589793)), (ATAN2, n(0), n(0), (4, 2)),
    (ATAN2, n(1), n(2), (1, 1.1071487177940904)), (ATAN2, n(-3), n(1), (1, 2.819842099193151)),
    (ATAN2, n(2), n(-5), (1, -1.1902899496825317)),
    (ACOT, n(2), (1, 0.4636476090008061)), (ACOT, n(-1), (1, 2.356194490192345)),
    (ACOT, n(0), (1, 1.5707963267948966)),
    (ASIN, n(-0.5), (1, -0.5235987755982989)), (ASIN, n(1), (1, 1.5707963267948966)),
    (ASIN, n(0.3), (1, 0.30469265401539753)), (ASIN, n(2), (4, 6)), (ASIN, n(0), (1, 0)),
    (ACOS, n(-0.5), (1, 2.0943951023931957)), (ACOS, n(1), (1, 0)), (ACOS, n(0.3), (1, 1.2661036727794992)),
    (ACOS, n(0), (1, 1.5707963267948966)), (ACOS, n(-1), (1, 3.141592653589793)), (ACOS, n(-1.5), (4, 6)),
    (ATAN, (ERR, 7), (4, 7)), (ATAN2, n(1), (TEXT, 2), (4, 3)), (ATAN2, (ERR, 5), (ERR, 2), (4, 5)),
    (ASIN, (TEXT, 2), (4, 3)),
]


@pytest.mark.parametrize("case", AT)
def test_atan(case):
    if len(case) == 3:
        sel, a, want = case
        (t, p), route = calla(sel, a)
    else:
        sel, a, b, want = case
        (t, p), route = calla(sel, a, b)
    assert t == want[0] and close15(p, want[1]), (t, p, route)


_lchain = {}


def lchain():
    if "h" not in _lchain:
        paths = [os.path.join(KERNEL, "trap.wt")] * 274
        paths[3] = os.path.join(KERNEL, "halt_ok.wt")
        for i, nm in ((267, "fm_dv1"), (268, "fm_pw0"), (269, "fm_pw1"), (273, "fm_lg")):
            paths[i] = os.path.join(MATH, nm + ".wt")
        _lchain["h"] = Harness(paths)
    return _lchain["h"]


def calll(a, b):
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[8] = 0.0
    x[LR_IN], x[LP_IN] = 3.0, 5.0
    x[A_TAG], x[A_PAY] = float(a[0]), float(a[1])
    x[B_TAG], x[B_PAY] = float(b[0]), float(b[1])
    trace = []
    h = lchain()
    h.trace = trace
    out = h.run(273, np.array(x), max_steps=12)
    route = [ln.split()[3] for ln in trace if ln.startswith("step")]
    assert route[0] == "273" and route[-1] == "3", route
    assert out[7] == 5 and out[12] == 0
    return (float(out[13]), float(out[14])), route


LG = [  # Excel documentation examples: LOG(10) 1, LOG(8, 2) 3, LOG(86, 2.7182818) 4.4543473
    (n(10), (MISS, 0), (1, 1)), (n(8), n(2), (1, 3)), (n(86), n(2.7182818), (1, 4.454347342888287)),
    (n(100), n(10), (1, 2)), (n(0.5), n(2), (1, -1)), (n(1), n(5), (1, 0)), (n(81), n(3), (1, 4)),
    (n(0), n(2), (4, 6)), (n(-2), n(2), (4, 6)), (n(2), n(-2), (4, 6)), (n(2), n(1), (4, 2)),
    (n(2), n(0), (4, 6)), ((ERR, 7), n(2), (4, 7)), (n(2), (ERR, 5), (4, 5)), ((TEXT, 1), (ERR, 5), (4, 3)),
    (n(1000), (MISS, 0), (1, 3)),
]


@pytest.mark.parametrize("a,b,want", LG)
def test_log(a, b, want):
    (t, p), route = calll(a, b)
    assert t == want[0] and close15(p, want[1]), (t, p, route)


def call_loop(net_id, path_ids, sel, a, b=(MISS, 0), steps=400):
    paths = [os.path.join(KERNEL, "trap.wt")] * (max(path_ids) + 1)
    paths[3] = os.path.join(KERNEL, "halt_ok.wt")
    for i, nm in path_ids.items():
        paths[i] = os.path.join(MATH, nm + ".wt")
    key = tuple(sorted(path_ids.items()))
    if key not in _chain:
        _chain[key] = Harness(paths)
    h = _chain[key]
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[8] = 0.0
    x[LR_IN], x[LP_IN] = 3.0, 5.0
    x[A_TAG], x[A_PAY] = float(a[0]), float(a[1])
    x[B_TAG], x[B_PAY] = float(b[0]), float(b[1])
    x[T0_IN] = float(sel)
    h.trace = []
    out = h.run(net_id, np.array(x), max_steps=steps)
    nsteps = sum(1 for ln in h.trace if ln.startswith("step"))
    assert out[7] == 5 and out[12] == 0
    return (float(out[13]), float(out[14])), nsteps


FA = [  # hand-stated (Excel documentation: FACT(5) 120, FACT(1.9) 1, FACT(0) 1, FACT(-1) #NUM!,
        # FACT(1) 1; FACTDOUBLE(6) 48, FACTDOUBLE(7) 105)
    (0, n(5), (1, 120)), (0, n(1.9), (1, 1)), (0, n(0), (1, 1)), (0, n(-1), (4, 6)), (0, n(1), (1, 1)),
    (0, n(10), (1, 3628800)), (0, n(20), (1, 2432902008176640000)), (0, n(170), (1, 7.257415615307994e306)),
    (0, n(171), (4, 6)), (0, n(25), (1, 1.5511210043330986e25)), (0, n(1e6), (4, 6)),
    (1, n(6), (1, 48)), (1, n(7), (1, 105)), (1, n(0), (1, 1)), (1, n(-1), (1, 1)), (1, n(-2), (4, 6)),
    (1, n(10), (1, 3840)), (1, n(1), (1, 1)), (1, n(2), (1, 2)), (1, n(302), (4, 6)),
    (0, (ERR, 7), (4, 7)), (0, (TEXT, 3), (4, 3)), (0, (BOOL, 1), (1, 1)),
]


@pytest.mark.parametrize("sel,a,want", FA)
def test_fact(sel, a, want):
    (t, p), _ = call_loop(274, {274: "fm_fact"}, sel, a)
    assert t == want[0] and close15(p, want[1]), (t, p)


CB = [  # hand-stated: Excel documentation COMBIN(8, 2) 28, COMBINA(4, 3) 20, COMBINA(10, 3) 220
    (0, n(8), n(2), (1, 28)), (0, n(10), n(3), (1, 120)), (0, n(5), n(0), (1, 1)), (0, n(5), n(5), (1, 1)),
    (0, n(8.9), n(2.9), (1, 28)), (0, n(52), n(5), (1, 2598960)), (0, n(100), n(50), (1, 1.0089134454556419e29)),
    (0, n(2), n(3), (4, 6)), (0, n(-1), n(0), (4, 6)), (0, n(5), n(-1), (4, 6)), (0, n(1100), n(550), (4, 6)),
    (0, n(60), n(30), (1, 118264581564861424)),
    (1, n(4), n(3), (1, 20)), (1, n(10), n(3), (1, 220)), (1, n(0), n(0), (1, 1)), (1, n(-1), n(2), (4, 6)),
    (0, (ERR, 7), n(1), (4, 7)), (0, n(4), (TEXT, 1), (4, 3)), (0, (BOOL, 1), (BOOL, 1), (1, 1)),
]


@pytest.mark.parametrize("sel,a,b,want", CB)
def test_combin(sel, a, b, want):
    (t, p), _ = call_loop(275, {267: "fm_dv1", 275: "fm_comb"}, sel, a, b, steps=2000)
    assert t == want[0] and close15(p, want[1]), (t, p)


GL = [  # hand-stated: Excel documentation GCD(5, 2) 1, GCD(24, 36) 12, GCD(7, 1) 1, GCD(5, 0) 5,
        # LCM(5, 2) 10, LCM(24, 36) 72
    (0, n(5), n(2), (1, 1)), (0, n(24), n(36), (1, 12)), (0, n(7), n(1), (1, 1)), (0, n(5), n(0), (1, 5)),
    (0, n(0), n(0), (1, 0)), (0, n(0), n(9), (1, 9)), (0, n(24.9), n(36.5), (1, 12)), (0, n(-1), n(2), (4, 6)),
    (0, n(1071), n(462), (1, 21)), (0, n(832040), n(514229), (1, 1)),
    (1, n(5), n(2), (1, 10)), (1, n(24), n(36), (1, 72)), (1, n(5), n(0), (1, 0)), (1, n(0), n(0), (1, 0)),
    (1, n(4294967296), n(4294967297), (4, 6)), (1, n(6), n(-4), (4, 6)), (1, n(21), n(6), (1, 42)),
    (0, (ERR, 7), n(1), (4, 7)), (0, n(4), (TEXT, 1), (4, 3)), (1, (BOOL, 1), n(3), (1, 3)),
]


@pytest.mark.parametrize("sel,a,b,want", GL)
def test_gcd(sel, a, b, want):
    (t, p), _ = call_loop(276, {267: "fm_dv1", 276: "fm_gcd"}, sel, a, b, steps=400)
    assert t == want[0] and close15(p, want[1]), (t, p)


# ---------------- ABI entry (fm_ent 277 -> fm_arg 278 / fm_go 279 -> core -> FN_RET).
# HALT_OK stands at id 257 in place of FN_RET, so the run halts with the function result in A.
ALL_MATH = {264: "fm_unary", 265: "fm_round", 266: "fm_dv0", 267: "fm_dv1", 268: "fm_pw0",
            269: "fm_pw1", 270: "fm_trig", 271: "fm_at0", 272: "fm_at1", 273: "fm_lg", 274: "fm_fact",
            275: "fm_comb", 276: "fm_gcd", 277: "fm_ent", 278: "fm_arg", 279: "fm_go", 280: "fm_rand",
            281: "fm_rnd", 282: "fm_hy0", 283: "fm_hy1", 284: "fm_ah0", 285: "fm_ah1"}
SP0 = 0x1000 + 40


def abi_call(fid, args, steps=3000):
    key = ("abi",)
    if key not in _chain:
        paths = [os.path.join(KERNEL, "trap.wt")] * 286
        paths[257] = os.path.join(KERNEL, "halt_ok.wt")
        for i, nm in ALL_MATH.items():
            paths[i] = os.path.join(MATH, nm + ".wt")
        _chain[key] = Harness(paths)
    h = _chain[key]
    h.mem[:] = 0
    nargs = len(args)
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[8] = 0.0                       # PC 0
    x[28] = float(nargs)             # N0 = n
    x[32] = float(64 + fid)          # T2
    x[54] = float(SP0)               # SP
    x[53] = 7777.0                   # TP (must survive)
    for i, (t, p) in enumerate(args[:-1]):   # arguments 1 .. n - 1 on the operand stack
        a = SP0 - 2 * (nargs - 1 - i)
        h.mem[a], h.mem[a + 1] = t, p
    if nargs:
        x[16], x[17] = float(args[-1][0]), float(args[-1][1])   # B = argument n
    h.trace = []
    out = h.run(277, np.array(x), max_steps=steps)
    route = [ln.split()[3] for ln in h.trace if ln.startswith("step")]
    assert route[0] == "277" and route[-1] == "257", route
    # preserve set (functions.md section 2): N0, P1, GEN, CYC, locals and evaluator registers
    for w in [22, 24, 26, 27] + list(range(40, 64)):
        assert out[w] == x[w + 1], w
    return (float(out[13]), float(out[14]))


ABI = [  # (fid, args, expected) hand-stated from Excel
    (1, [n(-3.5)], (1, 3.5)),                       # ABS
    (362, [], (1, 3.141592653589793)),              # PI()
    (400, [n(2.15), n(1)], (1, 2.2)),               # ROUND
    (482, [n(-8.9)], (1, -8)),                      # TRUNC one argument
    (482, [n(3.14159), n(2)], (1, 3.14)),           # TRUNC two arguments
    (311, [n(-3), n(2)], (1, 1)),                   # MOD
    (53, [n(-5.5), n(2), n(-1)], (1, -6)),          # CEILING.MATH three arguments
    (53, [n(6.7)], (1, 7)),                         # CEILING.MATH one argument
    (367, [n(98.6), n(3.2)], (1, 2401077.2220695773)),  # POWER
    (428, [n(16)], (1, 4)),                         # SQRT
    (284, [n(8), n(2)], (1, 3)),                    # LOG
    (284, [n(1000)], (1, 3)),                       # LOG one argument
    (419, [n(1)], (1, 0.8414709848078965)),         # SIN
    (452, [n(1)], (1, 1.5574077246549023)),         # TAN (through fm_dv1)
    (20, [n(-1), n(-1)], (1, -2.356194490192345)),  # ATAN2
    (17, [n(-0.5)], (1, -0.5235987755982989)),      # ASIN (through SQRT and fm_dv1)
    (163, [n(5)], (1, 120)),                        # FACT
    (72, [n(8), n(2)], (1, 28)),                    # COMBIN
    (202, [n(24), n(36)], (1, 12)),                 # GCD
    (202, [n(7)], (1, 7)),                          # GCD one argument
    (276, [n(24), n(36)], (1, 72)),                 # LCM
    (400, [(ERR, 7), n(1)], (4, 7)),                # error propagates
    (400, [n(2.5), (MISS, 0)], (1, 3)),             # ROUND(2.5,) : missing digits = 0
    (1, [(BOOL, 1)], (1, 1)),
    (420, [n(1)], (1, 1.1752011936438014)),         # SINH
    (83, [n(4)], (1, 27.308232836016487)),          # COSH
    (453, [n(-2)], (1, -0.9640275800758169)),       # TANH (through fm_dv1)
    (412, [n(1)], (1, 0.6480542736638855)),         # SECH
    (102, [n(0)], (4, 2)),                          # CSCH(0) #DIV/0!
    (85, [n(1)], (1, 1.3130352854993312)),          # COTH
    (18, [n(-2.5)], (1, -1.6472311463710958)),      # ASINH (SQRT, LN)
    (5, [n(10)], (1, 2.993222846126381)),           # ACOSH
    (21, [n(-0.1)], (1, -0.10033534773107558)),     # ATANH (series)
    (7, [n(6)], (1, 0.16823611831060645)),          # ACOTH (fm_dv1, LN)
]


@pytest.mark.parametrize("fid,args,want", ABI)
def test_abi(fid, args, want):
    t, p = abi_call(fid, args)
    assert t == want[0] and close15(p, want[1]), (t, p)


def test_rand():
    """RAND(): 0 <= r < 1 (Excel documentation), not constant over 40 calls."""
    seen = set()
    for _ in range(40):
        t, p = abi_call(381, [])
        assert t == 1 and 0 <= p < 1, p
        seen.add(p)
    assert len(seen) > 1


def test_randbetween():
    """RANDBETWEEN(1, 6): integers 1..6; RANDBETWEEN(1.5, 3.5) in 2..3 (bottom rounded up, top down)."""
    seen = set()
    for _ in range(40):
        t, p = abi_call(383, [n(1), n(6)])
        assert t == 1 and p == int(p) and 1 <= p <= 6, p
        seen.add(p)
    assert len(seen) > 1
    for _ in range(10):
        t, p = abi_call(383, [n(1.5), n(3.5)])
        assert t == 1 and p in (2, 3), p
    assert abi_call(383, [n(5), n(5)]) == (1, 5)
    assert abi_call(383, [n(6), n(1)]) == (4, 6)
    assert abi_call(383, [n(-3), n(-3)]) == (1, -3)
    assert abi_call(383, [(ERR, 7), n(1)]) == (4, 7)


HY_PATHS = {267: "fm_dv1", 268: "fm_pw0", 269: "fm_pw1", 282: "fm_hy0", 283: "fm_hy1"}
SINH, COSH, TANH, SECH, CSCH, COTH = range(6)
HY = [  # hand-stated: Excel documentation SINH(1) 1.175201194, COSH(4) 27.30823284, TANH(-2) -0.96402758,
        # TANH(0) 0, TANH(0.5) 0.462117157; other values are the known hyperbolic values
    (SINH, n(1), (1, 1.1752011936438014)), (SINH, n(-1), (1, -1.1752011936438014)), (SINH, n(0), (1, 0)),
    (SINH, n(0.5), (1, 0.5210953054937474)), (SINH, n(2), (1, 3.626860407847019)),
    (SINH, n(10), (1, 11013.232874703393)), (SINH, n(1e-10), (1, 1e-10)),
    (SINH, n(-710), (1, -1.1169973830808557e308)), (SINH, n(711), (4, 6)), (SINH, n(1e300), (4, 6)),
    (COSH, n(4), (1, 27.308232836016487)), (COSH, n(0), (1, 1)), (COSH, n(1), (1, 1.5430806348152437)),
    (COSH, n(-0.5), (1, 1.1276259652063807)), (COSH, n(2), (1, 3.7621956910836314)),
    (COSH, n(10), (1, 11013.232920103324)), (COSH, n(710), (1, 1.1169973830808557e308)), (COSH, n(-711), (4, 6)),
    (TANH, n(-2), (1, -0.9640275800758169)), (TANH, n(0), (1, 0)), (TANH, n(0.5), (1, 0.46211715726000974)),
    (TANH, n(1), (1, 0.7615941559557649)), (TANH, n(1000), (1, 1)), (TANH, n(-30), (1, -1)), (TANH, n(1e308), (1, 1)),
    (SECH, n(1), (1, 0.6480542736638855)), (SECH, n(0), (1, 1)), (SECH, n(800), (1, 0)),
    (CSCH, n(1), (1, 0.8509181282393216)), (CSCH, n(-1), (1, -0.8509181282393216)), (CSCH, n(0), (4, 2)),
    (CSCH, n(-800), (1, 0)), (COTH, n(1), (1, 1.3130352854993312)), (COTH, n(0), (4, 2)), (COTH, n(30), (1, 1)),
    (SINH, (ERR, 7), (4, 7)), (COSH, (TEXT, 3), (4, 3)), (SINH, (BOOL, 1), (1, 1.1752011936438014)),
    (COSH, (BLANK, 0), (1, 1)),
]


@pytest.mark.parametrize("sel,a,want", HY)
def test_hyp(sel, a, want):
    (t, p), _ = call_loop(282, HY_PATHS, sel, a)
    assert t == want[0] and close15(p, want[1]), (t, p)


AH_PATHS = {267: "fm_dv1", 268: "fm_pw0", 269: "fm_pw1", 284: "fm_ah0", 285: "fm_ah1"}
ASINH, ACOSH, ATANH, ACOTH = range(4)
AH = [  # hand-stated: Excel documentation ASINH(-2.5) -1.647231146, ASINH(10) 2.99822295, ACOSH(1) 0,
        # ACOSH(10) 2.9932228, ATANH(-0.1) -0.100335348, ACOTH(6) 0.168236118; others known values
    (ASINH, n(-2.5), (1, -1.6472311463710958)), (ASINH, n(10), (1, 2.99822295029797)), (ASINH, n(0), (1, 0)),
    (ASINH, n(1), (1, 0.881373587019543)), (ASINH, n(0.1), (1, 0.09983407889920758)),
    (ASINH, n(1e10), (1, 23.718998110500402)), (ASINH, n(-1e308), (1, -709.8893558227261)),
    (ACOSH, n(1), (1, 0)), (ACOSH, n(10), (1, 2.993222846126381)), (ACOSH, n(2), (1, 1.3169578969248166)),
    (ACOSH, n(1e10), (1, 23.718998110500402)), (ACOSH, n(0.5), (4, 6)), (ACOSH, n(-2), (4, 6)),
    (ATANH, n(-0.1), (1, -0.10033534773107558)), (ATANH, n(0.5), (1, 0.5493061443340549)), (ATANH, n(0), (1, 0)),
    (ATANH, n(1), (4, 6)), (ATANH, n(-1.5), (4, 6)),
    (ACOTH, n(6), (1, 0.16823611831060645)), (ACOTH, n(-6), (1, -0.16823611831060645)),
    (ACOTH, n(2), (1, 0.5493061443340549)), (ACOTH, n(10), (1, 0.10033534773107558)), (ACOTH, n(1), (4, 6)),
    (ACOTH, n(0.5), (4, 6)), (ACOSH, n(1.5), (1, 0.9624236501192069)), (ATANH, n(0.9), (1, 1.4722194895832204)),
    (ACOTH, n(1.5), (1, 0.8047189562170503)), (ASINH, (ERR, 7), (4, 7)), (ATANH, (TEXT, 3), (4, 3)), (ACOSH, (BOOL, 1), (1, 0)),
]


@pytest.mark.parametrize("sel,a,want", AH)
def test_ahyp(sel, a, want):
    (t, p), _ = call_loop(284, AH_PATHS, sel, a)
    assert t == want[0] and close15(p, want[1]), (t, p)
