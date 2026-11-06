"""Run the Stage 1 SUM cases with optional path overrides (output test helper, black box)."""
import os, sys, math, yaml
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402
from harness.harness import Harness  # noqa: E402
import numpy as np  # noqa: E402

CASES_PATH = os.path.join(os.path.dirname(HERE), "stage1", "cases.yaml")
with open(CASES_PATH) as _f:
    CASES = yaml.safe_load(_f)["cases"]
SUM_CASES = [c for c in CASES if "SUM" in c.get("requires", [])]


def run_case(case, overrides=None, max_steps=5_000_000):
    p = bb.manifest_paths()
    for i, q in (overrides or {}).items():
        p[i] = q
    h = Harness(p, events=bb.script(case["cells"], case.get("edits")))
    h.run(0, np.zeros(65), max_steps=max_steps)
    return h


def check(case, h):
    errs = []
    if bb.peek(h, bb.FAULT) != 0:
        errs.append(f"fault {bb.peek(h, bb.FAULT)}")
    for a, exp in case["expect"].items():
        got = bb.value(h, a)
        ok = (got == exp) if not isinstance(exp, (int, float)) or isinstance(exp, bool) else (
            isinstance(got, (int, float)) and not isinstance(got, bool) and math.isclose(got, exp, rel_tol=1e-12, abs_tol=0))
        if not ok:
            errs.append(f"{a}: expected {exp!r} got {got!r}")
    circ = bb.peek(h, bb.CIRC_FLAG)
    if "circular" in case and case["circular"]:
        if circ not in [bb.key_of(a) + 1 for a in case["circular"]]:
            errs.append(f"circ {circ}")
    elif circ != 0:
        errs.append(f"circ {circ}")
    return errs


if __name__ == "__main__":
    ov = {}
    for a in sys.argv[1:]:
        i, q = a.split("=")
        ov[int(i)] = q
    for c in SUM_CASES:
        try:
            h = run_case(c, ov)
            e = check(c, h)
        except Exception as ex:  # noqa: BLE001
            e = [repr(ex)[:200]]
        print(c["id"], "PASS" if not e else "FAIL " + "; ".join(e))
