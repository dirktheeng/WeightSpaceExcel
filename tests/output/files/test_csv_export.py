"""Output tests for CSV export (xp_imp 455 -> xp_scan, xp_cell, xp_str, xp_err; return via csv_ret 454).

Black box: cells are entered by key events through the booted engine, then the exporter is
called with LR = HALT_OK and N0 = file id 0. The harness writes the file bytes on io 3; the
test compares them with bytes stated by hand from Excel's "CSV UTF-8" save behaviour:
used range from A1, comma separated, CRLF after every row, a field quoted only when it holds
a comma, quote, CR or LF, with each quote doubled. Numbers use the General 15-digit text.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from blackbox import Harness, manifest_paths, script  # noqa: E402


def export(cells, tmp_path):
    out = str(tmp_path / "out.csv")
    h = Harness(manifest_paths(), files=[out], events=script(cells))
    h.run(0, np.zeros(65), max_steps=5_000_000)
    x = np.zeros(65)
    x[9], x[10], x[11] = 3, 0, 0x100      # LR = HALT_OK, LP, RSP
    x[28] = 0                             # N0 = file id
    for i in range(12):
        x[41 + i] = 900 + i
    trace = []
    h.trace = trace
    h.run(455, x, max_steps=3_000_000)
    with open(out, "rb") as f:
        data = f.read()
    return data, h, trace


def test_basic_grid(tmp_path):
    data, _, _ = export({"A1": "a", "B1": "1", "A2": "2.5", "B2": "TRUE"}, tmp_path)
    assert data == b"a,1\r\n2.5,TRUE\r\n"


def test_blank_cells_inside_used_range(tmp_path):
    data, _, _ = export({"A1": "x", "C2": "y"}, tmp_path)
    assert data == b"x,,\r\n,,y\r\n"


def test_quoting_and_formula_value(tmp_path):
    data, _, _ = export({"A1": 'say "hi", ok', "B1": "=1/0", "C1": "=2*3"}, tmp_path)
    assert data == b'"say ""hi"", ok",#DIV/0!,6\r\n'


def test_utf8_and_long_text(tmp_path):
    data, _, _ = export({"A1": "café €", "A2": "abcdefghij"}, tmp_path)
    assert data == "café €\r\nabcdefghij\r\n".encode("utf-8")


def test_empty_sheet_and_return(tmp_path):
    data, h, trace = export({}, tmp_path)
    assert data == b""
    last = [t for t in trace if t.startswith("step") and " net 454 " in t][-1]
    words = eval(last.split(" out ")[1], {"np": np})
    assert words[0] == 3 and words[10] == 0x100 and words[12] == 0
    assert list(words[40:52]) == [900 + i for i in range(12)]
