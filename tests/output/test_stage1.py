"""Stage 1 black-box output tests (docs/RULES.md rule 2, protocol in encodings/io.md).

For each case in stage1/cases.yaml: boot the manifest weights/MANIFEST.txt through the
harness, type every cell's text as keystroke events (Ctrl+G go-to, text, Enter), run
until the engine halts at end of input, then decode cell values from raw memory words.
Never opens weight files; computes no expected values.
"""
import math
import os

import pytest
import yaml

import blackbox as bb

CASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stage1", "cases.yaml")
with open(CASES_PATH) as _f:
    CASES = yaml.safe_load(_f)["cases"]
REL_TOL = 1e-12  # docs/ACCEPTANCE.md
PATHS = bb.manifest_paths()
DONE = bb.done_items()


def _same(actual, expected):
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(actual) is bool and actual is expected
    if isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)):
            return False
        if expected == 0:
            return actual == 0
        return math.isclose(actual, expected, rel_tol=REL_TOL, abs_tol=0.0)
    return actual == expected


@pytest.mark.xfail(PATHS is None, reason="weights/MANIFEST.txt missing: engine not built", strict=False)
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case(case):
    missing = [f for f in case.get("requires", []) if f not in DONE]
    if missing:
        pytest.skip(f"requires functions not done in checklist: {missing}")
    assert PATHS is not None
    h = bb.boot(bb.script(case["cells"], case.get("edits")))
    assert bb.peek(h, bb.FAULT) == 0, f"fault {bb.peek(h, bb.FAULT)}"
    for addr, exp in case["expect"].items():
        got = bb.value(h, addr)
        assert _same(got, exp), f"{case['id']} {addr}: expected {exp!r}, got {got!r}"
    circ = bb.peek(h, bb.CIRC_FLAG)
    if "circular" in case:
        assert circ in [bb.key_of(a) + 1 for a in case["circular"]], circ
    else:
        assert circ == 0
    assert bb.peek(h, bb.REJECT_COUNT) == len(case.get("rejected", []))
