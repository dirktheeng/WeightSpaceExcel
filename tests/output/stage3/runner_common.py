"""Shared black-box runner for Stage 3, 4 and 5 conformance cases.

Same protocol as tests/output/test_stage1.py: type each cell's text as keystrokes through
blackbox.py, run to halt, decode cell values from raw memory. Never opens weight files and
computes no expected values. Extra case keys over Stage 1:
  tol:       relative tolerance for numbers (Microsoft examples are printed rounded).
  abs_tol:   absolute tolerance (used where the documented result is near 0).
  requires:  checklist item names; the case is skipped until all are status done.
  settings:  workbook settings applied as keystrokes via blackbox.settings_events / format_events.
"""
import math

import yaml

import blackbox as bb

REL_TOL = 1e-12  # docs/ACCEPTANCE.md default


def merge(*docs):
    """Concatenate the case lists of already parsed YAML documents; ids must be unique."""
    cases = []
    for d in docs:
        cases += d["cases"]
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


def _events(case):
    """Cell entries, with settings applied before (date1904, precision) or after (autosum)."""
    before, after = [], []
    for st in case.get("settings", []):
        if st == "autosum_keystroke":
            after += bb.settings_events(st, addr=case.get("autosum_at", "A4"))
        elif st.startswith("A1 format "):
            after += bb.format_events("A1", st[len("A1 format "):])
        else:
            before += bb.settings_events(st)
    return before + bb.script(case["cells"], case.get("edits")) + after


def run_case(case, pytest):
    done = bb.done_items()
    missing = [f for f in case.get("requires", []) if f not in done]
    if missing:
        pytest.skip(f"requires items not done in checklist: {missing}")
    assert bb.manifest_paths() is not None
    h = bb.boot(_events(case))
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
    display_only (colors, column-width effects, fill/padding) read the cell display string."""
    done = bb.done_items()
    if case.get("display_only"):
        if not bb.display_available():
            pytest.skip("display_only: no documented display-string location yet (blackbox.DISPLAY_TABLE)")
        if case["item"] not in done:
            pytest.skip(f"requires item not done: {case['item']}")
        ev = bb.script({"A1": case["value"]})
        if case.get("format", "General") != "General":
            ev += bb.format_events("A1", case["format"])
        if "col_width" in case:
            ev += bb.width_events("A1", case["col_width"])
        h = bb.boot(ev)
        assert bb.peek(h, bb.FAULT) == 0
        got = bb.display(h, "A1")
        assert got == case["text"], f"{case['id']}: expected {case['text']!r}, got {got!r}"
        return
    missing = [f for f in case.get("requires", ["TEXT"]) if f not in done]
    if missing:
        pytest.skip(f"requires items not done in checklist: {missing}")
    cells = {"A1": case["value"], "A2": format_formula(case["format"])}
    h = bb.boot(bb.script(cells))
    assert bb.peek(h, bb.FAULT) == 0
    got = bb.value(h, "A2")
    assert got == case["text"], f"{case['id']}: {case['format']!r} on {case['value']!r}: expected {case['text']!r}, got {got!r}"
