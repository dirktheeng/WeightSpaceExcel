"""Output tests for harness mem_op 3 (block write) and 4 (block read), harness/FORMAT.md.

Drives the hand-written test networks weights/smoke/blk_*.wt (notes: weights/smoke/blk.md)
through the harness and checks memory, returned outputs and step counts. Never opens weights.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from harness.harness import Harness, MEM_SIZE  # noqa: E402
from blackbox import peek  # noqa: E402

BW = os.path.join(ROOT, "weights", "smoke", "blk_w.wt")
BR = os.path.join(ROOT, "weights", "smoke", "blk_r.wt")
BC = os.path.join(ROOT, "weights", "smoke", "blk_c.wt")
LINE = os.path.join(ROOT, "weights", "smoke", "blk_line.wt")
PAYLOAD = [3.25, -2.0, 1e300, 0.1]
FB, W = 0x100000, 1280


def run(addr, n, p0=3.25):
    trace = []
    h = Harness([BW, BR, BC], trace=trace)
    out = h.run(0, [0, 0, 0, addr, n, p0, 0, 0, 0], max_steps=10)
    return h, out, trace


def test_block_write_then_read_round_trip():
    h, out, trace = run(1000, 4)
    assert [peek(h, 1000 + i) for i in range(4)] == PAYLOAD
    assert peek(h, 999) == 0 and peek(h, 1004) == 0
    assert list(out[7:11]) == PAYLOAD
    assert sum(t.startswith("step") for t in trace) == 3
    assert "bwrite 1000 8 4" in trace and "bread 1000 8 4" in trace


@pytest.mark.parametrize("n", [0, 1, 2, 3])
def test_partial_run_length(n):
    h, out, _ = run(5000, n, p0=-7.5)
    want = [-7.5, -2.0, 1e300, 0.1][:n] + [0.0] * (4 - n)
    assert [peek(h, 5000 + i) for i in range(4)] == want
    assert list(out[7:11]) == want


def test_run_longer_than_payload_is_refused():
    with pytest.raises(IndexError):
        run(1000, 5)


@pytest.mark.parametrize("addr", [-1, MEM_SIZE - 3])
def test_address_range_is_checked(addr):
    with pytest.raises(IndexError):
        run(addr, 4)


def test_block_write_ending_at_last_word():
    h, _, _ = run(MEM_SIZE - 4, 4)
    assert [peek(h, MEM_SIZE - 4 + i) for i in range(4)] == PAYLOAD


def test_full_scanline_in_one_step():
    trace = []
    h = Harness([LINE], trace=trace)
    row = 5
    out = h.run(0, [0, 0, 0, FB + W * row, 0xE1E1E1, 0, 0, 0, 0], max_steps=2)
    assert sum(t.startswith("step") for t in trace) == 1
    assert len(out) == 8 + W
    assert all(peek(h, FB + W * row + x) == 0xE1E1E1 for x in range(W))
    assert peek(h, FB + W * row - 1) == 0 and peek(h, FB + W * (row + 1)) == 0
