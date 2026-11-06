"""Every function name in checklist/CHECKLIST.csv parses to OPC 64 + fid (fid = FN number).

Black box: drives the parser entry (78) after the boot-time FUNC_TABLE chain (259) and decodes the
token stream from memory by the documented layout (encodings/memory-map.md section 6). Names and
fids come from the checklist; nothing is computed from weights.
"""
import os
import sys

import numpy as np
import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402
from harness.harness import Harness  # noqa: E402

PATHS = bb.manifest_paths()
HS, FT0 = 0x30D400, 0x090000


NAMES_PATH = os.path.join(HERE, "names.yaml")


def names():
    with open(NAMES_PATH) as f:
        return [tuple(x) for x in yaml.safe_load(f)["names"]]


NAMES = names()


def parse(text):
    h = Harness(PATHS)
    x = np.zeros(65)
    x[1 + 8] = 3
    h.run(259, x, max_steps=100)
    m = h.mem
    units = [ord(c) for c in text]
    m[HS], m[HS + 1] = len(units), 1
    for i in range(0, len(units), 3):
        u = units[i:i + 3] + [0, 0]
        m[HS + 2 + i // 3] = u[0] + u[1] * 2**16 + u[2] * 2**32
    m[1], m[2] = HS + 2 + (len(units) + 2) // 3, FT0
    x = np.zeros(65)
    x[1 + 8], x[1 + 10], x[1 + 13], x[1 + 14] = 3, 0x100, 2, HS
    out = h.run(78, x, max_steps=20000)
    if out[12] != 0:
        return None
    rec = int(out[26])
    a, n = int(m[rec + 1]), int(m[rec + 2])
    return [(int(m[a + 2 * i]), float(m[a + 2 * i + 1])) for i in range(n + 1)]


def test_525_names():
    assert len(NAMES) == 525


@pytest.mark.parametrize("name,fid", NAMES, ids=[n for n, _ in NAMES])
def test_name_parses_to_fid(name, fid):
    toks = parse(f"={name}(1)")
    assert toks == [(1, 1.0), (64 + fid, 1.0), (0, 0.0)], toks


@pytest.mark.parametrize("text,fid", [("=sum(1)", 441), ("=Norm.S.Dist(1)", 330), ("=log10(1)", 285),
                                      ("=forecast.ets.seasonality(1)", 185)])
def test_case_folding(text, fid):
    assert parse(text)[1] == (64 + fid, 1.0)


@pytest.mark.parametrize("text", ["=FOO(1)", "=SUMM(1)", "=SU(1)", "=NORM.S(1)"])
def test_unknown_name_is_fid_0(text):
    assert parse(text)[1] == (64, 1.0)


@pytest.mark.parametrize("text", ["=A1(1)", "=XFD1(1)"])
def test_reference_with_paren_rejected(text):
    assert parse(text) is None
