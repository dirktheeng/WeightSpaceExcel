"""Output tests for the Text function cores (weights/func/text, ids 312 to 343).

Black box (docs/RULES.md rule 2): strings are placed in the text heap by the documented
layout (encodings/memory-map.md section 9) as test input, a core is called with the
register convention (encodings/control.md) and LR = HALT_OK (3), and the result register
A and heap contents are decoded. Expected values are stated by hand from Excel's
documented behaviour. Weight files are never opened here.
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from blackbox import manifest_paths, text_at  # noqa: E402
from harness.harness import Harness  # noqa: E402

TEXT_EMPTY = 0x302000
H1, H2 = 0x310000, 0x311000      # where tests place argument strings
HT0 = 0x320000                   # heap top handed to the core (word 23)
IDS = {"LEN": 312, "CODE": 313, "CASE": 314, "EXACT": 315, "MID": 316, "CHAR": 317, "T": 318}

_paths = None


def put(h, addr, s):
    if s == "":
        return TEXT_EMPTY
    b = s.encode("utf-16-le")
    u = [b[i] + 256 * b[i + 1] for i in range(0, len(b), 2)]
    h.mem[addr] = len(u)
    h.mem[addr + 1] = 1
    for j in range(0, len(u), 3):
        c = (u[j:j + 3] + [0, 0])[:3]
        h.mem[addr + 2 + j // 3] = c[0] + c[1] * 2**16 + c[2] * 2**32
    return addr


def call(name, a=(0, 0), b=(0, 0), c=(0, 0), strings=(), regs=None, max_steps=20000, x0=0.0):
    """strings: up to two python strings; their handles replace 'S1', 'S2' in a, b, c."""
    global _paths
    if _paths is None:
        _paths = manifest_paths()
    h = Harness(_paths)
    hs = [put(h, ad, s) for ad, s in zip((H1, H2), strings)]

    def val(v):
        t, p = v
        if isinstance(p, str):
            p = hs[int(p[1]) - 1]
        return float(t), float(p)

    x = np.zeros(65)
    for w in range(7, 64):
        x[w + 1] = 0
    x[8], x[9], x[10] = 0, 3, 0           # PC, LR = HALT_OK, LP
    x[11] = 0x100                         # RSP
    x[14], x[15] = val(a)
    x[16], x[17] = val(b)
    x[18], x[19] = val(c)
    x[24] = HT0                           # HT (word 23)
    for w, v in (regs or {}).items():
        x[w + 1] = v
    x[0] = x0                             # read result left by the caller's previous step
    x[64] = 777                           # a local that must survive
    out = h.run(IDS[name], x, max_steps=max_steps)
    assert out[63] == 777
    return h, out


def res(h, out):
    t, p = int(out[13]), out[14]
    if t == 1:
        return p
    if t == 2:
        return text_at(h, int(p))
    if t == 3:
        return bool(p)
    if t == 4:
        return ("err", int(p))
    return (t, p)


# ---------------- LEN
@pytest.mark.parametrize("s,n", [("", 0), ("a", 1), ("ab", 2), ("abc", 3), ("abcd", 4),
                                 ("Hello, World", 12), ("  x  ", 5)])
def test_len(s, n):
    h, out = call("LEN", a=(2, "S1"), strings=[s])
    assert res(h, out) == n


def test_len_error_passes():
    h, out = call("LEN", a=(4, 7))
    assert res(h, out) == ("err", 7)


# ---------------- CODE / UNICODE (first UTF-16 unit)
@pytest.mark.parametrize("s,n", [("A", 65), ("abc", 97), ("Zebra", 90), (" ", 32), ("~x", 126),
                                 ("été", 233), ("中", 20013)])
def test_code(s, n):
    h, out = call("CODE", a=(2, "S1"), strings=[s])
    assert res(h, out) == n


def test_code_empty_is_value_error():
    h, out = call("CODE", a=(2, "S1"), strings=[""])
    assert res(h, out) == ("err", 3)


def test_code_error_passes():
    h, out = call("CODE", a=(4, 2))
    assert res(h, out) == ("err", 2)


# ---------------- UPPER / LOWER (N0 = 0 UPPER, 1 LOWER; word 27 at input 28)
N0 = 27


@pytest.mark.parametrize("s,want", [("", ""), ("abc", "ABC"), ("Hello, World!", "HELLO, WORLD!"),
                                    ("az@[`{", "AZ@[`{"), ("café ÷ÿ", "CAFÉ ÷ÿ"),
                                    ("x1y2z3w", "X1Y2Z3W"), ("ALREADY", "ALREADY")])
def test_upper(s, want):
    h, out = call("CASE", a=(2, "S1"), strings=[s], regs={N0: 0})
    assert res(h, out) == want
    assert out[23] == HT0 + 2 + (len(s) + 2) // 3


@pytest.mark.parametrize("s,want", [("ABC", "abc"), ("Hello, World!", "hello, world!"),
                                    ("AZ@[`{", "az@[`{"), ("CAFÉ ×", "café ×"),
                                    ("lower", "lower")])
def test_lower(s, want):
    h, out = call("CASE", a=(2, "S1"), strings=[s], regs={N0: 1})
    assert res(h, out) == want


def test_case_error_passes():
    h, out = call("CASE", a=(4, 5), regs={N0: 0})
    assert res(h, out) == ("err", 5)
    assert out[23] == HT0


# ---------------- EXACT
@pytest.mark.parametrize("s,t,want", [("word", "word", True), ("Word", "word", False),
                                      ("w ord", "word", False), ("", "", True), ("a", "", False),
                                      ("", "a", False), ("abc", "abcd", False), ("abcdef", "abcdef", True),
                                      ("abcdefg", "abcdefh", False), ("abcdefg", "abcdefg", True),
                                      ("xbcdefg", "abcdefg", False)])
def test_exact(s, t, want):
    h, out = call("EXACT", a=(2, "S1"), b=(2, "S2"), strings=[s, t])
    assert res(h, out) is want


def test_exact_errors():
    h, out = call("EXACT", a=(4, 7), b=(4, 2))
    assert res(h, out) == ("err", 7)
    h, out = call("EXACT", a=(2, "S1"), b=(4, 2), strings=["x"])
    assert res(h, out) == ("err", 2)


# ---------------- MID (A text, B start, C count); LEFT = MID(s, 1, n)
@pytest.mark.parametrize("s,st,n,want", [
    ("Fluid Flow", 1, 5, "Fluid"), ("Fluid Flow", 7, 20, "Flow"), ("Fluid Flow", 20, 5, ""),
    ("abcdefghij", 2, 3, "bcd"), ("abcdefghij", 3, 3, "cde"), ("abcdefghij", 4, 3, "def"),
    ("abcdefghij", 2, 7, "bcdefgh"), ("abcdefghij", 3, 8, "cdefghij"), ("abcdefghij", 1, 10, "abcdefghij"),
    ("abcdefghij", 10, 1, "j"), ("abcdefghij", 11, 1, ""), ("abcdefghij", 5, 0, ""),
    ("abc", 1.9, 2.7, "ab"), ("abc", 2, 1e300, "bc"), ("", 1, 3, ""),
    ("abcdefghij", 1, 4, "abcd"), ("abcdefghij", 1, 2, "ab"),
])
def test_mid(s, st, n, want):
    h, out = call("MID", a=(2, "S1"), b=(1, st), c=(1, n), strings=[s])
    assert res(h, out) == want
    assert out[23] == HT0 + 2 + (len(want) + 2) // 3


@pytest.mark.parametrize("st,n", [(0, 1), (-3, 1), (0.5, 2), (1, -1), (-1e300, 1)])
def test_mid_value_errors(st, n):
    h, out = call("MID", a=(2, "S1"), b=(1, st), c=(1, n), strings=["abc"])
    assert res(h, out) == ("err", 3)
    assert out[23] == HT0


def test_mid_error_order():
    h, out = call("MID", a=(4, 7), b=(4, 2), c=(4, 6))
    assert res(h, out) == ("err", 7)
    h, out = call("MID", a=(2, "S1"), b=(4, 2), c=(4, 6), strings=["x"])
    assert res(h, out) == ("err", 2)
    h, out = call("MID", a=(2, "S1"), b=(1, 0), c=(4, 6), strings=["x"])
    assert res(h, out) == ("err", 6)


# ---------------- CHAR (N0 = 0) and UNICHAR (N0 = 1)
@pytest.mark.parametrize("n,want", [(65, "A"), (97, "a"), (32, " "), (1, "\x01"), (255, "ÿ"),
                                    (65.9, "A"), (128, "€"), (129, "\x81"), (150, "–"),
                                    (151, "—"), (153, "™"), (159, "Ÿ"), (160, " "),
                                    (127, "\x7f"), (146, "’")])
def test_char(n, want):
    h, out = call("CHAR", a=(1, n), regs={N0: 0})
    assert res(h, out) == want
    assert out[23] == HT0 + 3


@pytest.mark.parametrize("n", [0, 256, -1, 0.5, 1e300, -1e300])
def test_char_value_error(n):
    h, out = call("CHAR", a=(1, n), regs={N0: 0})
    assert res(h, out) == ("err", 3)
    assert out[23] == HT0


@pytest.mark.parametrize("n,want", [(65, "A"), (128, "\x80"), (8364, "€"), (20013, "中"),
                                    (65535, "￿"), (65536, "\U00010000"), (128512, "\U0001F600"),
                                    (1114111, "\U0010FFFF"), (55295, "퟿"), (57344, "")])
def test_unichar(n, want):
    h, out = call("CHAR", a=(1, n), regs={N0: 1})
    assert res(h, out) == want


@pytest.mark.parametrize("n,err", [(0, 3), (1114112, 3), (-5, 3), (55296, 7), (57343, 7), (56000, 7)])
def test_unichar_errors(n, err):
    h, out = call("CHAR", a=(1, n), regs={N0: 1})
    assert res(h, out) == ("err", err)


def test_char_error_passes():
    h, out = call("CHAR", a=(4, 2), regs={N0: 0})
    assert res(h, out) == ("err", 2)


# ---------------- T
def test_t_text():
    h, out = call("T", a=(2, "S1"), strings=["Rainfall"])
    assert res(h, out) == "Rainfall" and out[14] == H1


@pytest.mark.parametrize("a", [(1, 19), (1, -2.5), (3, 1), (3, 0), (0, 0), (8, 0)])
def test_t_non_text_is_empty(a):
    h, out = call("T", a=a)
    assert res(h, out) == "" and out[14] == TEXT_EMPTY


def test_t_error_passes():
    h, out = call("T", a=(4, 7))
    assert res(h, out) == ("err", 7)


# ---------------- a large stale read result (input word 0) on entry must not leak
@pytest.mark.parametrize("name", ["LEN", "CODE", "CASE", "EXACT", "MID", "CHAR", "T"])
def test_stale_x0_error_return(name):
    h, out = call(name, a=(4, 2), b=(4, 3), c=(4, 4), x0=3.0e14)
    assert res(h, out) == ("err", 2)
    assert out[23] == HT0


@pytest.mark.parametrize("x0", [3.0e14, -7.25, 1e300])
def test_stale_x0_normal_paths(x0):
    h, out = call("LEN", a=(2, "S1"), strings=["abcd"], x0=x0)
    assert res(h, out) == 4
    h, out = call("MID", a=(2, "S1"), b=(1, 2), c=(1, 2), strings=["abcd"], x0=x0)
    assert res(h, out) == "bc"
    h, out = call("CASE", a=(2, "S1"), strings=["abcd"], regs={N0: 0}, x0=x0)
    assert res(h, out) == "ABCD"
