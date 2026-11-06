"""Black-box helpers for weights/func/logic output tests.

Each network is a one-step leaf subroutine (encodings/control.md section 4). The harness is given
[network under test, kernel/halt_ok], LR = 1, LP = 5, so the subroutine returns into halt_ok, which
copies words 7..63 and halts. Weight files are only passed to the harness by path, never opened.
Expected values in the tests are stated by hand from Excel's documented behaviour.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402

LOGIC = os.path.join(ROOT, "weights", "func", "logic")
HALT = os.path.join(ROOT, "weights", "kernel", "halt_ok.wt")

# input index of output word w is w + 1
W = {"PC": 7, "LR": 8, "LP": 9, "STATUS": 12, "AT": 13, "AP": 14, "BT": 15, "BP": 16,
     "CT": 17, "CP": 18, "N0": 27, "N1": 28, "T0": 29, "T3": 32, "T4": 33, "T5": 34}
BLANK, NUM, TEXT, BOOL, ERR, REF, ARR, LAM, MISS = range(9)
E = {"#NULL!": 1, "#DIV/0!": 2, "#VALUE!": 3, "#REF!": 4, "#NAME?": 5, "#NUM!": 6, "#N/A": 7}


def call(name, **regs):
    """Run network `name` once as a called subroutine; return (output words, input words)."""
    x = [1000.0 + i for i in range(65)]
    x[0] = 0.0
    x[W["LR"] + 1] = 1.0
    x[W["LP"] + 1] = 5.0
    for k, v in regs.items():
        x[W[k] + 1] = float(v)
    h = Harness([os.path.join(LOGIC, name + ".wt"), HALT])
    out = h.run(0, x, max_steps=2)
    out = [float(v) for v in out]
    assert out[W["PC"]] == 5.0  # returned with PC = LP
    return out, x


def check_pass(out, x, changed):
    for w in range(8, 64):
        if w not in changed:
            assert out[w] == x[w + 1], w


# ---------------- ABI-level driver (encodings/functions.md sections 2 and 6)
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(HERE))
import blackbox as bb  # noqa: E402

FN_RET = 257
WX = {"SP": 53, "TP": 52, "T2": 31, "N0": 27, "P0": 25, "P1": 26, "AS": 19, "AR1": 20, "AC1": 21, "T1": 30}
W.update(WX)


class Abi:
    """Boots the manifest, then enters function networks at PC 0 as FN_CALL would. FN_RET (257)
    is replaced by kernel/halt_ok for these tests (if the ABI agent's FN_RET is not used), so a
    function's return halts with the result in A."""

    def __init__(self):
        paths = list(bb.manifest_paths())
        paths[FN_RET] = HALT
        self.h = Harness(paths)
        self.h.run(0, np.zeros(65), max_steps=200)

    def state(self, **regs):
        x = [0.0] * 65
        for i in range(40, 64):
            x[i + 1] = 5000.0 + i  # preserve-set markers
        x[W["SP"] + 1] = 0x1100
        x[W["TP"] + 1] = 0x98010
        x[W["LR"] + 1] = 3
        for k, v in regs.items():
            x[W[k] + 1] = float(v)
        return x

    def set_cell(self, a1, tag, pay, formula=0):
        r, c = bb.parse_a1(a1)
        x = self.state(AS=0, AR1=r, AC1=c, T1=1, AT=tag, AP=pay, P1=formula, LR=3, LP=0)
        self.h.run(16, x, max_steps=200)

    def key(self, a1):
        r, c = bb.parse_a1(a1)
        return r * 2**14 + c

    def call(self, net, fid, args, max_steps=400):
        """args: list of (tag, pay); the last goes in B, the others on the operand stack."""
        sp = 0x1100
        for i, (t, p) in enumerate(args[:-1]):
            self.h.mem[sp + 2 * i], self.h.mem[sp + 2 * i + 1] = t, p
        sp += 2 * (len(args) - 1) if args else 0
        regs = dict(PC=0, N0=len(args), T2=64 + fid)
        if args:
            regs.update(BT=args[-1][0], BP=args[-1][1])
        x = self.state(**regs)
        x[W["SP"] + 1] = sp
        trace = []
        self.h.trace = trace
        out = self.h.run(net, x, max_steps=max_steps)
        self.h.trace = None
        out = [float(v) for v in out]
        steps = sum(1 for t in trace if str(t).startswith("step"))
        for w in [10, 11, 22, 24, 26, 27] + list(range(40, 64)):
            if w == 53:
                assert out[w] == sp, "SP changed"
            else:
                assert out[w] == x[w + 1], ("preserve", w)
        return (out[W["AT"]], out[W["AP"]]), steps
