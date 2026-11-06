"""Stage 3 and 4 format cases (tests/output/stage3/formats.yaml, stage4/formats.yaml) run
black-box against fx_main (198) directly, without the TEXT function or a cell renderer.

Each case's value is entered as an engine input value: plain numbers as numbers, TRUE/FALSE
as booleans, other text as a text value. Formula values ("=...") are skipped (they need the
evaluator). The code string goes into a FMT_TABLE entry (General uses format id 0). Expected
text comes from the YAML only. display_only cases use W = col_width (default 10 characters,
README.md); other cases use W = 0 (TEXT). Never opens weight files.
"""
import os

import pytest
import yaml

import fmtbb as f

HERE = os.path.dirname(os.path.abspath(__file__))
FT, CODE, HEAP0, TXT = 0xC000, 0x300000, 0x310000, 0x302300


def load(stage):
    with open(os.path.join(HERE, "..", stage, "formats.yaml")) as fh:
        return yaml.safe_load(fh)["cases"]


CASES = [pytest.param(c, id=c["id"]) for st in ("stage3", "stage4") for c in load(st)]


def value_of(h, v):
    v = str(v)
    if v.startswith("="):
        pytest.skip("formula value needs the evaluator")
    if v.upper() in ("TRUE", "FALSE"):
        return 3, float(v.upper() == "TRUE")
    try:
        return 1, float(v)
    except ValueError:
        f.put_str(h, TXT, v)
        return 2, TXT


def show(case):
    h = f.harness()
    h.mem[1] = HEAP0
    h.run(199, f.regs(LR=f.HALT_OK), max_steps=5000)  # fx_init (boot)
    tag, pay = value_of(h, case["value"])
    code = case["format"]
    F = 0
    if code != "General":
        F = 170
        f.put_str(h, CODE, code)
        h.mem[FT + 4 * F] = CODE
    W = int(case.get("col_width", 10)) if case.get("display_only") else 0
    out = h.run(198, f.regs(ATAG=tag, APAY=pay, BTAG=F, BPAY=W, LR=f.HALT_OK), max_steps=20000)
    a = int(f.reg(out, "APAY"))
    if int(f.reg(out, "STATUS")) == 1:
        if tag == 2:
            return f.get_str(h, a)
        return {3: ("FALSE", "TRUE")[int(pay)] if tag == 3 else None}.get(tag, "")
    return f.get_str(h, a)


@pytest.mark.parametrize("case", CASES)
def test_stage_format(case):
    assert show(case) == str(case["text"])
