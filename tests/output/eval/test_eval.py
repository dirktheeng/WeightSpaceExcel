"""Black-box output tests for weights/eval (evaluator and recalculation).

Formula records are test data written into memory (evalbb.Sheet.tokens); cells are committed
through CELL_SET with LR = 80 (hk_commit). Results are read back from the cell store. Expected
values are Excel's, stated by hand (stage1 cases.yaml and Excel documentation).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evalbb as e  # noqa: E402

R = lambda a: ("ref", a)  # noqa: E731
E = lambda n: ("err", n)  # noqa: E731
ERR = lambda n: {"error": n}  # noqa: E731

SINGLE = [
    ([1, 2, "+"], 3), ([7, 10, "-"], -3), ([6, 7, "*"], 42), ([7, 2, "/"], 3.5),
    ([1, 0, "/"], ERR("#DIV/0!")), ([0, 0, "/"], ERR("#DIV/0!")), ([1, 3, "/", 3, "*"], 1),
    ([1e308, 10, "*"], ERR("#NUM!")), ([1e-200, 1e-200, "*"], 0), ([0.1, 3, "*"], 0.3),
    ([1, 2, 3, "*", "+"], 7), ([2, 3, "u-", "-"], 5),
    ([2, 10, "^"], 1024), ([2, -2, "^"], 0.25), ([0, 0, "^"], ERR("#NUM!")),
    ([0, -1, "^"], ERR("#DIV/0!")), ([-2, 3, "^"], -8), ([-2, 0.5, "^"], ERR("#NUM!")),
    ([10, 309, "^"], ERR("#NUM!")), ([2, 3, "^", 2, "^"], 64), ([2, "u-", 2, "^"], 4),
    ([2, "u-", 2, "u-", "^"], 0.25), ([50, "%", 2, "^"], 0.25), ([10, "%"], 0.1),
    ([200, "%", "%"], 0.02), ([1, "u-", "u-", "u-"], -1), ([True, "u-"], -1), ([5, "u+"], 5),
    ([True, 1, "+"], 2), ([False, 5, "*"], 0), (["'a", 1, "+"], ERR("#VALUE!")),
    ([E("#N/A"), E("#DIV/0!"), "+"], ERR("#N/A")), ([E("#DIV/0!"), E("#N/A"), "+"], ERR("#DIV/0!")),
    ([1, 0, "/", E("#N/A"), "+"], ERR("#DIV/0!")), ([E("#NUM!"), 0, "*"], ERR("#NUM!")),
    ([1, 2, E("#NUM!"), "*", "+"], ERR("#NUM!")),
    ([1, 2, "<"], True), ([2, 2, "<="], True), ([2, 3, ">="], False), ([1, 2, "<>"], True),
    (["'abc", "'ABC", "="], True), (["'A", "'b", "<"], True), (["'b", "'A", "<"], False),
    (["'ab", "'abc", "<"], True), (["'10", "'9", "<"], True), (["'1", 1, "="], False),
    ([1, "'a", "<"], True), (["'zzz", True, "<"], True), ([False, 1000, ">"], True),
    ([True, 1, "="], False), (["'", "'", "="], True), ([0.1, 0.2, "+", 0.3, "="], True),
    (["'a ", "'a", "="], False), ([1, E("#N/A"), "<"], ERR("#N/A")), ([1, 1, "=", 1, "="], False),
    ([2, 1, ">", 0, ">"], True), ([R("Z1"), "'", "="], True), ([R("Z1"), 0, "="], True),
    ([R("Z1"), False, "="], True), ([R("Z1"), "'a", "<"], True), ([R("Z1"), R("Z2"), "="], True),
    (["'ab", "'cd", "&"], "abcd"), ([1, 2, "&"], "12"), ([1.5, "'", "&"], "1.5"),
    ([True, "'", "&"], "TRUE"), ([True, False, "&"], "TRUEFALSE"),
    ([1, 3, "/", "'", "&"], "0.333333333333333"), ([0.1, 0.2, "+", "'", "&"], "0.3"),
    ([1e20, "'", "&"], "1E+20"), ([5, "u-", "'", "&"], "-5"), ([12, "%", "'", "&"], "0.12"),
    ([R("Z1"), R("Z2"), "&"], ""), ([1, 0, "/", "'x", "&"], ERR("#DIV/0!")),
    (["'x", E("#N/A"), "&"], ERR("#N/A")), ([123456789012, "'", "&"], "123456789012"),
    ([0.000001, "'", "&"], "0.000001"), ([1, 2, "&", 3, "&"], "123"), ([1, 2, "+", 3, "&"], "33"),
    ([R("Z1")], 0), ([R("Z1"), 5, "/"], 0), ([5, R("Z1"), "/"], ERR("#DIV/0!")),
    ([E("#REF!")], ERR("#REF!")),
]


@pytest.mark.parametrize("toks,exp", SINGLE)
def test_single_cell(toks, exp):
    s = e.Sheet()
    s.set("A1", formula=toks)
    assert s.fault() == 0
    got = s.value("A1")
    if isinstance(exp, bool):
        assert got is exp
    elif isinstance(exp, float) and exp not in (0,):
        assert abs(got - exp) <= 1e-12 * abs(exp)
    else:
        assert got == exp
    assert s.circ() == 0


def test_function_stub_gives_name_error():
    s = e.Sheet()
    s.set("A1", formula=[1, 2, ("fn", 0, 2)])
    assert s.value("A1") == ERR("#NAME?")
    s.set("A2", formula=[("fn", 0, 0), 1, "+"])
    assert s.value("A2") == ERR("#NAME?")


def test_references_and_edit_recalc():
    s = e.Sheet()
    s.set("A1", 7)
    s.set("B1", formula=[R("A1")])
    s.set("C3", formula=[R("A1"), R("$B$1"), "*", 2, "-"])
    assert s.value("B1") == 7 and s.value("C3") == 47
    s.set("A1", 10)
    assert s.value("B1") == 10 and s.value("C3") == 98


def test_dependents_entered_before_precedents():
    s = e.Sheet()
    s.set("A1", formula=[R("A2"), 1, "+"])
    s.set("A2", formula=[R("A3"), 1, "+"])
    s.set("A3", formula=[R("A4"), 1, "+"])
    s.set("A4", 1)
    assert [s.value(a) for a in ("A1", "A2", "A3")] == [4, 3, 2]


def test_diamond_and_text_chain():
    s = e.Sheet()
    s.set("A1", 2)
    s.set("B1", formula=[R("A1"), R("A1"), "*"])
    s.set("C1", formula=[R("B1"), R("A1"), "+"])
    s.set("D1", formula=[R("C1"), R("B1"), "*"])
    assert (s.value("B1"), s.value("C1"), s.value("D1")) == (4, 6, 24)
    s.set("E1", formula=[R("D2"), R("C2"), "&"])
    s.set("D2", formula=[R("C2"), "'b", "&"])
    s.set("C2", "a")
    assert s.value("D2") == "ab" and s.value("E1") == "aba"


def test_replaced_formula_no_longer_depends():
    s = e.Sheet()
    s.set("A1", 1)
    s.set("B1", formula=[R("A1")])
    s.set("B1", 7)
    s.set("A1", 9)
    assert s.value("B1") == 7


def test_self_cycle():
    s = e.Sheet()
    s.set("A1", formula=[R("A1"), 1, "+"])
    assert s.value("A1") == 0 and s.circ() == e.bb.key_of("A1") + 1


def test_cycle_dependent_and_break():
    s = e.Sheet()
    s.set("A1", formula=[R("B1")])
    s.set("B1", formula=[R("A1")])
    s.set("C1", formula=[R("A1"), 1, "+"])
    assert (s.value("A1"), s.value("B1"), s.value("C1")) == (0, 0, 1)
    assert s.circ() in (e.bb.key_of("A1") + 1, e.bb.key_of("B1") + 1)
    s.set("B1", 3)
    assert (s.value("A1"), s.value("B1"), s.value("C1")) == (3, 3, 4)
    assert s.circ() == 0


def test_three_cycle():
    s = e.Sheet()
    s.set("A1", formula=[R("B1"), 1, "+"])
    s.set("B1", formula=[R("C1"), 1, "+"])
    s.set("C1", formula=[R("A1"), 1, "+"])
    assert [s.value(a) for a in ("A1", "B1", "C1")] == [0, 0, 0]
    assert s.circ() != 0


def test_error_clears_after_fix():
    s = e.Sheet()
    s.set("A1", formula=[1, 0, "/"])
    s.set("B1", formula=[R("A1"), 1, "+"])
    assert s.value("B1") == ERR("#DIV/0!")
    s.set("A1", 4)
    assert s.value("B1") == 5


# ---- session 2: coercion, ^ via EXP/LN, ranges, union, intersection, sheets (expected values
# stated by hand from Excel's documented behaviour)
G = lambda a, b: ("rng", a, b)  # noqa: E731
SH = lambda n: ("sheet", n)  # noqa: E731

COERCE = [
    (["'1", 1, "+"], 2), (["' 2 ", 3, "*"], 6), (["'1e3", 0, "+"], 1000), (["'50%", 0, "+"], 0.5),
    (["'$1,000", 0, "+"], 1000), (["'(4)", 0, "+"], -4), (["'.5", 2, "*"], 1),
    (["'abc", 1, "+"], ERR("#VALUE!")), (["'", 1, "+"], ERR("#VALUE!")),
    (["'TRUE", 0, "+"], ERR("#VALUE!")), (["'1 1", 0, "+"], ERR("#VALUE!")),
    (["'3", "u-"], -3), (["'50", "%"], 0.5), (["'2", "'3", "^"], 8),
    (["'1", "'2", "&", 1, "+"], 13),
]
POW = [
    ([2, 0.5, "^"], 1.4142135623730951), ([10, 0.5, "^"], 3.1622776601683795),
    ([2, -0.5, "^"], 0.7071067811865476), ([0, 0.5, "^"], 0), ([0, -0.5, "^"], ERR("#DIV/0!")),
    ([-8, 1 / 3, "^"], ERR("#NUM!")), ([1e300, 1.5, "^"], ERR("#NUM!")), ([1e-300, 1.5, "^"], 0),
    ([4, 2.5, "^"], 32.0), ([0.5, 2**31, "^"], 0), ([2, 1024.5, "^"], ERR("#NUM!")),
    ([1e308, 0.5, "^"], 1e154), ([9, -1.5, "^"], 1 / 27),
]


@pytest.mark.parametrize("toks,exp", COERCE + POW)
def test_coercion_and_power(toks, exp):
    test_single_cell(toks, exp)


def _grid():
    s = e.Sheet()
    for a, v in (("A1", 1), ("A2", 2), ("A3", 3), ("B1", 10), ("B2", 20), ("C1", 30)):
        s.set(a, v)
    return s


REFS = [
    ("D2", [G("A1", "A3")], 2),                         # implicit intersection, same row
    ("D3", [G("A3", "A1"), 2, "*"], 6),                 # reversed corners normalise
    ("D4", [G("A1", "A3")], ERR("#VALUE!")),            # row outside the range
    ("B5", [G("A1", "C1")], 10),                        # one row, home column inside
    ("E5", [G("A1", "B2")], ERR("#VALUE!")),            # 2D range, cell outside
    ("E1", [G("A1", "C1"), G("B1", "B3"), "isect"], 10),
    ("E2", [G("A1", "A2"), G("C1", "C2"), "isect"], ERR("#NULL!")),
    ("E3", [G("A1", "C3"), G("B2", "D4"), "isect", R("B2"), "isect"], 20),
    ("E4", [R("A1"), R("B1"), "isect"], ERR("#NULL!")),
    ("E6", [G("A1", "A3"), G("A2", "A3"), "isect"], ERR("#VALUE!")),  # multi-cell result as value
    ("E7", [R("A1"), R("B1"), "union"], ERR("#VALUE!")),
    ("E8", [R("A1"), R("B1"), "union", 1, "+"], ERR("#VALUE!")),
    ("E9", [E("#N/A"), R("A1"), "isect"], ERR("#N/A")),
    ("F1", [G("$A$1", "$A$3"), R("A2"), "isect", 1, "+"], 3),
]


@pytest.mark.parametrize("home,toks,exp", REFS)
def test_ranges_union_intersection(home, toks, exp):
    s = _grid()
    s.set(home, formula=toks)
    assert s.fault() == 0
    got = s.value(home)
    assert got == exp, (home, got)


def test_whole_column_and_row_intersection():
    s = _grid()
    s.set("H1", formula=[G("$A$1", "$A$1048576"), G("$A$2", "$XFD$2"), "isect"])   # A:A 2:2
    assert s.value("H1") == 2
    s.set("H3", formula=[G("$B$1", "$B$1048576")])                                # B:B in row 3
    assert s.value("H3") == 0


def test_sheet_references_and_dependencies():
    s = e.Sheet()
    s.set("B2", 7, sheet=1)
    s.set("B2", 100)
    s.set("A1", formula=[SH(1), R("B2"), 1, "+"])
    assert s.value("A1") == 8
    s.set("B2", 10, sheet=1)
    assert s.value("A1") == 11
    s.set("A2", formula=[R("B2"), SH(1), R("B2"), "+"])
    assert s.value("A2") == 110
    s.set("A3", formula=[SH(1), R("B2"), R("B2"), "isect"])
    assert s.value("A3") == ERR("#VALUE!")
    t = e.Sheet()
    t.set("C1", formula=[SH(1), R("D1"), 2, "*"])
    t.set("D1", formula=[3, 4, "+"], sheet=1)
    assert t.value("C1") == 14
    t.set("D1", formula=[5, 5, "+"], sheet=1)
    assert t.value("C1") == 20
    assert t.fault() == 0
