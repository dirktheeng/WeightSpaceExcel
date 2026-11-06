"""Black-box output tests for the parser extension (2026-11-06, session 2): whole-column and whole-row
references, the union (,) and intersection (space) operators, sheet prefixes, and number literals with
decimal exponents beyond 22.

Calls the parser exactly as the kernel does (weights/kernel/commit.md), like test_parse.py, but can
also lay out a sheet table (encodings/memory-map.md sections 3 and 5: SHEET_COUNT at 0x0F, sheet record
word 0 = name handle) and choose the home cell. Expected tokens are stated by hand from
encodings/memory-map.md sections 6 and 13 and encodings/address.md sections 5 and 6; numbers are the
nearest doubles to the typed decimals (Excel stores those). No weight file is opened.
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
HS = 0x30D400
FT0 = 0x090000
SHEET_NAMES = ["Sheet1", "My Sheet", "Data_2024", "It's"]
NAME_BASE = 0x320000   # test-only place for the sheet name strings (inside TEXT_HEAP)

# hand-computed reference operands, home A1 (relative row bias 2^20, column bias 2^14)
A1 = 34359754752       # 2^20 * 2^15 + 2^14
B1 = 34359754753
C1 = 34359754754
B2 = 34359787521       # (2^20 + 1) * 2^15 + 2^14 + 1
B3 = 34359820289       # (2^20 + 2) * 2^15 + 2^14 + 1
C3 = 34359820290
D4 = 34359853059       # (2^20 + 3) * 2^15 + 2^14 + 3
AA1 = 206158430208     # $A$1
# whole columns: corner 1 row absolute 0, corner 2 row absolute 1048575 (FLAGS bit 0 set)
COL_A1 = 68719493120   # A:A first corner, 2^36 + 2^14
COL_A2 = 103079198720  # A:A second corner, 2^36 + 1048575 * 2^15 + 2^14
COLABS_A1 = 206158430208   # $A:$C first corner, 3 * 2^36
COLABS_C2 = 240518135810   # $A:$C second corner, 3 * 2^36 + 1048575 * 2^15 + 2
# whole rows: corner 1 column absolute 0, corner 2 column absolute 16383 (FLAGS bit 1 set)
ROW_3A = 171798757376  # 3:3 first corner, 2^37 + (2 + 2^20) * 2^15
ROW_3B = 171798773759  # 3:3 second corner, + 16383
ROW_1A = 171798691840  # 1:5 first corner, 2^37 + 2^20 * 2^15
ROW_5B = 171798839295  # 1:5 second corner, 2^37 + (4 + 2^20) * 2^15 + 16383
ROWABS_1A = 206158430208   # $1:$5 first corner, 3 * 2^36
ROWABS_5B = 206158577663   # $1:$5 second corner, 3 * 2^36 + 4 * 2^15 + 16383


def pack_string(m, addr, s):
    units = [ord(c) for c in s]
    m[addr] = len(units)
    m[addr + 1] = 1
    for i in range(0, len(units), 3):
        u = units[i:i + 3] + [0, 0]
        m[addr + 2 + i // 3] = u[0] + u[1] * 2**16 + u[2] * 2**32
    return addr + 2 + (len(units) + 2) // 3


def run(text, home=(0, 0), sheets=SHEET_NAMES):
    h = Harness(PATHS)
    m = h.mem
    for k, name in enumerate(sheets):
        m[0x4000 + 16 * k] = NAME_BASE + 64 * k
        pack_string(m, NAME_BASE + 64 * k, name)
    m[0x0F] = len(sheets)
    m[1] = pack_string(m, HS, text)
    m[2] = FT0
    x = np.zeros(65)
    x[1 + 8] = 3          # LR = HALT_OK
    x[1 + 10] = 0x100     # RSP
    x[1 + 13] = 2         # A.TAG
    x[1 + 14] = HS        # A.PAY
    x[1 + 20], x[1 + 21] = home    # AR1, AC1 (home ROW, COL)
    loc = list(range(500, 524))
    x[1 + 40:1 + 64] = loc
    trace = []
    h.trace = trace
    out = h.run(78, x, max_steps=20000)
    steps = sum(t.startswith("step") for t in trace)
    return h, out, steps, loc


def tokens(h, rec):
    a, n = int(h.mem[rec + 1]), int(h.mem[rec + 2])
    return [(int(h.mem[a + 2 * i]), float(h.mem[a + 2 * i + 1])) for i in range(n + 1)]


def formula(text, **kw):
    h, out, steps, loc = run(text, **kw)
    assert list(out[40:64]) == loc, "locals L0..L23 not preserved"
    assert out[12] == 0, f"{text!r} rejected"
    rec = int(out[26])
    assert rec == FT0 and h.mem[rec] == HS
    toks = tokens(h, rec)
    assert h.mem[2] == rec + 8 + 2 * len(toks), "FORMULA_TOP"
    return toks, steps


SUM = 64 + 441

FORMULAS = [
    # whole columns and rows
    ("=A:A", [(6, COL_A1), (7, COL_A2)]),
    ("=$A:$C", [(6, COLABS_A1), (7, COLABS_C2)]),
    ("=3:3", [(6, ROW_3A), (7, ROW_3B)]),
    ("=1:5", [(6, ROW_1A), (7, ROW_5B)]),
    ("=$1:$5", [(6, ROWABS_1A), (7, ROWABS_5B)]),
    ("=SUM(A:A)", [(6, COL_A1), (7, COL_A2), (SUM, 1)]),
    ("=SUM(3:3)", [(6, ROW_3A), (7, ROW_3B), (SUM, 1)]),
    ("=SUM(A:A,1:5)", [(6, COL_A1), (7, COL_A2), (6, ROW_1A), (7, ROW_5B), (SUM, 2)]),
    ("=B5:A1", [(6, 34359885825), (7, A1)]),          # corners kept as typed (decision P9)
    # union and intersection
    ("=SUM((A1,C1))", [(5, A1), (5, C1), (32, 0), (SUM, 1)]),
    ("=(A1,B1,C1)", [(5, A1), (5, B1), (32, 0), (5, C1), (32, 0)]),
    ("=SUM(A1:A2,A1:A2)", [(6, A1), (7, 34359787520), (6, A1), (7, 34359787520), (SUM, 2)]),
    ("=A1:C1 B1:B3", [(6, A1), (7, C1), (6, B1), (7, B3), (33, 0)]),
    ("=A1:C3 B2:D4 B2", [(6, A1), (7, C3), (6, B2), (7, D4), (5, B2), (33, 0), (33, 0)]),
    ("=SUM(A1:C3 B2:D4)", [(6, A1), (7, C3), (6, B2), (7, D4), (33, 0), (SUM, 1)]),
    ("=A1 (B1)", [(5, A1), (5, B1), (33, 0)]),
    ("=-A1 B1", [(5, A1), (5, B1), (33, 0), (16, 0)]),
    ("=A1 B1^2", [(5, A1), (5, B1), (33, 0), (1, 2), (19, 0)]),
    ("=A1 B1%", [(5, A1), (5, B1), (33, 0), (18, 0)]),
    ("=(A1 B1,C1)", [(5, A1), (5, B1), (33, 0), (5, C1), (32, 0)]),
    ("=(A1,B1 C1)", [(5, A1), (5, B1), (5, C1), (33, 0), (32, 0)]),
    ("=A1 +B1", [(5, A1), (5, B1), (22, 0)]),
    ("=SUM(A1 )", [(5, A1), (SUM, 1)]),
    ("=SUM(A1, B1)", [(5, A1), (5, B1), (SUM, 2)]),
    # sheet prefixes (sheet table: 0 Sheet1, 1 My Sheet, 2 Data_2024, 3 It's)
    ("=Sheet1!A1", [(8, 0), (5, A1)]),
    ("=sheet1!B2", [(8, 0), (5, B2)]),
    ("=SHEET1!A1*2", [(8, 0), (5, A1), (1, 2), (20, 0)]),
    ("='My Sheet'!A1:B2", [(8, 1), (6, A1), (7, B2)]),
    ("='Sheet1'!A1", [(8, 0), (5, A1)]),
    ("=Data_2024!A:A", [(8, 2), (6, COL_A1), (7, COL_A2)]),
    ("='It''s'!A1", [(8, 3), (5, A1)]),
    ("=Sheet1!1:3", [(8, 0), (6, ROW_1A), (7, ROW_3B)]),
    ("=Sheet1!$A$1", [(8, 0), (5, AA1)]),
    ("=-Sheet1!A1", [(8, 0), (5, A1), (16, 0)]),
    ("=SUM(Sheet1!A1,'My Sheet'!B1)", [(8, 0), (5, A1), (8, 1), (5, B1), (SUM, 2)]),
    ("=A1 Sheet1!B1", [(5, A1), (8, 0), (5, B1), (33, 0)]),
    ("=Sheet1!A1 'My Sheet'!A1", [(8, 0), (5, A1), (8, 1), (5, A1), (33, 0)]),
    # numbers beyond 10^22 (nearest double; 15-digit truncation still applies)
    ("=1E+308", [(1, 1e308)]),
    ("=1E-200", [(1, 1e-200)]),
    ("=1.5E+300", [(1, 1.5e300)]),
    ("=1E+23", [(1, 1e23)]),
    ("=1E-23", [(1, 1e-23)]),
    ("=6.02214076E+23", [(1, 6.02214076e23)]),
    ("=123456789012345E+290", [(1, 1.23456789012345e304)]),
    ("=9.99999999999999E+307", [(1, 9.99999999999999e307)]),
    ("=1.79769313486231E+308", [(1, 1.79769313486231e308)]),
    ("=8.98846567431158E+307", [(1, 8.98846567431158e307)]),
    ("=3.14159265358979E-250", [(1, 3.14159265358979e-250)]),
    ("=2.22507385850721E-308", [(1, 2.22507385850721e-308)]),
    ("=2.2250738585072E-308", [(1, 0.0)]),        # below 2^-1022: flushed to 0 (decision P8)
    ("=1E-400", [(1, 0.0)]),
    ("=0E+500", [(1, 0.0)]),
    ("=1E+308*10", [(1, 1e308), (1, 10), (20, 0)]),
    ("=1E-200*1E-200", [(1, 1e-200), (1, 1e-200), (20, 0)]),
]


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text,expect", FORMULAS, ids=[f[0] for f in FORMULAS])
def test_formula_tokens(text, expect):
    toks, _ = formula(text)
    want = list(expect) + [(0, 0)]
    assert toks == [(o, float(v)) for o, v in want], toks


HOME = [
    # home B3 (ROW 2, COL 1): relative fields move, absolute ones do not
    ("=3:3", [(6, 171798691840), (7, 171798708223)]),     # RF = 2 + 2^20 - 2 = 2^20
    ("=A:A", [(6, 68719493119), (7, 103079198719)]),      # CF = 0 + 2^14 - 1
    ("=$A:$C", [(6, COLABS_A1), (7, COLABS_C2)]),
    ("=$1:$5", [(6, ROWABS_1A), (7, ROWABS_5B)]),
]


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text,expect", HOME, ids=[h[0] for h in HOME])
def test_home_cell(text, expect):
    toks, _ = formula(text, home=(2, 1))
    assert toks == [(o, float(v)) for o, v in list(expect) + [(0, 0)]], toks


REJECTS = ["=A:A1", "=A1:3", "=XFE:XFE", "=0:5", "=A:", "=3:", "=A:A 3:3", "=1 2", "=Nope!A1",
           "=Sheet1!foo", "=Sheet1!SUM(1)", "='My Sheet'A1", "=''!A1", "=Sheet1!", "='Sheet1",
           "=Sheet1!A1!B1", "=$A!B1", "='abcdefghijabcdefghijabcdefghijab'!A1", "=1E+309",
           "=1.79769313486232E+308", "=1,2", "=SUM(1,+)"]


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text", REJECTS)
def test_rejected(text):
    h, out, _, loc = run(text)
    assert out[12] != 0
    assert list(out[40:64]) == loc
    assert h.mem[2] == FT0, "FORMULA_TOP unchanged on reject"


@pytest.mark.skipif(PATHS is None, reason="no manifest")
def test_no_sheets_rejects_prefix():
    h, out, _, _ = run("=Sheet1!A1", sheets=[])
    assert out[12] != 0


CONSTANTS = [("1E+308", 1, 1e308), ("1e-200", 1, 1e-200), ("-2.5E+300", 1, -2.5e300),
             ("1E-400", 1, 0.0)]


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text,tag,pay", CONSTANTS, ids=[c[0] for c in CONSTANTS])
def test_constant(text, tag, pay):
    h, out, _, loc = run(text)
    assert out[12] == 0 and out[26] == 0
    assert list(out[40:64]) == loc
    assert (out[13], out[14]) == (tag, pay)


@pytest.mark.skipif(PATHS is None, reason="no manifest")
@pytest.mark.parametrize("text", ["1E+309", "1e400"])
def test_out_of_range_entry_is_text(text):
    h, out, _, _ = run(text)
    assert out[12] == 0 and out[13] == 2 and out[14] == HS


@pytest.mark.skipif(PATHS is None, reason="no manifest")
def test_step_counts_reported():
    for text in ["=A:A", "=3:3", "=SUM((A1,C1))", "=A1:C1 B1:B3", "=Sheet1!A1", "='My Sheet'!A1:B2",
                 "=1E+308", "=1E-200"]:
        _, _, steps, _ = run(text)
        print(f"steps {text!r}: {steps}")
        assert steps < 400
