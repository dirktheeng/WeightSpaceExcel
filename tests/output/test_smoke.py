"""Output test: runs weights/smoke/add.wt through the harness; checks memory only."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402
from blackbox import peek  # noqa: E402

NET = os.path.join(ROOT, "weights", "smoke", "add.wt")


def run(a, b):
    trace = []
    h = Harness([NET], trace=trace)
    h.run(0, [0, a, b, 0, 0, 0, 0, 0], max_steps=10)
    return h, trace


def test_adds_and_halts():
    h, trace = run(2, 3)
    assert peek(h, 0) == 5
    assert sum(t.startswith("step") for t in trace) == 1


def test_negative_and_fraction():
    h, _ = run(-1.25, 0.5)
    assert peek(h, 0) == -0.75
    assert peek(h, 1) == 0
