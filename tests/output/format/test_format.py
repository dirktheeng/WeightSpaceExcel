"""Format engine output tests. Expected strings are stated by hand from Excel's documented
behaviour (docs/PARITY.md, Microsoft number format documentation)."""
import pytest

import fmtbb as f

# ---- fx_dec (192): x -> s, e, m (15 significant digits)
DEC = [
    (1.0, 0, 0, 100000000000000),
    (-123.456, 1, 2, 123456000000000),
    (0.001, 0, -3, 100000000000000),
    (1e300, 0, 300, 100000000000000),
    (1e-300, 0, -300, 100000000000000),
    (1 / 3, 0, -1, 333333333333333),
    (2 / 3, 0, -1, 666666666666667),
    (1.7976931348623157e308, 0, 308, 179769313486232),
    (0.0, 0, 0, 0),
    (9.999999999999999, 0, 1, 100000000000000),
    (1e16, 0, 16, 100000000000000),
    (12345678901234567890.0, 0, 19, 123456789012346),
    (99999999999999.5, 0, 13, 999999999999995),
    (5e-5, 0, -5, 500000000000000),
    (-0.1, 1, -1, 100000000000000),
]


@pytest.mark.parametrize("x,s,e,m", DEC)
def test_fx_dec(x, s, e, m):
    h = f.harness()
    out = h.run(192, f.regs(APAY=x, T10=f.HALT_OK), max_steps=5)
    assert (f.reg(out, "AS"), f.reg(out, "AR1"), f.reg(out, "AC1")) == (s, e, m)


def test_fx_dec_scale():
    h = f.harness()
    out = h.run(192, f.regs(APAY=0.25, T2=2, T10=f.HALT_OK), max_steps=5)
    assert (f.reg(out, "AR1"), f.reg(out, "AC1")) == (1, 250000000000000)
    out = h.run(192, f.regs(APAY=0.0, T2=2, T10=f.HALT_OK), max_steps=5)
    assert f.reg(out, "AR1") == 0


# ---- fx_dec -> fx_rnd (193): (x, k, nint, sci) -> M, R, X
RND = [
    (1.005, 2, 1, 0, 101000000000000, 1),
    (0.96, 1, 1, 0, 100000000000000, 1),
    (0.096, 1, 1, 0, 100000000000000, 0),
    (1234.5678, 2, 1, 0, 123457000000000, 4),
    (0.001234, 5, 1, 0, 1230000000000, 0),
    (0.4, 0, 1, 0, 0, 0),
    (0.5, 0, 1, 0, 100000000000000, 1),
    (9.96, 1, 1, 0, 100000000000000, 2),
    (0.0, 2, 1, 0, 0, 0),
    (12345678901234567890.0, 2, 1, 0, 123456789012346, 20),
    (-2.5, 0, 1, 0, 300000000000000, 1),
]


@pytest.mark.parametrize("x,k,nint,sci,M,R", RND)
def test_fx_rnd_fixed(x, k, nint, sci, M, R):
    h = f.harness()
    out = h.run(192, f.regs(APAY=x, AC2=k, N0=nint, N1=sci, T10=193, T9=f.HALT_OK), max_steps=5)
    assert (f.reg(out, "AC1"), f.reg(out, "AR2")) == (M, R)


SCI = [
    (12345, 2, 1, 123000000000000, 1, 4),
    (99999, 2, 1, 100000000000000, 1, 5),
    (0.000123456, 3, 1, 123500000000000, 1, -4),
    (0.0, 2, 1, 0, 1, 0),
    (12345, 1, 3, 123500000000000, 3, 2),
]


@pytest.mark.parametrize("x,k,nint,M,R,X", SCI)
def test_fx_rnd_sci(x, k, nint, M, R, X):
    h = f.harness()
    out = h.run(192, f.regs(APAY=x, AC2=k, N0=nint, N1=1, T10=193, T9=f.HALT_OK), max_steps=5)
    assert (f.reg(out, "AC1"), f.reg(out, "AR2"), f.reg(out, "AS2")) == (M, R, X)


# ---- emitter: fx_dec -> fx_rnd -> fx_fetch -> executors, buffer at FMT_BUF
FMT_BUF = 0xC800
TOK = 0xD000


def tok(code, arg=0):
    return (code, arg)


def put_tokens(h, addr, toks):
    """Token word = arg + 65536 code + 2^20 (code of the next token) (weights/format/fx_emit.md)."""
    codes = [c for c, _ in toks]
    for i, (c, a) in enumerate(toks):
        nc = codes[i + 1] if i + 1 < len(toks) else 0
        h.mem[addr + i] = a + 65536 * c + 2**20 * nc
    return codes[0]


def buf(h, start, end):
    return "".join(chr(int(h.mem[a])) for a in range(start, end))


def run_emit(x, toks, k, nint, th=0, sci=0):
    h = f.harness()
    nexp = sum(1 for c, _ in toks if c == 7)
    nc0 = put_tokens(h, TOK, toks)
    out = h.run(192, f.regs(APAY=x, AC2=k, N0=nint, N1=sci, T1=th, T10=193, T9=194, P0=TOK,
                            P1=FMT_BUF, T8=nc0, T3=nexp, LR=f.HALT_OK), max_steps=2000)
    # the emitted buffer runs from FMT_BUF to the first 0 (fresh memory)
    n = 0
    while h.mem[FMT_BUF + n] != 0:
        n += 1
    return buf(h, FMT_BUF, FMT_BUF + n)


def I(j, t):
    """integer placeholder, j = index from the left"""
    return (2, 4 * j + t)


def F(j, t):
    return (5, 4 * j + t)


P = (3, 0)
END = (0, 0)
EMIT = [
    (1234.567, [I(0, 0), P, F(1, 0), F(2, 0), END], 2, 1, 0, "1234.57"),
    (1234567.891, [I(0, 1), I(1, 1), I(2, 1), I(3, 0), P, F(1, 0), F(2, 0), END], 2, 4, 1, "1,234,567.89"),
    (5, [I(0, 0), I(1, 0), I(2, 0), I(3, 0), END], 0, 4, 1, "0,005"),
    (5, [I(0, 1), I(1, 1), I(2, 1), I(3, 0), END], 0, 4, 1, "5"),
    (0.5, [I(0, 1), P, F(1, 1), F(2, 1), END], 2, 1, 0, ".5"),
    (0.5, [I(0, 0), P, F(1, 0), F(2, 1), END], 2, 1, 0, "0.5"),
    (3, [I(0, 1), P, F(1, 1), F(2, 1), END], 2, 1, 0, "3."),
    (1.5, [I(0, 0), P, F(1, 2), F(2, 2), END], 2, 1, 0, "1.5 "),
    (12.345, [P, F(1, 0), F(2, 0), END], 2, 0, 0, "12.35"),
    (7, [(1, ord("$")), I(0, 0), (1, ord("x")), END], 0, 1, 0, "$7x"),
    (1234, [I(0, 2), I(0, 0), END][1:], 0, 1, 1, "1,234"),
]


@pytest.mark.parametrize("x,toks,k,nint,th,text", EMIT)
def test_emit(x, toks, k, nint, th, text):
    assert run_emit(x, toks, k, nint, th) == text


def ED(j, t):
    return (7, 4 * j + t)


SCI_EMIT = [
    (12345, [I(0, 0), P, F(1, 0), F(2, 0), (6, 0), ED(0, 0), ED(1, 0), END], 2, 1, "1.23E+04"),
    (0.000123456, [I(0, 0), P, F(1, 0), F(2, 0), (6, 0), ED(0, 0), ED(1, 0), END], 2, 1, "1.23E-04"),
    (1.5e300, [I(0, 0), P, F(1, 0), (6, 0), ED(0, 0), ED(1, 0), END], 1, 1, "1.5E+300"),
    (12345, [I(0, 0), P, F(1, 0), (6, 1), ED(0, 0), END], 1, 1, "1.2E4"),
    (0.012, [I(0, 0), P, F(1, 0), (6, 3), ED(0, 0), END], 1, 1, "1.2e-2"),
    (0.0, [I(0, 0), P, F(1, 0), F(2, 0), (6, 0), ED(0, 0), ED(1, 0), END], 2, 1, "0.00E+00"),
    pytest.param(12345, [I(0, 1), I(1, 1), I(2, 0), P, F(1, 0), (6, 0), ED(0, 0), END], 1, 3, "12.3E+3",
                 marks=pytest.mark.xfail(reason="engineering exponent (multiple of nint) not done")),
    (99999, [I(0, 0), P, F(1, 0), (6, 0), ED(0, 0), ED(1, 0), END], 1, 1, "1.0E+05"),
]


@pytest.mark.parametrize("x,toks,k,nint,text", SCI_EMIT)
def test_emit_sci(x, toks, k, nint, text):
    assert run_emit(x, toks, k, nint, 0, sci=1) == text


# ---- full emit + finish: heap string at HEAP_TOP (zero page 1), returns to LR
HEAP0 = 0x302002


def run_full(x, toks, k, nint, th=0, sci=0, W=0, kind=0, h=None):
    h = h or f.harness()
    if h.mem[1] == 0:
        h.mem[1] = HEAP0
    nc0 = put_tokens(h, TOK, toks)
    nexp = sum(1 for c, _ in toks if c == 7)
    out = h.run(192, f.regs(T3=nexp, APAY=x, BPAY=W, AC2=k, N0=nint, N1=sci, T1=th, T4=kind, T10=193, T9=194,
                            P0=TOK, P1=FMT_BUF, T8=nc0, LR=f.HALT_OK), max_steps=5000)
    assert f.reg(out, "ATAG") == 2
    return f.get_str(h, int(f.reg(out, "APAY"))), h


FULL = [
    (1234.567, [I(0, 0), P, F(1, 0), F(2, 0), END], 2, 1, 0, 0, "1234.57"),
    (1234.567, [I(0, 0), P, F(1, 0), F(2, 0), END], 2, 1, 0, 6, "######"),
    (1234.567, [I(0, 0), P, F(1, 0), F(2, 0), END], 2, 1, 0, 7, "1234.57"),
    (5, [(9, ord("-")), I(0, 0), END], 0, 1, 0, 6, "-----5"),
    (5, [(1, ord("$")), (9, ord(" ")), I(0, 0), END], 0, 1, 0, 8, "$      5"),
    (5, [(1, ord("$")), (9, ord(" ")), I(0, 0), END], 0, 1, 0, 0, "$5"),
    (0, [I(0, 1), END], 0, 1, 0, 0, ""),
    (42, [I(0, 0), END], 0, 1, 0, 2, "42"),
]


@pytest.mark.parametrize("x,toks,k,nint,th,W,text", FULL)
def test_full(x, toks, k, nint, th, W, text):
    assert run_full(x, toks, k, nint, th, W=W)[0] == text


def test_heap_top_advances():
    s1, h = run_full(1234.567, [I(0, 0), P, F(1, 0), F(2, 0), END], 2, 1)
    assert h.mem[1] == HEAP0 + 2 + 3
    s2, h = run_full(-0.5, [I(0, 0), P, F(1, 0), END], 1, 1, h=h)
    assert s2 == "0.5" and h.mem[1] == HEAP0 + 2 + 3 + 2 + 1


# ---- General (fx_init 199 once, then fx_dec -> fx_gen 196 -> fx_rnd -> fx_gen2 197 -> emit -> finish)
def general(x, W=0, h=None):
    h = h or f.harness()
    h.mem[1] = h.mem[1] or HEAP0
    h.run(199, f.regs(LR=f.HALT_OK), max_steps=5)
    out = h.run(192, f.regs(APAY=x, ATAG=1, BPAY=W, T10=196, P1=FMT_BUF, LR=f.HALT_OK), max_steps=5000)
    return f.get_str(h, int(f.reg(out, "APAY")))


GENERAL = [
    # TEXT(x, "General") behaviour: up to 11 characters
    (0, 0, "0"), (1, 0, "1"), (-1, 0, "-1"), (0.5, 0, "0.5"), (1 / 3, 0, "0.333333333"),
    (2 / 3, 0, "0.666666667"), (-1 / 3, 0, "-0.33333333"), (123456.123456, 0, "123456.1235"),
    (12345678901, 0, "12345678901"), (123456789012, 0, "1.23457E+11"), (-123456789012, 0, "-1.2346E+11"),
    (1e15, 0, "1E+15"), (1e100, 0, "1E+100"), (1.5e-10, 0, "1.5E-10"), (0.0001, 0, "0.0001"),
    (0.00001, 0, "0.00001"), (0.0000123456789, 0, "1.23457E-05"), (0.000123456789, 0, "0.000123457"),
    (99999999999.7, 0, "1E+11"), (1234.5, 0, "1234.5"), (0.1 + 0.2, 0, "0.3"), (1e-300, 0, "1E-300"),
    (100, 0, "100"), (12345678901234567890.0, 0, "1.23457E+19"),
    # column width (characters)
    (1 / 3, 8, "0.333333"), (123456789, 8, "1.23E+08"), (1234.5678, 6, "1234.6"), (12345, 5, "12345"),
    (123456, 5, "1E+05"), (123456, 3, "###"), (-0.5, 4, "-0.5"), (1234567, 7, "1234567"),
]


@pytest.mark.parametrize("x,W,text", GENERAL)
def test_general(x, W, text):
    assert general(x, W) == text


# ---- compiler (fc_start 223 .. fc_char 220 / fc_send 222): record layout in weights/format/README.md
CODE = 0x302100
FT = 0xC000
CR0 = 0xCA00


def compile_code(code, F=170, h=None):
    h = h or f.harness()
    f.put_str(h, CODE, code)
    h.mem[FT + 4 * F] = CODE
    x = f.regs(BTAG=F, LR=f.HALT_OK)
    x[0] = CODE
    try:
        h.run(223, x, max_steps=20000)
    except Exception:
        pass
    return h


def decode_record(h, cr):
    nsec = int(h.mem[cr])
    secs = []
    for i in range(nsec):
        sh = int(h.mem[cr + 5 + i])
        hdr = [int(v) for v in h.mem[sh:sh + 9]]
        toks = []
        a = sh + 9
        while True:
            w = int(h.mem[a])
            if w == 0:
                break
            toks.append(((w >> 16) & 15, w & 65535, w >> 20))
            a += 1
        secs.append((hdr, toks))
    return nsec, secs, [h.mem[cr + i] for i in range(1, 5)], int(h.mem[cr + 8])


def test_compile_number():
    h = compile_code("#,##0.00")
    assert h.mem[FT + 4 * 170 + 1] == CR0
    nsec, secs, conds, tsec = decode_record(h, CR0)
    assert nsec == 1
    hdr, toks = secs[0]
    assert hdr == [0, 0, 2, 4, 1, 0, 0, 0, 2]
    assert [(c, a) for c, a, _ in toks] == [(2, 1), (2, 5), (2, 9), (2, 12), (3, 0), (5, 4), (5, 8)]
    assert [n for _, _, n in toks] == [2, 2, 2, 3, 5, 5, 0]
    assert h.mem[0xC003] == CR0 + 9 + 9 + 7 + 1


def toks_of(secs, i):
    return [(c, a) for c, a, _ in secs[i][1]]


L = lambda ch: (1, ord(ch))  # noqa: E731


COMPILE = [
    ("0.0%", 1, [([0, 0, 1, 1, 0, 2, 0, 0, 2], [(2, 0), (3, 0), (5, 4), L("%")])]),
    ("0.00E+00", 1, [([0, 0, 2, 1, 0, 0, 1, 2, 2], [(2, 0), (3, 0), (5, 4), (5, 8), (6, 0), (7, 0), (7, 4)])]),
    ("0.0e-0", 1, [([0, 0, 1, 1, 0, 0, 1, 1, 2], [(2, 0), (3, 0), (5, 4), (6, 3), (7, 0)])]),
    ('"$"#,##0_);\\("$"#,##0\\)', 2,
     [([0, 0, 0, 4, 1, 0, 0, 0, 1], [L("$"), (2, 1), (2, 5), (2, 9), (2, 12), L(" ")]),
      ([0, 0, 0, 4, 1, 0, 0, 0, 1], [L("("), L("$"), (2, 1), (2, 5), (2, 9), (2, 12), L(")")])]),
    ("0,,", 1, [([0, 0, 0, 1, 0, -6, 0, 0, 2], [(2, 0)])]),
    ("#,##0,", 1, [([0, 0, 0, 4, 1, -3, 0, 0, 2], [(2, 1), (2, 5), (2, 9), (2, 12)])]),
    ("*-0;;", 3, [([0, 0, 0, 1, 0, 0, 0, 0, 9], [(9, ord("-")), (2, 0)]), ([0] * 9, []), ([0] * 9, [])]),
    ("0 ?/x", 1, [([0, 0, 0, 2, 0, 0, 0, 0, 2], [(2, 0), L(" "), (2, 6), L("/"), L("x")])]),
]


@pytest.mark.parametrize("code,nsec,want", COMPILE)
def test_compile(code, nsec, want):
    h = compile_code(code)
    n, secs, conds, tsec = decode_record(h, CR0)
    assert n == nsec
    for i, (hdr, toks) in enumerate(want):
        assert secs[i][0] == hdr
        assert toks_of(secs, i) == toks


def test_compile_text_section():
    h = compile_code("0.00;-0.00;0;[Red]@")
    n, secs, conds, tsec = decode_record(h, CR0)
    assert n == 4 and tsec == int(h.mem[CR0 + 8])
    h = compile_code("@")
    n, secs, conds, tsec = decode_record(h, CR0)
    assert n == 1 and tsec == int(h.mem[CR0 + 5]) and secs[0][0][0] == 2 and toks_of(secs, 0) == [(8, 0)]


# ---- full engine: fx_main (198) with a format id whose code string is in FMT_TABLE
def fmt(x, code, W=0, F=170, h=None, tag=1):
    h = h or f.harness()
    h.mem[1] = h.mem[1] or HEAP0
    if h.mem[FT + 4 * F] == 0:
        f.put_str(h, CODE + 64 * (F - 160), code)
        h.mem[FT + 4 * F] = CODE + 64 * (F - 160)
    out = h.run(198, f.regs(ATAG=tag, APAY=x, BTAG=F, BPAY=W, LR=f.HALT_OK), max_steps=20000)
    return f.get_str(h, int(f.reg(out, "APAY"))), int(f.reg(out, "CTAG")), int(f.reg(out, "CPAY")), h


CUSTOM = [
    (1234567.891, "#,##0.00", "1,234,567.89"), (-1234.5, "#,##0.00", "-1,234.50"),
    (0.5, "#,##0.00", "0.50"), (-3.14159, "0.00;(0.00)", "(3.14)"), (2, "0.00;(0.00)", "2.00"),
    (0, '0.00;-0.00;"zero"', "zero"), (-0.001, '0.00;-0.00;"zero"', "-0.00"), (0.256, "0%", "26%"),
    (0.256, "0.0%", "25.6%"), (12345, "0.00E+00", "1.23E+04"), (-1234, '"$"#,##0_);\\("$"#,##0\\)', "($1,234)"),
    (1234, '"$"#,##0_);\\("$"#,##0\\)', "$1,234 "), (1234567, "#,##0,", "1,235"), (123456789, "0,,", "123"),
    (42, "000000", "000042"),
    pytest.param(3.5, "# ??/??", "3  1/2", marks=pytest.mark.xfail(reason="fractions not done")), (7, "\\A0\\B", "A7B"), (-7, "0;;", ""),
    (0, "0;-0;;@", ""), (5, ";;;", ""), (1.25, "#.##", "1.25"), (0.25, "#.##", ".25"), (12, "#.##", "12."),
]


@pytest.mark.parametrize("x,code,text", CUSTOM)
def test_custom(x, code, text):
    assert fmt(x, code)[0] == text


BRACKET = [
    (5, "[Red]0.00;[Blue]-0.00", "5.00", 6), (-5, "[Red]0.00;[Blue]-0.00", "-5.00", 2),
    (150, "[>100]0;[<50]0.0;0.00", "150", 0), (20, "[>100]0;[<50]0.0;0.00", "20.0", 0),
    (75, "[>100]0;[<50]0.0;0.00", "75.00", 0), (3, "[Color10]0", "3", 19), (1.5, "[$-409]0.00", "1.50", 0),
    (7, "[green][=7]0\"!\";0", "7!", 4), (8, "[green][=7]0\"!\";0", "8", 0), (-8, "[MAGENTA]0", "-8", 5),
    (100, "[>=100]\"big\";\"small\"", "big", 0), (99, "[>=100]\"big\";\"small\"", "small", 0),
    (1, "[<>1]\"x\";\"one\"", "one", 0), (2, "[<>1]\"x\";\"one\"", "x", 0),
]


@pytest.mark.parametrize("x,code,text,color", BRACKET)
def test_brackets(x, code, text, color):
    s, c, a, _ = fmt(x, code)
    assert (s, c, a) == (text, color, 3)


def test_compiled_once_and_reused():
    s, c, a, h = fmt(1234.5, "#,##0.0")
    top = h.mem[0xC003]
    s2, c2, a2, h = fmt(-2, "#,##0.0", h=h)
    assert (s, s2) == ("1,234.5", "-2.0") and h.mem[0xC003] == top


def test_text_value_shown_as_is():
    h = f.harness()
    f.put_str(h, 0x302300, "abc")
    s, c, a, h = fmt(0x302300, "0.00", tag=2, h=h)
    assert (s, a) == ("abc", 1)
