"""Output tests for the VBA groundwork (weights/vba). Expected values are stated by hand from
VBA's documented behaviour (comments give the reason). Black box: no weight file is read."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vbabb as vb  # noqa: E402

P48 = 2 ** 48
B = vb.BC
PRO = [(64, 0), (64, 0), (7, 0), (0, 0)]          # PUSH Empty x2, CALL 0, END
ENTRY = [(0, B + 8, 1, 0)]                          # proc 0 starts after the prologue, 1 slot
I = lambda v: (82, v)   # noqa: E731  PUSH Integer
L = lambda v: (83, v)   # noqa: E731  PUSH Long
D = lambda v: (85, v)   # noqa: E731  PUSH Double
T = lambda v: (91, v)   # noqa: E731  PUSH Boolean
PRINT, MSGBOX, POP, RET = (9, 0), (10, 0), (6, 0), (8, 0)


def prints(*items):
    body = []
    for it in items:
        body += list(it) + [PRINT]
    return vb.run(PRO + body + [RET], ENTRY)


# ---------- lexer: VBA source as test data
def test_lex_keywords_idents_ops():
    h, t = vb.lex("Sub Main()\n  Dim x As Integer: x = y Mod z And Not True\nEnd Sub\n"
                  "Function F2(a_b)\nRem hi\nEnd Function\n")
    x, y, z = 24 + P48, 25 + P48, 26 + P48           # one letter: KEY = letter value, LEN 1
    main = (((13 * 64 + 1) * 64 + 9) * 64 + 14) + 4 * P48
    assert t == [(64, 0), (2, main), (10, 0), (11, 0), (1, 0),
                 (67, 0), (2, x), (68, 0), (91, 0), (1, 0),
                 (2, x), (24, 7), (2, y), (21, 10), (2, z), (30, 5), (41, 6), (8, -1), (1, 0),
                 (66, 0), (64, 0), (1, 0),
                 (65, 0), (2, (6 * 64 + 29) + 2 * P48), (10, 0),
                 (2, ((1 * 64 + 37) * 64 + 2) + 3 * P48), (11, 0), (1, 0),
                 (1, 0), (66, 0), (65, 0), (1, 0), (0, 0)]
    assert h.mem[vb.VGLOB + 4] == 2                    # Main and F2 registered
    assert h.mem[vb.PROCT] == main and h.mem[vb.PROCT + 4] == (6 * 64 + 29) + 2 * P48


def test_lex_punct_comment_continuation():
    h, t = vb.lex("( ) + -*/\\ ^&=,;.:\n'x\n_\n:")
    assert t == [(10, 0), (11, 0), (16, 9), (17, 9), (18, 12), (19, 12), (20, 11), (22, 14),
                 (23, 8), (24, 7), (12, 0), (13, 0), (14, 0), (1, 0), (1, 0), (1, 0), (1, 0),
                 (0, 0)]


@pytest.mark.parametrize("src,tok", [
    ("5", (3, 5)), ("40000", (4, 40000)), ("3000000000", (5, 3e9)),   # Integer, Long, Double by size
    ("2.5", (5, 2.5)), ("1E3", (5, 1000)), ("1.5D-2", (5, 0.015)), ("1.5E+2", (5, 150)),
    ("7#", (5, 7)), ("3%", (3, 3)), ("9&", (4, 9)), ("0.001", (5, 0.001)), ("007", (3, 7)),
    ("12345678901234567", (5, 12345678901234500)),                    # 15 significant digits kept
])
def test_lex_numbers(src, tok):
    h, t = vb.lex(src + "\n")
    assert t[0] == tok and t[1] == (1, 0)


@pytest.mark.parametrize("src,serial", [
    ("#1/2/2000#", 36527), ("#12/31/1999#", 36525), ("#1/1/1900#", 2),  # VBA: 12/30/1899 is 0
    ("#3/1/1900#", 61), ("#2/29/2024#", 45351)])
def test_lex_dates(src, serial):
    h, t = vb.lex("d = " + src + "\n")
    assert t[2] == (7, serial)


def test_lex_strings_and_compare_ops():
    h, t = vb.lex('s = "Hi ""you""" & "" : If a <> b Or a <= b Or a >= c Or a < 1 Or a > 2 Or a=b Then\n')
    assert [k for k, v in t] == [2, 24, 6, 23, 6, 1, 69, 2, 25, 2, 31, 2, 27, 2, 31, 2, 29, 2, 31,
                                 2, 26, 3, 31, 2, 28, 3, 31, 2, 24, 2, 70, 1, 0]
    assert vb.vstr(h, int(t[2][1])) == 'Hi "you"' and vb.vstr(h, int(t[4][1])) == ""


# ---------- interpreter: hand-assembled bytecode (the parser is not built yet)
def test_print_formats():
    h, dbg, msg, err = prints([I(5)], [I(-3)], [T(-1)], [D(2.5)], [D(1 / 3)], [L(-123456)])
    # Print puts a sign space before non-negative numbers and a space after every number
    assert dbg == " 5 \n-3 \nTrue\n 2.5 \n 0.333333333333333 \n-123456 \n" and err == 0


@pytest.mark.parametrize("a,b,op,out", [
    (I(2), I(3), 16, " 5 "), (I(2), I(3), 17, "-1 "), (I(6), I(7), 18, " 42 "),
    (L(30000), I(30000), 16, " 60000 "), (D(0.1), D(0.2), 16, " 0.3 "),
    (I(3), I(5), 26, "True"), (I(3), I(5), 24, "False"), (I(5), I(5), 27, "True"),
    (T(-1), T(0), 30, "False"), (T(-1), T(0), 31, "True"), (T(-1), T(-1), 32, "False"),
    (D(2.5), D(1.5), 29, "True"), (I(4), I(4), 25, "False")])
def test_binary(a, b, op, out):
    h, dbg, msg, err = vb.run(PRO + [a, b, (op, 0), PRINT, RET], ENTRY)
    assert (dbg, err) == (out + "\n", 0)


@pytest.mark.parametrize("v,op,out", [(I(7), 40, "-7 "), (T(-1), 41, "False"), (I(5), 41, "-6 "),
                                      (D(2.5), 41, "-3 ")])   # Not 2.5 = Not CLng(2.5) = Not 2
def test_unary(v, op, out):
    h, dbg, msg, err = vb.run(PRO + [v, (op, 0), PRINT, RET], ENTRY)
    assert dbg == out + "\n"


@pytest.mark.parametrize("prog,err", [
    ([I(30000), I(30000), (16, 0)], 6),       # Integer overflow
    ([I(0), I(-32768), (40, 0)], 6),          # -(-32768) overflows Integer
    ([D(1e308), D(1e308), (16, 0)], 6), ([D(1e200), D(1e200), (18, 0)], 6),
    ([I(1), (88, vb.VSTR0 - 1), (16, 0)], 13),  # Integer + String (no coercion yet)
    ([D(40000), (5, 1 + 4096 * 2)], 6),       # store 40000 into an Integer
])
def test_errors(prog, err):
    h, dbg, msg, e = vb.run(PRO + prog + [RET], ENTRY)
    assert e == err


def test_store_coercion():
    # Integer <- 2.5 is 2, Long <- 3.5 is 4 (banker's rounding), Boolean <- 5 is True
    body = [D(2.5), (5, 1 + 4096 * 2), D(3.5), (5, 2 + 4096 * 3), I(5), (5, 3 + 4096 * 11),
            (4, 1), PRINT, (4, 2), PRINT, (4, 3), PRINT, RET]
    h, dbg, msg, err = vb.run(PRO + body, [(0, B + 8, 4, 0)])
    assert dbg == " 2 \n 4 \nTrue\n"


def test_for_loop_in_called_proc():
    # For i = 1 To 3: s = s + i: Next: Debug.Print s; i   (slots: 1 i, 2 s, 3 limit, 4 step)
    body = [I(0), (5, 2), I(1), (5, 1), I(3), (5, 3), I(1), (5, 4),
            (4, 1), (4, 3), (4, 4), (11, 0), (2, B + 52),
            (4, 2), (4, 1), (16, 0), (5, 2), (4, 1), (4, 4), (16, 0), (5, 1), (1, B + 24),
            (4, 2), (9, 1), (4, 1), PRINT, RET]
    h, dbg, msg, err = vb.run(PRO + body, [(0, B + 8, 5, 0)])
    assert dbg == " 6  4 \n"


def test_strings_concat_msgbox():
    H = vb.VSTR0
    body = [(88, H), I(5), (23, 0), PRINT, T(-1), (88, H + 5), (23, 0), PRINT,
            (88, H), (88, H + 5), (16, 0), MSGBOX, POP, D(2.5), I(-7), (23, 0), PRINT,
            D(1e15), MSGBOX, PRINT, RET]
    h, dbg, msg, err = vb.run(PRO + body, ENTRY, strings=["x = ", "abc"])
    assert dbg == "x = 5\nTrueabc\n2.5-7\n 1 \n"     # MsgBox returns vbOK = 1
    assert msg == "x = abc\n1E+15\n"


def test_function_call_returns_value():
    # Function Sq(n): Sq = n * n: End Function; Main: Debug.Print Sq(7)
    sq = 0x390040
    main = [(64, 0), (64, 0), I(7), (7, 1), PRINT, RET]
    body = main + [(0, 0)] * ((sq - (B + 8)) // 2 - len(main)) + [(4, 1), (4, 1), (18, 0), (5, 0), RET]
    h, dbg, msg, err = vb.run(PRO + body, [(0, B + 8, 1, 0), (0, sq, 2, 1)])
    assert dbg == " 49 \n" and err == 0
