"""NOW and TODAY (dt_now, id 349). Clock values stated by hand: Unix time 1735689600 is
2025-01-01T00:00:00Z, which is serial 45658 (Unix epoch 1970-01-01 is serial 25569)."""
from dtbb import result, call, NUM, W

NOW = 349
CLOCK = 0x301000


def test_now_from_clock_word():
    # enter at PC 1 (skip the io request) with a clock value placed by the test
    assert result(NOW, regs={"PC": 1}, sel=0, mem={CLOCK: 1735689600}) == (NUM, 45658.0)
    assert result(NOW, regs={"PC": 1}, sel=0, mem={CLOCK: 1735689600 + 43200}) == (NUM, 45658.5)
    assert result(NOW, regs={"PC": 1}, sel=1, mem={CLOCK: 1735689600 + 43200}) == (NUM, 45658)
    assert result(NOW, regs={"PC": 1}, sel=1, mem={CLOCK: 1735689600}) == (NUM, 45658)
    assert result(NOW, regs={"PC": 1}, sel=1, mem={CLOCK: 1735689599.5}) == (NUM, 45657)
    assert result(NOW, regs={"PC": 1}, sel=0, mem={CLOCK: 0}) == (NUM, 25569)
    tag, v = result(NOW, regs={"PC": 1}, sel=0, mem={CLOCK: 1735689600 + 21600.25})
    assert tag == NUM and abs(v - 45658.250002893519) < 1e-9   # 6:00:00.25


def test_now_live_clock():
    # full path: io 4 then read. Real time is after 2025-01-01 and before 2100-01-01.
    tag, v = result(NOW, sel=0)
    assert tag == NUM and 45658 < v < 73051
    tag, d = result(NOW, sel=1)
    assert tag == NUM and d == int(d) and 45658 <= d < 73051 and d <= v + 1


def test_now_steps_and_return():
    out, h = call(NOW, sel=0, regs={"LP": 7})
    assert out[W["PC"]] == 7      # returned to LP (HALT_OK copies PC)
