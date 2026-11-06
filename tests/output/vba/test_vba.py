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


# ---------- end to end: VBA source -> lexer -> parser -> interpreter
def src(*lines):
    return "\n".join(lines) + "\n"


def test_src_precedence_assign_print():
    h, dbg, msg, err = vb.run_src(src("Sub Main()", "  x = 1 + 2 * 3", "  Debug.Print x", "End Sub"))
    assert dbg == " 7 \n" and err == 0                  # * binds tighter than +
    assert h.mem[vb.VGLOB + 6] == 2 * 13                # BCLEN: prologue 4 + 9 instructions


def test_src_for_next_dim_types():
    h, dbg, msg, err = vb.run_src(src("Sub Main()", " Dim i As Integer, s As Long", " For i = 1 To 3",
                                      "  s = s + i", " Next i", " Debug.Print s; i", "End Sub"))
    assert dbg == " 6  4 \n"                            # i is 4 after the loop; ';' joins items


def test_src_if_else_unary_not():
    h, dbg, msg, err = vb.run_src(src("Sub Main()", " x = 5", " If x > 3 Then", '  Debug.Print "big"',
                                      " Else", '  Debug.Print "small"', " End If", " If x < 3 Then",
                                      '  Debug.Print "no"', " End If",
                                      " Debug.Print -(2 + 3) * 2; Not True", "End Sub"))
    assert dbg == "big\n-10 False\n"                    # unary minus binds tighter than *


def test_src_function_sub_calls_msgbox():
    h, dbg, msg, err = vb.run_src(src("Sub Main()", ' MsgBox "x = " & Sq()', " Call Hi", " Hi", "End Sub",
                                      "Function Sq()", " Sq = 7 * 7", "End Function",
                                      "Sub Hi()", ' Debug.Print "hi"', "End Sub"))
    assert msg == "x = 49\n" and dbg == "hi\nhi\n"     # calls may precede definitions


def test_src_nested_for_if_step():
    h, dbg, msg, err = vb.run_src(src("Sub Main()", " For i = 1 To 2", "  For j = 1 To 2 Step 1",
                                      "   If i = j Then", "    Debug.Print i * 10 + j", "   End If",
                                      "  Next j", " Next i", " Dim s As String", ' Debug.Print s & "|"',
                                      " For k = 3 To 1 Step -1", "  Debug.Print k;", " Next",
                                      " Debug.Print", "End Sub"))
    assert dbg == " 11 \n 22 \n|\n 3  2  1 \n"         # String Dim starts as ""; bare Print ends the line


def test_src_integer_overflow():
    h, dbg, msg, err = vb.run_src(src("Sub Main()", " Dim n As Integer", " n = 30000 + 30000",
                                      " Debug.Print n", "End Sub"))
    assert err == 6 and dbg == ""                       # Integer + Integer overflows: error 6


# ---------- vi_div (434): / \ Mod ^ (expected values from VBA's documented rules)
def binop(a, b, op):
    h, dbg, msg, err = vb.run(PRO + [a, b, (op, 0), PRINT, RET], ENTRY)
    return dbg, err


@pytest.mark.parametrize("a, b, op, want", [
    (D(7), D(2), 19, (" 3.5 \n", 0)),
    (D(1), D(3), 19, (" 0.333333333333333 \n", 0)),      # Print shows 15 significant digits
    (I(1), I(0), 19, ("", 11)),                            # x / 0: division by zero
    (I(0), I(0), 19, ("", 6)),                             # 0 / 0: VBA reports overflow
    (D(1e308), D(1e-10), 19, ("", 6)),                     # Double overflow
    (I(7), I(2), 20, (" 3 \n", 0)),                        # \ truncates toward zero
    (I(-7), I(2), 20, ("-3 \n", 0)),
    (I(7), I(-2), 20, ("-3 \n", 0)),
    (D(2.5), I(1), 20, (" 2 \n", 0)),                      # operands rounded half to even first
    (I(-32768), I(-1), 20, ("", 6)),                       # Integer \ Integer result 32768 overflows
    (L(-32768), I(-1), 20, (" 32768 \n", 0)),              # Long rank: fits
    (D(1e300), I(2), 20, ("", 6)),                         # operand outside Long
    (I(7), I(2), 21, (" 1 \n", 0)),
    (I(-7), I(2), 21, ("-1 \n", 0)),                       # Mod takes the sign of the dividend
    (I(7), I(-2), 21, (" 1 \n", 0)),
    (D(5.5), D(2), 21, (" 0 \n", 0)),                      # 6 Mod 2
    (I(5), D(0.3), 21, ("", 11)),                          # divisor rounds to 0
    (I(2), I(10), 22, (" 1024 \n", 0)),
    (I(0), I(0), 22, (" 1 \n", 0)),                        # VBA: 0 ^ 0 = 1
    (D(-8), D(1 / 3), 22, ("", 5)),                        # negative base, fractional exponent
])
def test_div_family(a, b, op, want):
    assert binop(a, b, op) == want


def test_src_div_mod_pow():
    h, dbg, msg, err = vb.run_src(src("Sub Main()",
                                      " Debug.Print 7 \\ 2; -7 Mod 3; 2 ^ 10; 1 / 4; 4 / 2 ^ 2; 2 ^ 3 ^ 2",
                                      " Dim n As Long", " n = 2147483647", " Debug.Print n \\ -1; 10 Mod 4 * 2",
                                      "End Sub"))
    # ^ is left associative ((2^3)^2 = 64); * binds tighter than Mod (10 Mod 8)
    assert dbg == " 3 -1  1024  0.25  1  64 \n-2147483647  2 \n" and err == 0


# ---------- vi_scmp (433) / vi_scl (447): string comparison, Option Compare Binary
@pytest.mark.parametrize("a, b, want", [
    ("abc", "abd", "FalseTrueTrueTrueFalseFalse"),      # = <> < <= > >=: first difference decides
    ("abc", "abc", "TrueFalseFalseTrueFalseTrue"),
    ("ab", "abc", "FalseTrueTrueTrueFalseFalse"),       # a proper prefix is smaller
    ("abc", "ab", "FalseTrueFalseFalseTrueTrue"),
    ("", "", "TrueFalseFalseTrueFalseTrue"),
    ("Z", "a", "FalseTrueTrueTrueFalseFalse"),          # binary: code 90 < 97
    ("abcdefghij", "abcdefghik", "FalseTrueTrueTrueFalseFalse"),   # difference in the second block of 8
    ("abcdefgh", "abcdefghi", "FalseTrueTrueTrueFalseFalse"),      # a ends exactly at a block edge
    ("abcdefghijklmnopq", "abcdefghijklmnopq", "TrueFalseFalseTrueFalseTrue"),
])
def test_src_string_compare(a, b, want):
    qa, qb = '"' + a + '"', '"' + b + '"'
    line = " Debug.Print " + "; ".join(qa + " " + op + " " + qb for op in ("=", "<>", "<", "<=", ">", ">="))
    h, dbg, msg, err = vb.run_src(src("Sub Main()", line, "End Sub"), max_steps=1000000)
    assert dbg == want + "\n" and err == 0


def test_src_string_compare_empty_and_mismatch():
    h, dbg, msg, err = vb.run_src(src("Sub Main()", " Dim s As String", ' Debug.Print s = ""; s < "a"',
                                      "End Sub"))
    assert dbg == "TrueTrue\n"                          # a String Dim starts as ""
    h, dbg, msg, err = vb.run_src(src("Sub Main()", ' Debug.Print "abc" = 5', "End Sub"))
    assert err == 13                                    # non-numeric string vs number: type mismatch
