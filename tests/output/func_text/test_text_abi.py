"""ABI-level output tests for the Text functions (encodings/functions.md sections 2 and 6).

The manifest is booted with FN_RET (257) replaced by kernel/halt_ok (tests/output/func_logic/lgbb.py),
then tx_w0 (319) is entered at PC 0 as FN_CALL would, with the arguments on the operand stack and the
last in B. Strings are placed in the text heap by the documented layout; cells by CELL_SET. Expected
values are stated by hand from Excel's documented behaviour. Weight files are never opened.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "func_logic"))
sys.path.insert(0, os.path.dirname(HERE))
import lgbb  # noqa: E402
from blackbox import text_at  # noqa: E402

W0 = 319
TEXT_EMPTY = 0x302000
HT0 = 0x320000
FID = {"LEN": 279, "LENB": 280, "CODE": 69, "UNICODE": 487, "UPPER": 489, "LOWER": 292,
       "EXACT": 158, "MID": 302, "MIDB": 303, "LEFT": 277, "LEFTB": 278, "RIGHT": 397,
       "RIGHTB": 398, "CHAR": 56, "UNICHAR": 486, "T": 451}

_abi = None


class TextAbi(lgbb.Abi):
    """lgbb.Abi with a boot step budget large enough for the current boot chain (FT_INIT)."""

    def __init__(self):
        import numpy as np
        from harness.harness import Harness
        paths = list(lgbb.bb.manifest_paths())
        paths[lgbb.FN_RET] = lgbb.HALT
        self.h = Harness(paths)
        self.h.run(0, np.zeros(65), max_steps=200000)


def abi():
    global _abi
    if _abi is None:
        _abi = TextAbi()
    return _abi


class Heap:
    def __init__(self, h):
        self.h, self.at = h, 0x310000

    def s(self, text):
        if text == "":
            return (2, TEXT_EMPTY)
        b = text.encode("utf-16-le")
        u = [b[i] + 256 * b[i + 1] for i in range(0, len(b), 2)]
        a = self.at
        self.h.mem[a], self.h.mem[a + 1] = len(u), 1
        for j in range(0, len(u), 3):
            c = (u[j:j + 3] + [0, 0])[:3]
            self.h.mem[a + 2 + j // 3] = c[0] + c[1] * 2**16 + c[2] * 2**32
        self.at += 2 + (len(u) + 2) // 3
        return (2, a)


def run(name, *args, cells=None):
    """args: python values (str, float, bool, None blank, 'MISS', ('err', code), ('ref', 'A1'))."""
    ab = abi()
    hp = Heap(ab.h)
    for a1, v in (cells or {}).items():
        t, p = enc(hp, v)
        ab.set_cell(a1, t, p)
    vals = []
    for v in args:
        if isinstance(v, tuple) and v[0] == "ref":
            vals.append((9, ab.key(v[1])))
        else:
            vals.append(enc(hp, v))
    orig = ab.state

    def st(**regs):
        x = orig(**regs)
        x[24] = HT0
        x[11] = 0x100       # RSP: start of RET_STACK (control.md); TEXT spills there
        return x
    ab.state = st
    try:
        (t, p), steps = ab.call(W0, FID[name], vals, max_steps=20000)
    finally:
        ab.state = orig
    if t == 1:
        return p
    if t == 2:
        return text_at(ab.h, int(p))
    if t == 3:
        return bool(p)
    if t == 4:
        return ("err", int(p))
    return (t, p)


def enc(hp, v):
    if v is None:
        return (0, 0)
    if v == "MISS":
        return (8, 0)
    if isinstance(v, bool):
        return (3, float(v))
    if isinstance(v, (int, float)):
        return (1, float(v))
    if isinstance(v, tuple) and v[0] == "err":
        return (4, v[1])
    return hp.s(v)


@pytest.mark.parametrize("name,args,want", [
    ("LEN", ["Phoenix, AZ"], 11), ("LEN", [""], 0), ("LEN", [None], 0), ("LEN", [12345], 5),
    ("LEN", [-2.5], 4), ("LEN", [True], 4), ("LEN", [False], 5), ("LENB", ["abc"], 3),
    ("LEN", [("err", 7)], ("err", 7)),
    ("CODE", ["A"], 65), ("CODE", [1], 49), ("UNICODE", ["B"], 66), ("CODE", [""], ("err", 3)),
    ("UPPER", ["total"], "TOTAL"), ("LOWER", ["E. E. Cummings"], "e. e. cummings"), ("UPPER", [12], "12"),
    ("EXACT", ["word", "word"], True), ("EXACT", ["Word", "word"], False), ("EXACT", [1, "1"], True),
    ("EXACT", [True, "TRUE"], True), ("EXACT", [None, ""], True),
    ("MID", ["Fluid Flow", 7, 20], "Flow"), ("MID", ["Fluid Flow", "1", 5], "Fluid"),
    ("MID", ["abc", 0, 1], ("err", 3)), ("MIDB", ["abcdef", 2, 3], "bcd"),
    ("MID", ["abc", ("err", 2), 1], ("err", 2)), ("MID", ["abc", "x", 1], ("err", 3)),
    ("MID", ["abc", True, 2], "ab"),
    ("LEFT", ["Sale Price", 4], "Sale"), ("LEFT", ["Sweden"], "S"), ("LEFTB", ["abc", 2], "ab"),
    ("LEFT", ["abc", "MISS"], ""), ("LEFT", ["abc", -1], ("err", 3)), ("LEFT", [12345, 2], "12"),
    ("RIGHT", ["Sale Price", 5], "Price"), ("RIGHT", ["Stock Number"], "r"), ("RIGHT", ["abc", 10], "abc"),
    ("RIGHT", ["abc", 0], ""), ("RIGHT", ["abc", 1.9], "c"), ("RIGHTB", ["abcd", 2], "cd"),
    ("RIGHT", ["abc", -1], ("err", 3)),
    ("CHAR", [65], "A"), ("CHAR", [33], "!"), ("CHAR", ["66"], "B"), ("CHAR", [0], ("err", 3)),
    ("UNICHAR", [66], "B"), ("UNICHAR", [128512], "\U0001F600"),
    ("T", ["Rainfall"], "Rainfall"), ("T", [19], ""), ("T", [True], ""), ("T", [("err", 7)], ("err", 7)),
])
def test_abi(name, args, want):
    assert run(name, *args) == want


def test_wrong_arg_count():
    assert run("LEN", "a", "b") == ("err", 3)
    assert run("MID", "abc", 1) == ("err", 3)
    assert run("EXACT", "a") == ("err", 3)


def test_cell_references():
    cells = {"A1": "Fluid Flow", "B1": 3.0, "C1": True}
    assert run("LEN", ("ref", "A1"), cells=cells) == 10
    assert run("LEFT", ("ref", "A1"), ("ref", "B1"), cells=cells) == "Flu"
    assert run("T", ("ref", "B1"), cells=cells) == ""
    assert run("T", ("ref", "A1"), cells=cells) == "Fluid Flow"
    assert run("LEN", ("ref", "Z99"), cells=cells) == 0
    assert run("EXACT", ("ref", "C1"), "TRUE", cells=cells) is True


# ---------------- direct entry into a driver (A, B, C, N0 set as tx_ld would), result via tx_fin
def direct(net, a, n0=0, b=(0, 0), c=(0, 0), extra=None, max_steps=200000):
    ab = abi()
    hp = Heap(ab.h)
    a = enc(hp, a) if not (isinstance(a, tuple) and isinstance(a[0], int)) else a
    x = ab.state(PC=0, N0=n0, AT=a[0], AP=a[1], BT=b[0], BP=b[1], CT=c[0], CP=c[1])
    x[24] = HT0
    x[11] = 0x100      # RSP
    x[39 + 1] = 0      # T9 = P1 to restore
    x[40] = 1          # T10 = n (word 39)
    for w, v in (extra or {}).items():
        x[w + 1] = v
    out = ab.h.run(net, x, max_steps=max_steps)
    t, p = int(out[13]), out[14]
    assert out[27] == 1  # N0 restored from T10
    if t == 2:
        return text_at(ab.h, int(p))
    return (t, p)


@pytest.mark.parametrize("mode,s,want", [
    (1, "a\tb\x01c\nd\x1f", "abcd"), (1, "", ""), (1, "plain", "plain"), (1, "x\x7fy", "x\x7fy"),
    (2, "  First Quarter   Earnings  ", "First Quarter Earnings"), (2, "   ", ""), (2, "a", "a"),
    (2, " a  b ", "a b"), (2, "ab  cd", "ab cd"), (2, " x ", " x "),
    (3, "this is a TITLE", "This Is A Title"), (3, "2-way street", "2-Way Street"),
    (3, "76BudGet", "76Budget"), (3, "it's", "It'S"), (3, "école ÉTÉ", "École Été"),
    (3, "", ""),
])
def test_clean_trim_proper(mode, s, want):
    assert direct(326, s, n0=mode) == want


FID.update({"CLEAN": 68, "TRIM": 478, "PROPER": 374, "CONCAT": 75, "CONCATENATE": 76, "TEXTJOIN": 465,
            "REPT": 396, "REPLACE": 394, "REPLACEB": 395, "FIND": 171, "FINDB": 172, "SEARCH": 409,
            "SEARCHB": 410, "VALUE": 490})


@pytest.mark.parametrize("name,args,want", [
    ("CLEAN", ["a\x07b"], "ab"), ("TRIM", ["  a  b  "], "a b"), ("PROPER", ["hello world"], "Hello World"),
    ("TRIM", [12], "12"),
    ("CONCATENATE", ["Stream population for ", "brook trout", " is ", 32, "/mile."],
     "Stream population for brook trout is 32/mile."),
    ("CONCAT", ["a"], "a"), ("CONCAT", ["a", "", "b", True], "abTRUE"), ("CONCAT", ["x", ("err", 7), "y"], ("err", 7)),
    ("CONCAT", ["a", "b", "c", "d", ("err", 2)], ("err", 2)), ("CONCATENATE", [None, 1.5], "1.5"),
    ("TEXTJOIN", [", ", True, "a", "", "b"], "a, b"), ("TEXTJOIN", [", ", False, "a", "", "b"], "a, , b"),
    ("TEXTJOIN", ["-", True, "x"], "x"), ("TEXTJOIN", ["", True, "ab", "cd", "e"], "abcde"),
    ("TEXTJOIN", [" ", 1, "a", None, "c"], "a c"), ("TEXTJOIN", [",", True, "", ""], ""),
    ("REPT", ["*-", 3], "*-*-*-"), ("REPT", ["-", 10], "----------"), ("REPT", ["ab", 0], ""),
    ("REPT", ["ab", 2.9], "abab"), ("REPT", ["ab", -1], ("err", 3)), ("REPT", ["abc", 20000], ("err", 3)),
    ("REPT", ["", 5], ""),
    ("REPLACE", ["abcdefghijk", 6, 5, "*"], "abcde*k"), ("REPLACE", ["2009", 3, 2, "10"], "2010"),
    ("REPLACE", ["123456", 1, 3, "@"], "@456"), ("REPLACE", ["abc", 10, 1, "X"], "abcX"),
    ("REPLACE", ["abc", 2, 0, "XY"], "aXYbc"), ("REPLACE", ["abc", 0, 1, "X"], ("err", 3)),
    ("REPLACE", ["abc", 1, -1, "X"], ("err", 3)), ("REPLACEB", ["abcd", 2, 2, ""], "ad"),
    ("REPLACE", ["abc", 2, 99, ""], "a"),
    ("FIND", ["M", "Miriam McGovern"], 1), ("FIND", ["m", "Miriam McGovern"], 6),
    ("FIND", ["M", "Miriam McGovern", 3], 8), ("FIND", ["x", "abc"], ("err", 3)), ("FIND", ["", "abc"], 1),
    ("FIND", ["", "abc", 3], 3), ("FIND", ["bc", "abcbc", 3], 4), ("FIND", ["a", "abc", 0], ("err", 3)),
    ("FIND", ["a", "abc", 4], ("err", 3)), ("FIND", ["abcd", "abc"], ("err", 3)), ("FINDB", ["c", "abc"], 3),
    ("FIND", ["?", "a?c"], 2), ("FIND", [3, 12345], 3),
    ("SEARCH", ["e", "Statements", 6], 7), ("SEARCH", ["margin", "Profit Margin"], 8),
    ("SEARCH", ["MAR", "Profit margin"], 8), ("SEARCH", ["p?o", "aProfit"], 2), ("SEARCH", ["f*m", "Profit Margin"], 4),
    ("SEARCH", ["~?", "a?b"], 2), ("SEARCH", ["~*", "ab*"], 3), ("SEARCH", ["*", "abc"], 1),
    ("SEARCH", ["a*c", "xxabxbc"], 3), ("SEARCH", ["z*", "abc"], ("err", 3)), ("SEARCH", ["é", "CAFÉ"], 4),
    ("SEARCH", ["b?", "ab"], ("err", 3)), ("SEARCHB", ["C", "abc"], 3), ("SEARCH", ["~x", "a~xb"], 2),
    ("VALUE", ["123"], 123), ("VALUE", [7.5], 7.5), ("VALUE", ["abc"], ("err", 3)), ("VALUE", [None], 0),
    ("VALUE", [True], ("err", 3)), ("VALUE", ["-1.5E3"], -1500),
])
def test_abi_new(name, args, want):
    assert run(name, *args) == want


def test_new_arg_counts():
    assert run("TEXTJOIN", ",", True) == ("err", 3)
    assert run("REPLACE", "a", 1, 1) == ("err", 3)
    assert run("FIND", "a") == ("err", 3)
    assert run("REPT", "a") == ("err", 3)


def test_new_with_refs():
    cells = {"A1": "  padded  ", "B1": 2.0, "C1": "x"}
    assert run("TRIM", ("ref", "A1"), cells=cells) == "padded"
    assert run("REPT", ("ref", "C1"), ("ref", "B1"), cells=cells) == "xx"
    assert run("CONCAT", ("ref", "C1"), ("ref", "B1"), ("ref", "Q7"), cells=cells) == "x2"
    assert run("FIND", ("ref", "C1"), "abcx", cells=cells) == 4


# ---------------- TEXT driver entered directly (A = value, B = code text)
@pytest.mark.parametrize("v,code,want", [
    (1234.567, "#,##0.00", "1,234.57"), (0.285, "0.0%", "28.5%"), (42, "000000", "000042"),
    (-3.14159, "0.00;(0.00)", "(3.14)"), (5, "$#,##0", "$5"), (1234567.891, "#,##0", "1,234,568"),
])
def test_text_direct(v, code, want):
    ab = abi()
    hp = Heap(ab.h)
    hp.at = 0x318000
    b = hp.s(code)
    assert direct(336, (1, float(v)), b=b) == want


# ---------------- SUBSTITUTE driver entered directly (tx_ld state: A, B, C texts, AS/AR1 instance)
@pytest.mark.parametrize("t,o,n,inst,want", [
    ("Sales Data", "Sales", "Cost", None, "Cost Data"),
    ("Quarter 1, 2008", "1", "2", 1, "Quarter 2, 2008"),
    ("Quarter 1, 2011", "1", "2", 3, "Quarter 1, 2012"),
    ("aaaa", "aa", "x", None, "xx"), ("aaaa", "aa", "x", 2, "aax"), ("abc", "", "x", None, "abc"),
    ("abcabc", "b", "", None, "acac"), ("abc", "z", "y", None, "abc"), ("abc", "c", "XYZ", None, "abXYZ"),
    ("a.b.c.d.e.f.g.h.i.j.k.l.m.n.o.p.q.r", ".", "--", None, "a--b--c--d--e--f--g--h--i--j--k--l--m--n--o--p--q--r"),
    ("abc", "b", "x", 0, ("err", 3)), ("abc", "b", "x", 5, "abc"), ("", "a", "b", None, ""),
])
def test_substitute_direct(t, o, n, inst, want):
    ab = abi()
    hp = Heap(ab.h)
    hp.at = 0x318000
    a, b, c = hp.s(t), hp.s(o), hp.s(n)
    extra = {19: 1 if inst is not None else 0, 20: float(inst) if inst is not None else 0}
    r = direct(334, a, b=b, c=c, extra=extra)
    if isinstance(want, tuple):
        assert (int(r[0]), int(r[1])) == (4, want[1])
    else:
        assert r == want


FID.update({"TEXT": 462, "SUBSTITUTE": 439})


@pytest.mark.parametrize("name,args,want", [
    ("TEXT", [1234.567, "$#,##0.00"], "$1,234.57"), ("TEXT", [0.285, "0.0%"], "28.5%"),
    ("TEXT", [42, "000000"], "000042"), ("TEXT", ["5", "0.00"], "5"), ("TEXT", [None, "0.0"], "0.0"),
    ("TEXT", [7, ("err", 2)], ("err", 2)), ("TEXT", [-1.5, "0.0;(0.0)"], "(1.5)"),
    ("SUBSTITUTE", ["Sales Data", "Sales", "Cost"], "Cost Data"),
    ("SUBSTITUTE", ["Quarter 1, 2011", "1", "2", 3], "Quarter 1, 2012"),
    ("SUBSTITUTE", ["Quarter 1, 2008", "1", "2", 1], "Quarter 2, 2008"),
    ("SUBSTITUTE", [12121, 1, 3], "32323"), ("SUBSTITUTE", ["abc", "b", "x", 0], ("err", 3)),
    ("SUBSTITUTE", ["abc", "b", "x", "two"], ("err", 3)), ("SUBSTITUTE", ["a b", " ", ""], "ab"),
])
def test_abi_text_substitute(name, args, want):
    assert run(name, *args) == want


def test_text_substitute_counts():
    assert run("TEXT", 1) == ("err", 3)
    assert run("SUBSTITUTE", "a", "b") == ("err", 3)
