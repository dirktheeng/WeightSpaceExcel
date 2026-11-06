"""Aggregate-function output tests (black box): run each case through the full manifest and compare
cell values with expected values typed by hand from Excel's documented behaviour."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "func"))
import yaml  # noqa: E402
import sumrun  # noqa: E402

with open(os.path.join(HERE, "cases.yaml")) as _f:
    CASES = yaml.safe_load(_f)["cases"]


def run(ids=None):
    out = []
    for c in CASES:
        if ids and c["id"] not in ids:
            continue
        try:
            h = sumrun.run_case(c)
            e = sumrun.check(c, h)
        except Exception as ex:  # noqa: BLE001
            e = [repr(ex)[:300]]
        out.append((c["id"], e))
    return out


if __name__ == "__main__":
    for i, e in run(sys.argv[1:]):
        print(i, "PASS" if not e else "FAIL " + "; ".join(e))
