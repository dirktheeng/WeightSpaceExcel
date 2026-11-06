"""Shared black-box runner for Stage 3, 4 and 5 conformance cases.

Same protocol as tests/output/test_stage1.py: type each cell's text as keystrokes through
blackbox.py, run to halt, decode cell values from raw memory. Never opens weight files and
computes no expected values. Extra case keys over Stage 1:
  tol:       relative tolerance for numbers (Microsoft examples are printed rounded).
  abs_tol:   absolute tolerance (used where the documented result is near 0).
  requires:  checklist item names; the case is skipped until all are status done.
  settings:  non-default workbook settings (e.g. date1904); skipped until blackbox supports them.
"""
import glob
import math
import os

import yaml

import blackbox as bb

REL_TOL = 1e-12  # docs/ACCEPTANCE.md default


def load(stage_dir, pattern="cases*.yaml"):
    cases = []
    for p in sorted(glob.glob(os.path.join(stage_dir, pattern))):
        with open(p) as f:
            cases += yaml.safe_load(f)["cases"]
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "duplicate case ids"
    return cases


def same(actual, expected, tol=REL_TOL, abs_tol=0.0):
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(actual) is bool and actual is expected
    if isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)):
            return False
        if expected == 0 and abs_tol == 0.0:
            return actual == 0
        return math.isclose(actual, expected, rel_tol=tol, abs_tol=abs_tol)
    return actual == expected


def run_case(case, pytest):
    done = bb.done_items()
    missing = [f for f in case.get("requires", []) if f not in done]
    if missing:
        pytest.skip(f"requires items not done in checklist: {missing}")
    if case.get("settings"):
        if not hasattr(bb, "settings_events"):
            pytest.skip(f"settings {case['settings']} not supported by blackbox.py yet")
    assert bb.manifest_paths() is not None
    h = bb.boot(bb.script(case["cells"], case.get("edits")))
    assert bb.peek(h, bb.FAULT) == 0, f"fault {bb.peek(h, bb.FAULT)}"
    tol = float(case.get("tol", REL_TOL))
    atol = float(case.get("abs_tol", 0.0))
    for addr, exp in case["expect"].items():
        got = bb.value(h, addr)
        assert same(got, exp, tol, atol), f"{case['id']} {addr}: expected {exp!r}, got {got!r}"
    assert bb.peek(h, bb.REJECT_COUNT) == len(case.get("rejected", []))


def format_formula(fmt):
    return '=TEXT(A1,"' + fmt.replace('"', '""') + '")'


def run_format(case, pytest):
    """Number format display case: value typed in A1, format code, expected display text.
    Checked through =TEXT(A1, code) in A2 (TEXT applies the same format engine). Cases marked
    display_only (colors, column-width effects, fill/padding) need a cell display observer."""
    if case.get("display_only"):
        if not hasattr(bb, "display"):
            pytest.skip("display_only: blackbox.py has no cell display observer yet")
        h = bb.boot(bb.script({"A1": case["value"]}) + list(bb.format_events("A1", case["format"])))
        assert bb.display(h, "A1") == case["text"]
        return
    done = bb.done_items()
    missing = [f for f in case.get("requires", ["TEXT"]) if f not in done]
    if missing:
        pytest.skip(f"requires items not done in checklist: {missing}")
    cells = {"A1": case["value"], "A2": format_formula(case["format"])}
    h = bb.boot(bb.script(cells))
    assert bb.peek(h, bb.FAULT) == 0
    got = bb.value(h, "A2")
    assert got == case["text"], f"{case['id']}: {case['format']!r} on {case['value']!r}: expected {case['text']!r}, got {got!r}"
