"""Output tests for the primitive block library (weights/prim/, encodings/primitives.md).

Black box (docs/RULES.md rule 2): each test network is loaded by path only, given a
65-word input in the 64-word register convention (encodings/control.md), run for one
step, and its output words are compared with values stated by hand from the math.
Weight files are never opened here.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402

PRIM = os.path.join(ROOT, "weights", "prim")

# input index = output word + 1 (encodings/control.md section 1)
A_TAG, A_PAY, B_TAG, B_PAY, C_TAG, C_PAY = 14, 15, 16, 17, 18, 19
AS, AR1, AC1 = 20, 21, 22
T0_IN = 30
T0 = 29  # output word of T0

MAXD = 1.7976931348623157e308


def run(name, **inp):
    x = [0.0] * 65
    for i in range(65):
        x[i] = 1000.0 + i  # recognisable pass-through words
    x[0] = 0.0
    for k, v in inp.items():
        x[globals()[k] if not k.startswith("i") else int(k[1:])] = v
    h = Harness([os.path.join(PRIM, name + ".wt")])
    out = h.run(0, x, max_steps=1)
    assert len(out) == 64
    assert list(out[:7]) == [0, 0, 0, 0, 0, 0, 1]
    return out, x


def results(name, n, **inp):
    out, x = run(name, **inp)
    # pass-through check: every word that is not a result equals its input word
    for w in range(7, 64):
        if not T0 <= w < T0 + n:
            assert out[w] == x[w + 1], (name, w)
    return [float(v) for v in out[T0:T0 + n]]


# ---------------- IS_K and ONEHOT
@pytest.mark.parametrize("x,want", [(3, 1), (2, 0), (4, 0), (0, 0), (-3, 0), (1e15, 0)])
def test_is_k(x, want):
    assert results("is_k", 1, A_TAG=x) == [want]


@pytest.mark.parametrize("x,want", [
    (0, [1, 0, 0, 0, 0]), (1, [0, 1, 0, 0, 0]), (2, [0, 0, 1, 0, 0]),
    (3, [0, 0, 0, 1, 0]), (4, [0, 0, 0, 0, 1]), (5, [0, 0, 0, 0, 0]),
    (-1, [0, 0, 0, 0, 0]), (63, [0, 0, 0, 0, 0])])
def test_onehot(x, want):
    assert results("onehot", 5, A_TAG=x) == want


# ---------------- real compare: [LT, EQ, GT, SIGN(a)]
@pytest.mark.parametrize("a,b,want", [
    (1, 2, [1, 0, 0, 1]), (2, 1, [0, 0, 1, 1]), (2, 2, [0, 1, 0, 1]),
    (-0.0, 0.0, [0, 1, 0, 0]), (0.0, 0.0, [0, 1, 0, 0]),
    (0.1 + 0.2, 0.3, [0, 0, 1, 1]),            # 0.30000000000000004 > 0.3
    (5e-324, 0.0, [0, 0, 1, 1]),               # smallest subnormal
    (-5e-324, 5e-324, [1, 0, 0, -1]),
    (MAXD, -MAXD, [0, 0, 1, 1]),               # a - b overflows; only step reads it
    (-MAXD, MAXD, [1, 0, 0, -1]),
    (1.0, 1.0000000000000002, [1, 0, 0, 1]),   # one ulp apart
    (-7.5, -7.5, [0, 1, 0, -1])])
def test_compare(a, b, want):
    assert results("compare", 4, A_PAY=a, B_PAY=b) == want


# ---------------- MUX: [mul form, relu big-M form]
@pytest.mark.parametrize("g,a,b,want", [
    (1, 5, 9, [5, 5]), (0, 5, 9, [9, 9]),
    (1, -4194303, 4194303, [-4194303, -4194303]), (0, -4194303, 4194303, [4194303, 4194303]),
    (1, 0, -7, [0, 0]), (0, 3, -7, [-7, -7])])
def test_mux_int_and_mul(g, a, b, want):
    assert results("mux", 2, C_PAY=g, A_PAY=a, B_PAY=b) == want


@pytest.mark.parametrize("g,a,b,want", [
    (1, 0.1, MAXD, 0.1), (0, 0.1, MAXD, MAXD), (1, -MAXD, 2.5, -MAXD), (0, 1e300, 5e-324, 5e-324)])
def test_mux_doubles(g, a, b, want):
    assert results("mux", 2, C_PAY=g, A_PAY=a, B_PAY=b)[0] == want


# ---------------- FLOOR, CEIL, ROUND (even), TRUNC, ROUND half away
@pytest.mark.parametrize("x,want", [
    (2.5, [2, 3, 2, 2, 3]), (-2.5, [-3, -2, -2, -2, -3]), (3.5, [3, 4, 4, 3, 4]),
    (1.5, [1, 2, 2, 1, 2]), (-1.5, [-2, -1, -2, -1, -2]),
    (-0.5, [-1, 0, 0, 0, -1]), (0.5, [0, 1, 0, 0, 1]),
    (0.49999999999999994, [0, 1, 0, 0, 0]), (-0.49999999999999994, [-1, 0, 0, 0, 0]),
    (7, [7, 7, 7, 7, 7]), (-7, [-7, -7, -7, -7, -7]), (0, [0, 0, 0, 0, 0]),
    (-0.0001, [-1, 0, 0, 0, 0]), (2.7, [2, 3, 3, 2, 3]), (-2.7, [-3, -2, -3, -2, -3]),
    (1e15 + 0.25, [1e15, 1e15 + 1, 1e15, 1e15, 1e15]),
    (2.0**51 - 0.5, [2.0**51 - 1, 2.0**51, 2.0**51, 2.0**51 - 1, 2.0**51]),
    (-(2.0**51 - 0.5), [-2.0**51, -(2.0**51 - 1), -2.0**51, -(2.0**51 - 1), -2.0**51])])
def test_floor_round(x, want):
    assert results("floor_round", 5, A_PAY=x) == want


# ---------------- MOD2K(x, 16): [x mod 65536, floor(x / 65536)]
@pytest.mark.parametrize("x,want", [
    (0, [0, 0]), (1, [1, 0]), (65535, [65535, 0]), (65536, [0, 1]), (65537, [1, 1]),
    (131071, [65535, 1]), (-1, [65535, -1]), (-65536, [0, -1]),
    (2.0**51 - 1, [65535, 2.0**35 - 1]), (1000003, [16963, 15])])
def test_mod2k(x, want):
    assert results("mod2k", 2, A_PAY=x) == want


# ---------------- DIVMOD_K(x, 10): [floor(x / 10), x mod 10]
@pytest.mark.parametrize("x,want", [
    (0, [0, 0]), (9, [0, 9]), (10, [1, 0]), (19, [1, 9]), (99, [9, 9]), (100, [10, 0]),
    (-1, [-1, 9]), (-10, [-1, 0]), (-11, [-2, 9]),
    (999999999999999, [99999999999999, 9]), (1000000000000000, [100000000000000, 0]),
    (2251799813685247, [225179981368524, 7])])   # 2^51 - 1
def test_divmod_k(x, want):
    assert results("divmod_k", 2, A_PAY=x) == want


# ---------------- DIGITS: d0 (units) .. d14
@pytest.mark.parametrize("n,digits", [
    (0, "0"), (7, "7"), (10, "10"), (123456789012345, "123456789012345"),
    (999999999999999, "999999999999999"), (100000000000000, "100000000000000"),
    (900719925474099, "900719925474099"), (500000000000005, "500000000000005"),
    (99999, "99999")])
def test_digits(n, digits):
    want = [int(c) for c in reversed(digits.rjust(15, "0"))]
    assert results("digits", 15, A_PAY=n) == want


# ---------------- SAFE_ADD: [sum or 0, overflow]
@pytest.mark.parametrize("a,b,want", [
    (2, 3, [5, 0]), (0.1, 0.2, [0.30000000000000004, 0]), (1e308, 1e308, [0, 1]),
    (-1e308, -1e308, [0, 1]), (1e308, -1e308, [0, 0]), (MAXD, 1, [MAXD, 0]),
    (MAXD, 1e292, [0, 1]), (MAXD, 9e291, [MAXD, 0]), (-MAXD, -1e292, [0, 1]),
    (MAXD, -MAXD, [0, 0]), (5e-324, 5e-324, [1e-323, 0])])
def test_safe_add(a, b, want):
    assert results("safe_add", 2, A_PAY=a, B_PAY=b) == want


# ---------------- SAFE_MUL: [product or 0, overflow]
@pytest.mark.parametrize("a,b,want", [
    (3, -7, [-21, 0]), (1e200, 1e200, [0, 1]), (-1e200, 1e200, [0, 1]),
    (MAXD, 1, [MAXD, 0]), (MAXD, 1.0000000000000002, [0, 1]), (MAXD, -1, [-MAXD, 0]),
    (1e-300, 1e-300, [0, 0]), (2.0**512, 2.0**511, [2.0**1023, 0]),
    (2.0**512, 2.0**512, [0, 1]), (0.1, 3, [0.30000000000000004, 0]), (0, MAXD, [0, 0])])
def test_safe_mul(a, b, want):
    assert results("safe_mul", 2, A_PAY=a, B_PAY=b) == want


# ---------------- HASH: [slot, address]
@pytest.mark.parametrize("s,r,c,ns,f,want", [
    (0, 0, 0, 0, 0, [0, 65536]), (0, 1, 0, 0, 0, [40503, 389560]),
    (0, 2, 0, 0, 1, [15470, 189297]), (0, 0, 1, 0, 0, [63, 66040]),
    (1, 0, 0, 0, 0, [16963, 201240]), (0, 0, 0, 1, 2, [7919, 128890]),
    (0, 1048575, 16383, 0, 0, [8586, 134224])])
def test_hash(s, r, c, ns, f, want):
    assert results("hash", 2, AS=s, AR1=r, AC1=c, i30=ns, i31=f) == want


# ---------------- DIVMOD with a variable integer divisor: [floor(x / d), x mod d]
@pytest.mark.parametrize("x,d,want", [
    (7, 2, [3, 1]), (100, 7, [14, 2]), (-7, 2, [-4, 1]), (0, 5, [0, 0]), (1000, 1, [1000, 0]),
    (562949953421311, 3, [187649984473770, 1]),                    # 2^49 - 1
    (562949953421311, 562949953421312, [0, 562949953421311]),
    (562949953421311, 562949953421311, [1, 0]),
    (-1, 562949953421312, [-1, 562949953421311]),
    (12345678901234, 97, [127275040218, 88]),
    (-562949953421311, 7, [-80421421917331, 6]),
    (999999999999, 999999, [1000001, 0]), (999999999998, 999999, [1000000, 999998]),
    (65535, 255, [257, 0]), (65536, 255, [257, 1])])
def test_idivmod(x, d, want):
    assert results("idivmod", 2, A_PAY=x, B_PAY=d) == want


# ---------------- DIV: [fl(a / b) or 0, overflow, divide by zero]
H = float.fromhex  # exact binary literals, not computed values
DIV_CASES = [
    (6, 3, 2.0), (1, 3, 0.3333333333333333), (2, 3, 0.6666666666666666),
    (4, 3, 1.3333333333333333), (5, 3, 1.6666666666666667), (10, 3, 3.3333333333333335),
    (1, 9, 0.1111111111111111), (1, 10, 0.1), (1, 0.1, 10.0), (22, 7, 3.142857142857143),
    (100, 7, 14.285714285714286), (1, 49, 0.02040816326530612), (0.1, 3, 0.03333333333333333),
    (0.3, 0.1, 2.9999999999999996), (0.6, 0.2, 2.9999999999999996), (0.7, 0.1, 6.999999999999999),
    (-2, 3, -0.6666666666666666), (1, -7, -0.14285714285714285), (-1, -7, 0.14285714285714285),
    (3, 1.5, 2.0), (-7.5, 2.5, -3.0), (0, 5, 0.0), (0, -5e-324, 0.0),
    # binade edges: 1/(1 + 2^-52) = 1 - 2^-52; 1/(2 - 2^-52) just above the 0.5 midpoint
    (1, H("0x1.0000000000001p+0"), H("0x1.ffffffffffffep-1")),
    (1, H("0x1.fffffffffffffp+0"), H("0x1.0000000000001p-1")),
    (H("0x1.fffffffffffffp+0"), H("0x1.0000000000001p+0"), H("0x1.ffffffffffffdp+0")),
    # extremes
    (H("0x1.fffffffffffffp+1023"), 2, H("0x1.fffffffffffffp+1022")),
    (H("0x1.fffffffffffffp+1023"), 1, H("0x1.fffffffffffffp+1023")),
    (H("0x1p-1000"), H("0x1p-1074"), H("0x1p+74")),
    (1, H("0x1.fffffffffffffp+1023"), H("0x1p-1024")),             # subnormal result
    (H("0x1p-1022"), 4, H("0x1p-1024")),
    (H("0x0.0000000000001p-1022"), 0.5, H("0x0.0000000000002p-1022")),
    (H("0x0.0000000000001p-1022"), 2, 0.0),                         # 2^-1075 ties to even 0
    (H("0x0.0000000000003p-1022"), 2, H("0x0.0000000000002p-1022")),  # 1.5 units ties to 2
    (H("0x1p+1023"), 0.5, None), (H("0x1.fffffffffffffp+1023"), 0.5, None),
    (H("0x1.fffffffffffffp+1023"), H("0x1.fffffffffffffp-1"), None),  # MAXD / (1 - 2^-53)
    (1, H("0x0.0000000000001p-1022"), None), (-1e308, 1e-10, None)]


@pytest.mark.parametrize("a,b,want", DIV_CASES)
def test_div(a, b, want):
    q, ov, dz = results("div", 3, A_PAY=a, B_PAY=b)
    if want is None:
        assert (q, ov, dz) == (0, 1, 0)
    else:
        assert (q, ov, dz) == (want, 0, 0)


@pytest.mark.parametrize("a", [3, -3, 0, 1e308])
def test_div_by_zero(a):
    q, ov, dz = results("div", 3, A_PAY=a, B_PAY=0.0)
    assert q == 0 and dz == 1
