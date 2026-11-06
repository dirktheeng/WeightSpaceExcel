"""Output tests for the lookup and reference functions through the function ABI
(encodings/functions.md): entry network 375 with the ABI entry state, FN_RET (257) replaced by
HALT_OK so the returned A is observed. Black box: only A, the preserve set and SCR are checked.
Expected values are stated by hand from Microsoft's documentation of each function.

Sheet used by most tests (rows and columns as Excel shows them):
    A1:A5 = 10, 20, 30, 40, 50      B1:B5 = a, b, c, d, e      C1:C5 = 1.5, 2.5, 3.5, 4.5, 5.5
    E1:H1 = 1, 2, 3, 4 (a row)      E2:H2 = w, x, y, z
    J1:J4 = pear, apple, fig, kiwi
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lkbb import Sheet, call, ref, rng, union, MISSING, SCR0, HOME  # noqa: E402

NA, VALUE, REF, DIV0 = ("err", 7), ("err", 4 - 1), ("err", 4), ("err", 2)
REF = ("err", 4)
VALUE = ("err", 3)

_sh = None


def sh():
    global _sh
    if _sh is None:
        s = Sheet()
        s.column(0, [10, 20, 30, 40, 50])
        s.column(1, ["a", "b", "c", "d", "e"])
        s.column(2, [1.5, 2.5, 3.5, 4.5, 5.5])
        s.row(0, [1, 2, 3, 4], col0=4)
        s.row(1, ["w", "x", "y", "z"], col0=4)
        s.column(9, ["pear", "apple", "fig", "kiwi"])
        _sh = s
    return _sh


def f(name, *args):
    v, out, steps = call(sh(), name, *args)
    return v


# ---------------- MATCH
@pytest.mark.parametrize("args,want", [
    ((30, rng("A1:A5"), 0), 3), ((35, rng("A1:A5"), 0), NA), ((35, rng("A1:A5")), 3), ((35, rng("A1:A5"), 1), 3),
    ((5, rng("A1:A5"), 1), NA), ((99, rng("A1:A5"), 1), 5), (("c", rng("B1:B5"), 0), 3), (("C", rng("B1:B5"), 0), 3),
    (("?", rng("B1:B5"), 0), 1), (("*", rng("J1:J4"), 0), 1), (("f*", rng("J1:J4"), 0), 3), (("k?w?", rng("J1:J4"), 0), 4),
    ((3, rng("E1:H1"), 0), 3), ((3.5, rng("E1:H1"), 1), 3), ((30, rng("A1:B5"), 0), NA), ((NA, rng("A1:A5"), 0), NA),
    ((30, ref("A3"), 0), 1), ((30, rng("A1:A5"), 2), 3), ((34, rng("A1:A5"), 0.5), 3),
])
def test_match(args, want):
    assert f("MATCH", *args) == want


def test_match_descending():
    s = sh()
    s.column(11, [50, 40, 30, 20, 10])            # L1:L5
    assert f("MATCH", 35, rng("L1:L5"), -1) == 2
    assert f("MATCH", 30, rng("L1:L5"), -1) == 3
    assert f("MATCH", 55, rng("L1:L5"), -1) == NA


def test_match_lookup_value_from_cell():
    assert f("MATCH", ref("A4"), rng("A1:A5"), 0) == 4
    assert f("MATCH", ref("B2"), rng("B1:B5"), 0) == 2


# ---------------- VLOOKUP / HLOOKUP
@pytest.mark.parametrize("args,want", [
    ((30, rng("A1:C5"), 2, False), "c"), ((30, rng("A1:C5"), 3, 0), 3.5), ((35, rng("A1:C5"), 3), 3.5),
    ((35, rng("A1:C5"), 2, True), "c"), ((5, rng("A1:C5"), 2), NA), ((35, rng("A1:C5"), 2, False), NA),
    ((30, rng("A1:C5"), 4), REF), ((30, rng("A1:C5"), 0), VALUE), ((30, rng("A1:C5"), 2.9, False), "c"),
    ((30, rng("A1:C5"), "x"), VALUE), ((DIV0, rng("A1:C5"), 2), DIV0), ((30, REF, 2), REF),
    ((ref("A2"), rng("A1:C5"), 3, False), 2.5), ((50, rng("A1:C5"), 1, False), 50),
])
def test_vlookup(args, want):
    assert f("VLOOKUP", *args) == want


@pytest.mark.parametrize("args,want", [
    ((3, rng("E1:H2"), 2, False), "y"), ((3.5, rng("E1:H2"), 2), "y"), ((0, rng("E1:H2"), 2), NA),
    ((4, rng("E1:H2"), 3, False), REF), ((4, rng("E1:H2"), 1), 4),
])
def test_hlookup(args, want):
    assert f("HLOOKUP", *args) == want


def test_vlookup_wildcard_text():
    assert f("VLOOKUP", "b*", rng("B1:C5"), 2, False) == 2.5


# ---------------- LOOKUP
@pytest.mark.parametrize("args,want", [
    ((44, rng("A1:A5"), rng("B1:B5")), "d"), ((10, rng("A1:A5"), rng("C1:C5")), 1.5), ((9, rng("A1:A5"), rng("B1:B5")), NA),
    ((44, rng("A1:C5")), 4.5),                    # array form, taller than wide: first column, last column
    ((2.5, rng("E1:H2")), "x"),                   # array form, wider than tall: first row, last row
    ((3, rng("E1:H1"), rng("B1:B5")), "c"),       # horizontal lookup vector, vertical result vector
])
def test_lookup(args, want):
    assert f("LOOKUP", *args) == want


# ---------------- XMATCH
@pytest.mark.parametrize("args,want", [
    ((30, rng("A1:A5")), 3), ((35, rng("A1:A5")), NA), ((35, rng("A1:A5"), -1), 3), ((35, rng("A1:A5"), 1), 4),
    ((60, rng("A1:A5"), 1), NA), (("c", rng("B1:B5"), 0, -1), 3), (("b?", rng("B1:B5"), 2), NA), (("?", rng("B1:B5"), 2), 1),
    ((35, rng("A1:A5"), -1, 2), 3), ((35, rng("A1:A5"), 1, 2), 4), ((40, rng("A1:A5"), 0, 2), 4), ((41, rng("A1:A5"), 0, 2), NA),
    (("grape", rng("J1:J4"), -1), 3), (("grape", rng("J1:J4"), 1), 4),
    ((30, rng("A1:A5"), 3), VALUE), ((30, rng("A1:A5"), 0, 3), VALUE), ((30, rng("A1:A5"), 0, ("err", 6)), ("err", 6)),
])
def test_xmatch(args, want):
    assert f("XMATCH", *args) == want


def test_xmatch_descending_binary():
    s = sh()
    s.column(11, [50, 40, 30, 20, 10])
    assert f("XMATCH", 35, rng("L1:L5"), -1, -2) == 3     # next smaller in descending data: 30
    assert f("XMATCH", 35, rng("L1:L5"), 1, -2) == 2      # next larger: 40
    assert f("XMATCH", 20, rng("L1:L5"), 0, -2) == 4


# ---------------- XLOOKUP
@pytest.mark.parametrize("args,want", [
    ((40, rng("A1:A5"), rng("B1:B5")), "d"), ((41, rng("A1:A5"), rng("B1:B5")), NA),
    ((41, rng("A1:A5"), rng("B1:B5"), "none"), "none"), ((41, rng("A1:A5"), rng("C1:C5"), MISSING, -1), 4.5),
    ((41, rng("A1:A5"), rng("C1:C5"), MISSING, 1), 5.5), (("C", rng("B1:B5"), rng("A1:A5")), 30),
    (("*e", rng("J1:J4"), rng("A1:A4"), MISSING, 2), 20), ((3, rng("E1:H1"), rng("E2:H2")), "y"),
    ((30, rng("A1:A5"), 5), VALUE), ((30, rng("A1:A5"), rng("B1:B5"), MISSING, 0, -1), "c"),
    ((45, rng("A1:A5"), rng("B1:B5"), MISSING, -1, 2), "d"), ((NA, rng("A1:A5"), rng("B1:B5"), 0), NA),
])
def test_xlookup(args, want):
    assert f("XLOOKUP", *args) == want


# ---------------- ROW / COLUMN / ROWS / COLUMNS / AREAS
def test_row_column():
    assert f("ROW") == HOME[0] + 1 and f("COLUMN") == HOME[1] + 1
    assert f("ROW", ref("C7")) == 7 and f("COLUMN", ref("C7")) == 3
    assert f("ROW", rng("B3:D9")) == 3 and f("COLUMN", rng("B3:D9")) == 2
    assert f("ROW", REF) == REF and f("ROW", 5) == VALUE


def test_rows_columns():
    assert f("ROWS", rng("B3:D9")) == 7 and f("COLUMNS", rng("B3:D9")) == 3
    assert f("ROWS", ref("A1")) == 1 and f("COLUMNS", ref("Z9")) == 1
    assert f("ROWS", 5) == 1 and f("COLUMNS", "x") == 1
    assert f("ROWS", rng("A1:A1048576")) == 1048576 and f("COLUMNS", rng("A1:XFD1")) == 16384


def test_areas():
    assert f("AREAS", ref("A1")) == 1 and f("AREAS", rng("A1:B2")) == 1
    assert f("AREAS", union(ref("A1"), rng("B1:C3"))) == 2
    assert f("AREAS", union(union(ref("A1"), ref("B1")), ref("C1"))) == 3
    assert f("AREAS", 5) == VALUE


# ---------------- INDEX (reference form)
@pytest.mark.parametrize("args,want", [
    ((rng("A1:C5"), 2, 3), ("ref", 0, 1, 2)), ((rng("A1:A5"), 4), ("ref", 0, 3, 0)), ((rng("E1:H1"), 3), ("ref", 0, 0, 6)),
    ((rng("A1:C5"), 6, 1), REF), ((rng("A1:C5"), 1, 4), REF), ((rng("A1:C5"), -1, 1), VALUE),
    ((rng("A1:C5"), "x", 1), VALUE), ((rng("A1:C5"), DIV0, 1), DIV0), ((rng("A1:C5"), 2, 2, 2), REF),
    ((rng("A1:C5"), 2, 2, 1), ("ref", 0, 1, 1)), ((ref("B4"), 1, 1), ("ref", 0, 3, 1)), ((rng("A1:C5"), 2.7, 1.2), ("ref", 0, 1, 0)),
])
def test_index_cell(args, want):
    assert f("INDEX", *args) == want


@pytest.mark.parametrize("args,want", [
    ((rng("A1:C5"), 0, 2), ("rng", 0, 0, 1, 4, 1, 0)), ((rng("A1:C5"), 2, 0), ("rng", 0, 1, 0, 1, 2, 0)),
    ((rng("A1:C5"), 0, 0), ("rng", 0, 0, 0, 4, 2, 0)), ((rng("A1:C5"), 2), ("rng", 0, 1, 0, 1, 2, 0)),
])
def test_index_range_results(args, want):
    v, out, _ = call(sh(), "INDEX", *args)
    assert v == want and out[56] == SCR0 + 8                 # one 8-word record allocated


# ---------------- OFFSET
@pytest.mark.parametrize("args,want", [
    ((ref("A1"), 2, 1), ("ref", 0, 2, 1)), ((ref("B2"), -1, -1), ("ref", 0, 0, 0)), ((ref("A1"), 2.9, -0.5), ("ref", 0, 2, 0)),
    ((ref("A1"), -1, 0), REF), ((ref("A1"), 0, -1), REF), ((ref("A1"), 0, 0, 0), REF), ((ref("A1"), 0, 0, 1, 0), REF),
    ((ref("A1"), 1048575, 0), ("ref", 0, 1048575, 0)), ((ref("A1"), 1048575, 0, 2), REF), ((ref("A1"), 0, 16384), REF),
    ((5, 1, 1), VALUE), ((ref("A1"), "x", 1), VALUE), ((ref("A1"), 1, REF), REF),
])
def test_offset_cell(args, want):
    assert f("OFFSET", *args) == want


@pytest.mark.parametrize("args,want", [
    ((rng("A1:B2"), 1, 1), ("rng", 0, 1, 1, 2, 2, 0)), ((ref("A1"), 1, 0, 3, 2), ("rng", 0, 1, 0, 3, 1, 0)),
    ((rng("A1:B2"), 2, 2, MISSING, 3), ("rng", 0, 2, 2, 3, 4, 0)),
])
def test_offset_range_results(args, want):
    v, out, _ = call(sh(), "OFFSET", *args)
    assert v == want and out[56] == SCR0 + 8


# ---------------- CHOOSE
@pytest.mark.parametrize("args,want", [
    ((2, "x", "y", "z"), "y"), ((3.7, "x", "y", "z"), "z"), ((4, "x", "y", "z"), VALUE), ((0, "x"), VALUE),
    ((True, "t", "u"), "t"), (("1", "t"), VALUE), ((NA, 1, 2), NA), ((1, NA, 2), NA), ((2, NA, 2), 2),
    ((5, 1, 2, 3, 4, 5, 6), 5), ((6, 1, 2, 3, 4, 5, 6, 7), 6), ((7, 1, 2, 3, 4, 5, 6, 7, 8, 9), 7),
    ((8, 1, 2, 3, 4, 5, 6, 7, 8, 9), 8), ((9, 1, 2, 3, 4, 5, 6, 7, 8, 9), 9),
    ((ref("A1"), *range(1, 12)), 10), ((2, ref("B2"), rng("A1:A2")), ("rng", 0, 0, 0, 1, 0, 0)),
    ((1, ref("B2"), 5), ("ref", 0, 1, 1)),
])
def test_choose(args, want):
    assert f("CHOOSE", *args) == want


# ---------------- TRANSPOSE (no arrays yet: only single-cell and scalar arguments)
def test_transpose_without_arrays():
    assert f("TRANSPOSE", ref("A1")) == ("ref", 0, 0, 0)
    assert f("TRANSPOSE", 5) == 5
    assert f("TRANSPOSE", rng("A1:B2")) == VALUE


def test_step_counts():
    _, _, st_ref = call(sh(), "ROW", ref("C7"))
    _, _, st_v = call(sh(), "VLOOKUP", 30, rng("A1:C5"), 2, False)
    assert st_ref == 5
    assert st_v < 60
