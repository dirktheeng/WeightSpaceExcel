"""Black-box output tests for the control kernel and cell store (weights/kernel/).

Runs kernel networks through the frozen harness and checks memory words and returned
state words only. Never opens weight files. Expected values come from the documented
layouts (encodings/control.md, memory-map.md, address.md, io.md), not from weights.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import kernel_ids as k  # noqa: E402
import blackbox as bb  # noqa: E402

HALT_OK = 3


def harness(events=()):
    h = k.Harness(k.paths(), events=list(events))
    h.trace = []
    return h


def nsteps(h):
    return sum(t.startswith("step") for t in h.trace)


def run(h, net, x, max_steps=100):
    h.trace.clear()
    return h.run(net, x, max_steps=max_steps)


# ---------- BOOT, TRAP, RET, HALT_OK

def test_boot_initialises_zero_page_and_halts_on_empty_queue():
    h = harness()
    out = run(h, 0, np.zeros(65))
    m = h.mem
    assert m[0x00] == 0                      # FAULT
    assert m[0x01] == 0x302002               # HEAP_TOP
    assert m[0x02] == 0x090000               # FORMULA_TOP
    assert m[0x04] == 0x0C0000               # DEP_TOP
    assert m[0x05] == 512                    # NET_NEXT
    assert m[0x0A] == 100                    # ITER_MAX
    assert m[0x0B] == 0.001                  # ITER_DELTA
    assert m[0x0D] == 0x0B0000               # SCRATCH_TOP
    assert m[0x0F] == 1                      # SHEET_COUNT
    assert m[0x11] == 0x3C0000               # STAGING_TOP
    assert m[0x0C] == 0 and m[0x14] == 0     # CELL_COUNT, REJECT_COUNT
    assert out[k.RSP] == 0x100 and out[k.MODE] == 1
    assert nsteps(h) == 14                   # 10 boot + poll + count + first + halt


def test_trap_writes_fault_and_halts():
    h = harness()
    run(h, 1, k.regs(T0=6))
    assert h.mem[0] == 6 and nsteps(h) == 1


def test_ret_unpacks_link():
    h = harness()
    x = k.regs(ATAG=1, APAY=2.5)
    for lp in (0, 7, 65535):
        x[0] = HALT_OK * 65536 + lp
        out = run(h, 2, x)
        assert out[k.PC] == lp and out[k.ATAG] == 1 and out[k.APAY] == 2.5
        assert nsteps(h) == 2               # RET, then HALT_OK


def test_halt_ok_preserves_state():
    h = harness()
    x = np.arange(65, dtype=float)
    out = run(h, HALT_OK, x)
    assert list(out[7:]) == list(x[8:])
    assert out[6] == 1


# ---------- cell store

def cset(h, row, col, tag, pay, p1=0, sheet=0):
    out = run(h, 16, k.regs(LR=HALT_OK, LP=5, T1=1, ATAG=tag, APAY=pay, P1=p1, AS=sheet, AR1=row, AC1=col))
    return out


def cget(h, row, col, sheet=0):
    out = run(h, 16, k.regs(LR=HALT_OK, LP=9, T1=0, ATAG=7, APAY=7, AS=sheet, AR1=row, AC1=col))
    return out


def test_set_then_get_roundtrip():
    h = harness()
    cases = [(0, 0, 1, -0.1), (4, 1, 1, 1e300), (1048575, 16383, 3, 1), (7, 3, 4, 7), (12, 2, 2, 0x302002)]
    for r, c, tag, pay in cases:
        out = cset(h, r, c, tag, pay, p1=0x090010)
        assert out[k.STATUS] == 0 and out[k.PC] == 5
        assert nsteps(h) == 10               # new cell: hash, probe, 7 writes and reads, halt
    for r, c, tag, pay in cases:
        out = cget(h, r, c)
        assert out[k.STATUS] == 0 and out[k.PC] == 9
        assert out[k.ATAG] == tag and out[k.APAY] == pay
        assert nsteps(h) == 5                # hash, probe, tag, pay, halt
        s = k.slot_of(h.mem, 0, r, c)
        base = k.CELL_BASE + 8 * s
        assert h.mem[base + 3] == 0x090010   # FORMULA word = P1
        assert h.mem[base + 6] == 1          # CALC = 4 * CALC_GEN + 1 (dirty), CALC_GEN 0
    assert h.mem[0x0C] == len(cases)         # CELL_COUNT


def test_get_missing_returns_blank_not_found():
    h = harness()
    cset(h, 2, 2, 1, 5.0)
    out = cget(h, 3, 3)
    assert out[k.STATUS] == 1 and out[k.ATAG] == 0 and out[k.APAY] == 0 and out[k.PC] == 9
    assert nsteps(h) == 3


def test_overwrite_keeps_count():
    h = harness()
    cset(h, 9, 4, 1, 1.0)
    out = cset(h, 9, 4, 3, 0.0)
    assert nsteps(h) == 7                    # existing cell: hash, probe (writes TAG), PAY, FORMULA, gen, CALC, halt
    assert h.mem[0x0C] == 1
    out = cget(h, 9, 4)
    assert out[k.ATAG] == 3 and out[k.APAY] == 0


def test_collision_probes_linearly():
    # rows 0 and 65536 of column 0 have the same hash slot (40503 * 65536 = 0 mod 2^16)
    h = harness()
    cset(h, 0, 0, 1, 11.0)
    cset(h, 65536, 0, 1, 22.0)
    cset(h, 131072, 0, 1, 33.0)
    assert k.slot_of(h.mem, 0, 65536, 0) == 1 and k.slot_of(h.mem, 0, 131072, 0) == 2
    out = cget(h, 131072, 0)
    assert out[k.APAY] == 33.0 and nsteps(h) == 7   # two extra probes
    out = cget(h, 196608, 0)
    assert out[k.STATUS] == 1


def test_probe_wraps_at_table_end():
    def slot(r, c):
        return (40503 * r + 65599 * c) % 65536
    r1 = next(r for r in range(65536) if slot(r, 0) == 65535)
    h = harness()
    cset(h, r1, 0, 1, 1.5)
    cset(h, r1 + 65536, 0, 1, 2.5)
    assert k.slot_of(h.mem, 0, r1 + 65536, 0) == 0
    out = cget(h, r1 + 65536, 0)
    assert out[k.APAY] == 2.5 and out[k.STATUS] == 0


def test_sheets_are_separate():
    h = harness()
    cset(h, 1, 1, 1, 10.0, sheet=0)
    cset(h, 1, 1, 1, 20.0, sheet=3)
    assert cget(h, 1, 1, sheet=0)[k.APAY] == 10.0
    assert cget(h, 1, 1, sheet=3)[k.APAY] == 20.0


def test_cell_store_preserves_locals():
    h = harness()
    x = k.regs(LR=HALT_OK, LP=5, T1=1, ATAG=1, APAY=3.0, AR1=1, AC1=1)
    x[41:65] = np.arange(24) + 100.0         # L0..L23
    h.trace.clear()
    out = h.run(16, x, max_steps=50)
    assert list(out[40:64]) == list(x[41:65])


# ---------- main loop (encodings/io.md protocol)

def boot(events, max_steps=20000):
    h = harness(events)
    h.run(0, np.zeros(65), max_steps=max_steps)
    return h


def test_text_entry_via_goto():
    h = boot(bb.enter("B3", "hello") + bb.enter("A1", "x") + bb.enter("C2", "abcdefg"))
    assert bb.value(h, "B3") == "hello"
    assert bb.value(h, "A1") == "x"
    assert bb.value(h, "C2") == "abcdefg"
    assert h.mem[0] == 0 and h.mem[0x0C] == 3
    s = bb.slot_of(h, "C2")
    # CALC word is 4*CALC_GEN + 1 (address.md); with recalculation hooked in,
    # CALC_GEN advances past 0, so check the dirty bit, not the whole word.
    assert h.mem[k.CELL_BASE + 8 * s + 6] % 4 == 1   # dirty


def test_strings_are_contiguous_in_heap():
    h = boot(bb.enter("A1", "abc") + bb.enter("A2", "de"))
    a1 = bb.slot_of(h, "A1")
    a2 = bb.slot_of(h, "A2")
    assert h.mem[k.CELL_BASE + 8 * a1 + 2] == 0x302002
    assert h.mem[k.CELL_BASE + 8 * a2 + 2] == 0x302002 + 3   # header 2 words + 1 packed word
    assert h.mem[1] == 0x302002 + 3 + 3                      # HEAP_TOP


def test_lowercase_and_multiletter_goto():
    h = boot(bb.enter("aa10", "p") + bb.enter("XFD1048576", "q") + bb.enter("Z9", "r"))
    assert bb.value(h, "AA10") == "p"
    assert bb.value(h, "XFD1048576") == "q"
    assert bb.value(h, "Z9") == "r"


def test_enter_moves_down_and_typing_continues():
    ev = bb.goto("C5") + bb.type_text("one") + bb.press(bb.VK_ENTER) + bb.type_text("two") + bb.press(bb.VK_ENTER)
    ev += bb.press(bb.VK_ENTER) + bb.type_text("four") + bb.press(bb.VK_ENTER)
    h = boot(ev)
    assert bb.value(h, "C5") == "one"
    assert bb.value(h, "C6") == "two"
    assert bb.value(h, "C7") == {"blank": True}
    assert bb.value(h, "C8") == "four"


def test_delete_clears_cell():
    h = boot(bb.enter("D4", "keep") + bb.enter("E4", "gone") + bb.enter("E4", ""))
    assert bb.value(h, "D4") == "keep"
    assert bb.value(h, "E4") == {"blank": True}


def test_overwrite_cell_text():
    h = boot(bb.enter("A1", "first") + bb.enter("A1", "second"))
    assert bb.value(h, "A1") == "second"
    assert h.mem[0x0C] == 1


def test_unicode_and_punctuation_units():
    text = "=1+2 é€😀"
    h = boot(bb.enter("B2", text))
    assert bb.value(h, "B2") == text


def test_non_key_events_ignored():
    mouse = [float(4 * 2**48 + 10 + 2**16 * 20 + 2**32), float(5 * 2**48 + 10 + 2**16 * 20 + 2**32)]
    h = boot(mouse + bb.enter("A3", "m") + mouse)
    assert bb.value(h, "A3") == "m" and h.mem[0] == 0


def test_long_queue_crosses_event_chunks():
    cells = {f"A{i}": f"v{i}" for i in range(1, 241)}   # more than 4095 event words
    ev = bb.script(cells)
    assert len(ev) > 4095
    h = boot(ev, max_steps=200000)
    for a, t in cells.items():
        assert bb.value(h, a) == t
    assert h.mem[0x0C] == 240 and h.mem[0] == 0
