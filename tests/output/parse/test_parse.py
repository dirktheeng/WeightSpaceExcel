"""Black-box output tests for the entry parser and formula compiler (weights/parse, ids 64..79).

Calls the parser exactly as the kernel does (weights/kernel/commit.md): the typed text is written
into memory as a packed heap string, A = (2, handle), address register = home cell, LR = 3
(HALT_OK), and network 78 is run. Results are read back from raw memory and the output words:
A (value), STATUS, P1 (formula record), the token stream, HEAP_TOP, FORMULA_TOP.
Expected tokens are stated by hand from encodings/memory-map.md section 6 and encodings/address.md
section 6 (home cell A1, so a relative A1 is RF = 2^20, CF = 2^14). No weight file is opened.
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402
from harness.harness import Harness  # noqa: E402

PATHS = bb.manifest_paths()
HS = 0x30D400          # where the test puts the typed string (inside TEXT_HEAP)
FT0 = 0x090000         # FORMULA_TOP before the entry
TEXT_EMPTY = 0x302000

# hand-computed reference operands (home A1)
A1 = 34359754752       # 2^20 * 2^15 + 2^14
A3 = 34359820288       # (2^20 + 2) * 2^15 + 2^14
B2 = 34359787521       # (2^20 + 1) * 2^15 + 2^14 + 1
AA1 = 206158430208     # $A$1: FLAGS 3 * 2^36
CA1 = 171798691840     # $A1: FLAGS 2 * 2^36 + 2^20 * 2^15
RA1 = 68719493120      # A$1: FLAGS 1 * 2^36 + 2^14


def run(text, locals_=None):
    h = Harness(PATHS)
    m = h.mem
    units = [ord(c) for c in text]
    m[HS] = len(units)
    m[HS + 1] = 1
    for i in range(0, len(units), 3):
        u = units[i:i + 3] + [0, 0]
        m[HS + 2 + i // 3] = u[0] + u[1] * 2**16 + u[2] * 2**32
    m[1] = HS + 2 + (len(units) + 2) // 3          # HEAP_TOP after the string
    m[2] = FT0                                     # FORMULA_TOP
    x = np.zeros(65)
    x[1 + 8] = 3          # LR = HALT_OK
    x[1 + 10] = 0x100     # RSP
    x[1 + 13] = 2         # A.TAG
    x[1 + 14] = HS        # A.PAY
    loc = locals_ if locals_ is not None else list(range(500, 524))
    x[1 + 40:1 + 64] = loc
    trace = []
    h.trace = trace
    out = h.run(78, x, max_steps=20000)
    steps = sum(t.startswith("step") for t in trace)
    return h, out, steps, loc


def tokens(h, rec):
    a, n = int(h.mem[rec + 1]), int(h.mem[rec + 2])
    return [(int(h.mem[a + 2 * i]), float(h.mem[a + 2 * i + 1])) for i in range(n + 1)]


def text_at(h, handle):
    n = int(h.mem[handle])
    return "".join(chr(int(h.mem[handle + 2 + i // 3]) // 2**(16 * (i % 3)) % 2**16) for i in range(n))


def formula(text):
    h, out, steps, loc = run(text)
    assert list(out[40:64]) == loc, "locals L0..L23 not preserved"
    assert out[12] == 0, f"{text!r} rejected"
    rec = int(out[26])
    assert rec == FT0 and h.mem[rec] == HS
    assert out[13] == 0 and out[14] == 0
    toks = tokens(h, rec)
    assert h.mem[2] == rec + 8 + 2 * len(toks), "FORMULA_TOP"
    return toks, h, steps


FORMULAS = [
    ("=1+2*3", [(1, 1), (1, 2), (1, 3), (20, 0), (22, 0)]),
    ("=(1+2)*3", [(1, 1), (1, 2), (22, 0), (1, 3), (20, 0)]),
    ("= 1 + 2", [(1, 1), (1, 2), (22, 0)]),
    ("=((((7))))", [(1, 7)]),
    ("=-2^2", [(1, 2), (16, 0), (1, 2), (19, 0)]),
    ("=2^3^2", [(1, 2), (1, 3), (19, 0), (1, 2), (19, 0)]),
    ("=10-2-3", [(1, 10), (1, 2), (23, 0), (1, 3), (23, 0)]),
    ("=2*-3", [(1, 2), (1, 3), (16, 0), (20, 0)]),
    ("=2+-+-3", [(1, 2), (1, 3), (16, 0), (17, 0), (16, 0), (22, 0)]),
    ("=1+2&3=4", [(1, 1), (1, 2), (22, 0), (1, 3), (24, 0), (1, 4), (25, 0)]),
    ("=5%", [(1, 5), (18, 0)]),
    ("=2^3%", [(1, 2), (1, 3), (18, 0), (19, 0)]),
    ("=-5%", [(1, 5), (16, 0), (18, 0)]),
    ("=1<=2", [(1, 1), (1, 2), (28, 0)]),
    ("=1<>2", [(1, 1), (1, 2), (26, 0)]),
    ("=3>=2", [(1, 3), (1, 2), (30, 0)]),
    ("=3>2", [(1, 3), (1, 2), (29, 0)]),
    ("=1<2", [(1, 1), (1, 2), (27, 0)]),
    ("=.5+.25", [(1, 0.5), (1, 0.25), (22, 0)]),
    ("=0.1+0.2", [(1, 0.1), (1, 0.2), (22, 0)]),
    ("=1.5E+2", [(1, 150)]),
    ("=1e-2", [(1, 0.01)]),
    ("=2.5e1*2", [(1, 25), (1, 2), (20, 0)]),
    ("=123456789012345", [(1, 123456789012345)]),
    ("=12345678901234567", [(1, 12345678901234500)]),
    ("=TRUE", [(3, 1)]),
    ("=false", [(3, 0)]),
    ("=#N/A", [(4, 7)]),
    ("=#div/0!+1", [(4, 2), (1, 1), (22, 0)]),
    ("=#REF!", [(4, 4)]),
    ("=foo", [(4, 5)]),
    ("=A1+B2", [(5, A1), (5, B2), (22, 0)]),
    ("=a1", [(5, A1)]),
    ("=$A$1", [(5, AA1)]),
    ("=$A1", [(5, CA1)]),
    ("=A$1", [(5, RA1)]),
    ("=SUM(A1:A3)", [(6, A1), (7, A3), (64 + 441, 1)]),
    ("=SUM(1,2)", [(1, 1), (1, 2), (64 + 441, 2)]),
    ("=SUM(A1:A3)*2", [(6, A1), (7, A3), (64 + 441, 1), (1, 2), (20, 0)]),
    ("=PI()", [(64 + 362, 0)]),
    ("=IF(,1,2)", [(11, 0), (1, 1), (1, 2), (64 + 218, 3)]),
    ("=IF(1,,2)", [(1, 1), (11, 0), (1, 2), (64 + 218, 3)]),
    ("=ROUND(1.25,1)", [(1, 1.25), (1, 1), (64 + 400, 2)]),
    ("=MAX(1,MIN(2,3))", [(1, 1), (1, 2), (1, 3), (64 + 304, 2), (64 + 296, 2)]),
    ("=FOO(1)", [(1, 1), (64, 1)]),
    ('="abc"&""', [(2, None), (2, TEXT_EMPTY), (24, 0)]),
]


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text,expect", FORMULAS, ids=[f[0] for f in FORMULAS])
def test_formula_tokens(text, expect):
    toks, h, _ = formula(text)
    want = list(expect) + [(0, 0)]
    assert len(toks) == len(want), toks
    for (o, v), (eo, ev) in zip(toks, want):
        assert o == eo, toks
        if ev is not None:
            assert v == ev, toks


@pytest.mark.skipif(PATHS is None, reason="no manifest")
def test_string_literals_in_heap():
    toks, h, _ = formula('="ab""c"&"x"')
    assert text_at(h, int(toks[0][1])) == 'ab"c'
    assert text_at(h, int(toks[1][1])) == "x"
    assert h.mem[1] > toks[1][1], "HEAP_TOP moved past the new strings"


REJECTS = ["=1+", "=(1+2", "=1+2)", "=*2", "=()", "=1 2", '="abc', "=1+2,3", "=A1(1)",
           "=SUM(1+,2)", "=#BOGUS!", "=1e", "=1.2.3", "=@1", "=$A", "=SUM(A1:)"]


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text", REJECTS)
def test_rejected(text):
    h, out, _, loc = run(text)
    assert out[12] != 0
    assert list(out[40:64]) == loc
    assert h.mem[2] == FT0, "FORMULA_TOP unchanged on reject"


CONSTANTS = [
    ("5", 1, 5), ("-5", 1, -5), ("3.25", 1, 3.25), ("1e3", 1, 1000), ("12%", 1, 0.12),
    ("1,000", 1, 1000), ("$1,234.50", 1, 1234.5), ("(5)", 1, -5), ("+5", 1, 5), (".5", 1, 0.5),
    ("0012", 1, 12), ("0.3", 1, 0.3), ("12345678901234567", 1, 12345678901234500),
    ("TRUE", 3, 1), ("false", 3, 0), ("#N/A", 4, 7), ("#DIV/0!", 4, 2), ("#VALUE!", 4, 3),
    ("#NAME?", 4, 5), ("", 0, 0),
]


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text,tag,pay", CONSTANTS, ids=[c[0] or "empty" for c in CONSTANTS])
def test_constant(text, tag, pay):
    h, out, _, loc = run(text)
    assert out[12] == 0 and out[26] == 0
    assert list(out[40:64]) == loc
    assert (out[13], out[14]) == (tag, pay)


TEXTS = [("abc", "abc"), ("1 2", "1 2"), ("1e", "1e"), ("#nope", "#nope"), ("'123", "123"),
         ("'=1+1", "=1+1"), ("'", "")]


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text,want", TEXTS)
def test_text_constant(text, want):
    h, out, _, loc = run(text)
    assert out[12] == 0 and out[13] == 2
    assert text_at(h, int(out[14])) == want
    if text.startswith("'"):
        assert out[14] != HS
    if want == "":
        assert out[14] == TEXT_EMPTY


@pytest.mark.skipif(PATHS is None, reason="no manifest")
def test_step_counts_reported():
    # Not a pass criterion beyond sanity: records steps for the log (printed with -s).
    for text in ["5", "abc", "=1+2*3", "=SUM(A1:A3)*2"]:
        _, _, steps, _ = run(text)
        print(f"steps {text!r}: {steps}")
        assert steps < 400
