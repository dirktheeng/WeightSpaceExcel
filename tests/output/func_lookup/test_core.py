"""Output tests for the shared search core (weights/func/lookup ids 360..374, core.md).

Black box: cells are written through CELL_SET, the core is started at lk_start (360) with
the register convention of weights/func/lookup/core.md section 2 and LR = HALT_OK, and only
STATUS, the result index (T3) and restored words are checked. Expected positions (0-based)
are stated by hand from Excel's documented MATCH / XMATCH behaviour.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lkbb import (Sheet, search, M_FWD, M_FWD_SMALLER, M_FWD_LARGER, M_REV, M_REV_SMALLER,  # noqa: E402
                  M_REV_LARGER, M_ASC_LAST_LE, M_DESC_LAST_GE, M_ASC_FIRST_GE, M_DESC_FIRST_LE,
                  M_ASC_EXACT, M_DESC_EXACT)

NF = None  # not found

_sheets = {}


def sheet(name):
    if name in _sheets:
        return _sheets[name]
    sh = Sheet()
    if name == "nums":
        sh.column(0, [10, 20, 30, 40, 50])                    # A1:A5 ascending
        sh.column(1, [50, 40, 30, 20, 10])                    # B1:B5 descending
        sh.column(2, [30, 10, 50, 20, 40, "x", 20])           # C1:C7 unsorted, one text
        sh.row(9, [5, 7, 9, 11])                              # A10:D10 horizontal
        sh.column(4, [1, 2, 2, 2, 3])                         # E1:E5 duplicates
        sh.column(5, [1, 2, 3, "a", "b"])                     # F1:F5 numbers then text
        sh.column(6, [1, 2, 3, None, None, None])             # G1:G6 trailing blanks
        sh.column(7, [False, True, 1, "TRUE"])                # H1:H4 types
    elif name == "text":
        sh.column(0, ["apple", "Banana", "cherry", "date", "fig"])
        sh.column(1, ["pear", "apple", "fig", "kiwi"])
        sh.column(2, ["apple", "Banana", "cherry", "date", "fig*", "a?c", "abc", "", "longer text value here"])
    _sheets[name] = sh
    return sh


# ---- exact, linear (MATCH 0 without wildcards, XMATCH 0 / 1 and 0 / -1)
@pytest.mark.parametrize("v,mode,want", [
    (30, M_FWD, 2), (10, M_FWD, 0), (50, M_FWD, 4), (35, M_FWD, NF), (5, M_FWD, NF),
    (30, M_REV, 2), (60, M_REV, NF),
    ("30", M_FWD, NF),                      # text "30" never equals the number 30
    (True, M_FWD, NF),                      # TRUE is not 1 in a lookup
])
def test_exact_numbers(v, mode, want):
    f, i, _, _ = search(sheet("nums"), v, 0, 0, 5, mode)
    assert (i if f else NF) == want


def test_exact_first_and_last_duplicate():
    sh = sheet("nums")
    assert search(sh, 2, 0, 4, 5, M_FWD)[1] == 1           # first 2 (E2)
    assert search(sh, 2, 0, 4, 5, M_REV)[1] == 3           # last 2 (E4), XMATCH search_mode -1


@pytest.mark.parametrize("v,want", [(False, 0), (True, 1), (1, 2), ("TRUE", 3), ("true", 3), (0, NF)])
def test_exact_type_classes(v, want):
    f, i, _, _ = search(sheet("nums"), v, 0, 7, 4, M_FWD)
    assert (i if f else NF) == want


def test_horizontal_vector():
    sh = sheet("nums")
    assert search(sh, 9, 9, 0, 4, M_FWD, horizontal=True)[1] == 2
    assert search(sh, 8, 9, 0, 4, M_ASC_LAST_LE, horizontal=True)[1] == 1
    assert search(sh, 12, 9, 0, 4, M_ASC_LAST_LE, horizontal=True)[1] == 3


@pytest.mark.parametrize("v,want", [("cherry", 2), ("CHERRY", 2), ("Banana", 1), ("banana", 1),
                                    ("cat", NF), ("", NF), ("figs", NF), ("fi", NF)])
def test_exact_text_case_insensitive(v, want):
    f, i, _, _ = search(sheet("text"), v, 0, 0, 5, M_FWD)
    assert (i if f else NF) == want


def test_exact_text_long_and_empty():
    sh = sheet("text")
    assert search(sh, "LONGER TEXT VALUE HERE", 0, 2, 9, M_FWD)[1] == 8
    assert not search(sh, "longer text value her", 0, 2, 9, M_FWD)[0]
    assert search(sh, "", 0, 2, 9, M_FWD)[1] == 7          # the empty-string cell C8


# ---- approximate, binary search (MATCH 1 / -1, VLOOKUP TRUE, LOOKUP, XMATCH search_mode +-2)
@pytest.mark.parametrize("v,want", [(30, 2), (35, 2), (10, 0), (9.99, NF), (50, 4), (1e300, 4), (5, NF),
                                    (-1, NF), (49.999, 3)])
def test_ascending_last_le(v, want):
    f, i, _, _ = search(sheet("nums"), v, 0, 0, 5, M_ASC_LAST_LE)
    assert (i if f else NF) == want


def test_ascending_duplicates_give_last():
    assert search(sheet("nums"), 2, 0, 4, 5, M_ASC_LAST_LE)[1] == 3
    assert search(sheet("nums"), 2.5, 0, 4, 5, M_ASC_LAST_LE)[1] == 3


@pytest.mark.parametrize("v,want", [(30, 2), (35, 1), (50, 0), (55, NF), (10, 4), (5, 4)])
def test_descending_last_ge(v, want):
    # MATCH(v, {50;40;30;20;10}, -1): smallest value >= v
    f, i, _, _ = search(sheet("nums"), v, 0, 1, 5, M_DESC_LAST_GE)
    assert (i if f else NF) == want


@pytest.mark.parametrize("v,want", [(30, 2), (35, 3), (5, 0), (50, 4), (51, NF)])
def test_ascending_first_ge(v, want):
    # XMATCH(v, {10..50}, 1, 2): exact or next larger
    f, i, _, _ = search(sheet("nums"), v, 0, 0, 5, M_ASC_FIRST_GE)
    assert (i if f else NF) == want


@pytest.mark.parametrize("v,want", [(30, 2), (35, 2), (5, NF), (55, 0), (10, 4)])
def test_descending_first_le(v, want):
    # XMATCH(v, {50..10}, -1, -2): exact or next smaller
    f, i, _, _ = search(sheet("nums"), v, 0, 1, 5, M_DESC_FIRST_LE)
    assert (i if f else NF) == want


@pytest.mark.parametrize("v,mode,col,want", [
    (30, M_ASC_EXACT, 0, 2), (35, M_ASC_EXACT, 0, NF), (60, M_ASC_EXACT, 0, NF),
    (40, M_DESC_EXACT, 1, 1), (45, M_DESC_EXACT, 1, NF),
])
def test_binary_exact(v, mode, col, want):
    f, i, _, _ = search(sheet("nums"), v, 0, col, 5, mode)
    assert (i if f else NF) == want


def test_binary_mixed_types_and_blanks():
    sh = sheet("nums")
    # numbers then text: a number finds the last number <= v, text finds text
    assert search(sh, 9e307, 0, 5, 5, M_ASC_LAST_LE)[1] == 2
    assert search(sh, "a", 0, 5, 5, M_ASC_LAST_LE)[1] == 3
    assert search(sh, "zzz", 0, 5, 5, M_ASC_LAST_LE)[1] == 4
    # trailing blanks are skipped
    assert search(sh, 2.5, 0, 6, 6, M_ASC_LAST_LE)[1] == 1
    assert search(sh, 100, 0, 6, 6, M_ASC_LAST_LE)[1] == 2


def test_binary_text_against_numbers_not_found():
    # MATCH("b", {1;2;3}, 1) is #N/A: no value of the lookup's type
    assert not search(sheet("nums"), "b", 0, 0, 5, M_ASC_LAST_LE)[0]


@pytest.mark.parametrize("v,mode,want", [
    ("cherry", M_ASC_LAST_LE, 2), ("cat", M_ASC_LAST_LE, 1), ("a", M_ASC_LAST_LE, NF),
    ("zz", M_ASC_LAST_LE, 4), ("CAT", M_ASC_FIRST_GE, 2), ("a", M_ASC_FIRST_GE, 0),
    ("zz", M_ASC_FIRST_GE, NF), ("date", M_ASC_EXACT, 3), ("dates", M_ASC_EXACT, NF),
])
def test_binary_text(v, mode, want):
    f, i, _, _ = search(sheet("text"), v, 0, 0, 5, mode)
    assert (i if f else NF) == want


# ---- exact or next smaller / larger, linear (XMATCH match_mode -1 / 1, search_mode 1 / -1)
@pytest.mark.parametrize("v,mode,want", [
    (25, M_FWD_SMALLER, 3), (20, M_FWD_SMALLER, 3), (5, M_FWD_SMALLER, NF), (60, M_FWD_SMALLER, 2),
    (25, M_REV_SMALLER, 6), (20, M_REV_SMALLER, 6), (60, M_REV_SMALLER, 2),
    (25, M_FWD_LARGER, 0), (5, M_FWD_LARGER, 1), (60, M_FWD_LARGER, NF), (45, M_FWD_LARGER, 2),
    (25, M_REV_LARGER, 0), (20, M_REV_LARGER, 6), (15, M_REV_LARGER, 6),
])
def test_next_smaller_larger_numbers(v, mode, want):
    # C1:C7 = 30, 10, 50, 20, 40, "x", 20
    f, i, _, _ = search(sheet("nums"), v, 0, 2, 7, mode)
    assert (i if f else NF) == want


@pytest.mark.parametrize("v,mode,want", [
    ("grape", M_FWD_SMALLER, 2), ("b", M_FWD_SMALLER, 1), ("zz", M_FWD_SMALLER, 0), ("a", M_FWD_SMALLER, NF),
    ("grape", M_FWD_LARGER, 3), ("b", M_FWD_LARGER, 2), ("zz", M_FWD_LARGER, NF), ("KIWI", M_FWD_LARGER, 3),
])
def test_next_smaller_larger_text(v, mode, want):
    # B1:B4 = pear, apple, fig, kiwi
    f, i, _, _ = search(sheet("text"), v, 0, 1, 4, mode)
    assert (i if f else NF) == want


# ---- wildcards (MATCH 0, VLOOKUP FALSE, XMATCH match_mode 2)
@pytest.mark.parametrize("pat,want", [
    ("cherry", 2), ("CHERRY", 2), ("b*", 1), ("*e", 0), ("?ig*", 4), ("*", 0), ("f*~*", 4), ("a~?c", 5),
    ("a?c", 5), ("ab", NF), ("*r*y", 2), ("c*h*r*r*y", 2), ("d?t?", 3), ("~*", NF), ("??", NF),
    ("?????", 0), ("*value*", 8), ("long*here", 8), ("*x", NF), ("", 7), ("fig~", NF), ("a*c", 5),
])
def test_wildcards_forward(pat, want):
    # C1:C9 = apple, Banana, cherry, date, fig*, a?c, abc, "", longer text value here
    f, i, _, _ = search(sheet("text"), pat, 0, 2, 9, M_FWD, wild=True)
    assert (i if f else NF) == want


def test_wildcards_reverse():
    sh = sheet("text")
    assert search(sh, "a*", 0, 2, 9, M_REV, wild=True)[1] == 6    # abc, last a*
    assert search(sh, "*a*", 0, 2, 9, M_REV, wild=True)[1] == 8


def test_wildcards_ignore_numbers():
    # a wildcard pattern only matches text cells
    assert not search(sheet("nums"), "1*", 0, 0, 5, M_FWD, wild=True)[0]
    assert search(sheet("nums"), 30, 0, 0, 5, M_FWD, wild=True)[1] == 2


def test_step_counts_are_logarithmic_for_binary():
    sh = sheet("nums")
    _, _, _, lin = search(sh, 50, 0, 0, 5, M_FWD)
    _, _, _, bsr = search(sh, 50, 0, 0, 5, M_ASC_LAST_LE)
    assert bsr < lin
