"""Black-box output tests for the stage 2 UI networks (weights/ui/, ids 128..169).

Drives networks only through the frozen harness and checks framebuffer and buffer words
against hand-stated expectations from the layout decision record (log/WORKLOG.md, U1).
Never opens weight files. Until the kernel hooks exist (boot -> 152, ev_next -> 153) the
test plays their role by calling run(152) after boot and run(153) after an event batch.
"""
import numpy as np
import pytest

import ui_util as u  # noqa: E402 (adds tests/output to sys.path)
import blackbox as bb  # noqa: E402

GREEN, RIB, BRD, WH, BOX, HDR, GRID, HT, BLACK = (
    0x217346, 0xF3F3F3, 0xD4D4D4, 0xFFFFFF, 0xC6C6C6, 0xEFEFEF, 0xE1E1E1, 0x444444, 0)
BUF = 0x0F0100


def cx(c):
    return 31 + 64 * c


def ry(r):
    return 196 + 20 * r


def ink(fb, x0, x1, y0, y1, color):
    """Pixels of `color` inside the inclusive box, as (x, y) list."""
    out = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if fb[u.W * y + x] == color:
                out.append((x, y))
    return out


def cell_set(h, row, col, tag, pay):
    """Store a value through the kernel CELL_SET path (network 16), as a caller would."""
    x = u.regs(LR=u.HALT_OK, AR1=row, AC1=col, T1=1, ATAG=tag, APAY=pay)
    h.run(16, x, max_steps=100)


@pytest.fixture(scope="module")
def frames():
    ev = bb.script({"A1": "Item", "B1": "Qty", "A2": "Apples", "D5": "hello world", "C3": "=1+2"}) + bb.goto("A2")
    h = u.harness(ev)
    out, n_engine = u.run_counted(h, 0, np.zeros(65))
    cell_set(h, 2, 1, 1, 12.5)          # B3 = 12.5 (number)
    cell_set(h, 3, 1, 1, -1 / 3)        # B4 = -1/3
    cell_set(h, 4, 2, 3, 1)             # C5 = TRUE
    cell_set(h, 5, 2, 4, 7)             # C6 = #N/A
    x = np.concatenate([[0], out]); x[u.REG["PC"] + 1] = 0
    out, n_full = u.run_counted(h, 152, x)
    full = h.mem[u.FB:u.FB + u.W * u.H].astype(np.int64).copy()
    u.dump_png(h, "test_full.png")
    full_fault = h.mem[0]
    h.events = bb.script({"C9": "new", "A1": ""}) + bb.goto("C3")
    out, _ = u.run_counted(h, 4, np.concatenate([[0], out]))
    out, n_inc = u.run_counted(h, 153, np.concatenate([[0], out]))
    inc = h.mem[u.FB:u.FB + u.W * u.H].astype(np.int64).copy()
    u.dump_png(h, "test_incremental.png")
    return dict(full=full, inc=inc, n_full=n_full, n_inc=n_inc, fault=(full_fault, h.mem[0]),
                aw=(h.mem[0x40], h.mem[0x41]))


def px(fb, x, y):
    return int(fb[u.W * y + x])


def test_no_fault_and_step_counts(frames):
    assert frames["fault"] == (0, 0)
    assert frames["n_full"] < 1_200_000
    assert frames["n_inc"] < 60_000


def test_chrome_colours(frames):
    fb = frames["full"]
    assert px(fb, 5, 5) == GREEN and px(fb, 1270, 50) == GREEN       # title bar, tab strip
    assert px(fb, 60, 33) == RIB                                       # selected Home tab
    assert px(fb, 600, 100) == RIB and px(fb, 600, 147) == BRD        # ribbon body, border
    assert px(fb, 3, 160) == BOX and px(fb, 1276, 160) == BOX         # name box, formula box borders
    assert px(fb, 130, 150) == WH                                      # formula band
    assert px(fb, 600, 756) == BRD and px(fb, 600, 790) == RIB        # tab bar line, status bar
    assert px(fb, 62, 760) == WH and px(fb, 62, 777) == GREEN         # Sheet1 tab and underline


def test_grid_geometry(frames):
    fb = frames["full"]
    for c in range(19):                       # vertical gridlines at 31 + 64 c + 63
        assert px(fb, cx(c) + 63, 400) == GRID
        assert px(fb, cx(c) + 62, 400) == WH
    for r in range(27):                       # horizontal gridlines at 196 + 20 r + 19
        assert px(fb, 1000, ry(r) + 19) == GRID
        assert px(fb, 1000, ry(r) + 18) == WH
    assert px(fb, 1000, ry(10) + 5) == WH


def test_headers(frames):
    fb = frames["full"]
    assert px(fb, 33, 178) == HDR and px(fb, 2, 300) == HDR           # header fills
    assert px(fb, 94, 185) == BRD and px(fb, 30, 300) == BRD          # separators
    assert px(fb, 300, 195) == BRD and px(fb, 10, 215) == BRD
    for c in range(20):                       # a letter in every column header, centred
        pts = ink(fb, cx(c), min(cx(c) + 62, 1279), 176, 194, HT)
        assert pts, f"no header letter in column {c}"
        if c < 19:
            mid = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
            assert abs(mid - (cx(c) + 31)) <= 2
    for r in range(28):                       # a number in every row header
        assert ink(fb, 0, 29, ry(r), ry(r) + 18, HT), f"no row number {r + 1}"
    # row 10 has two digits, row 9 one: wider ink span
    w9 = ink(fb, 0, 29, ry(8), ry(8) + 18, HT)
    w10 = ink(fb, 0, 29, ry(9), ry(9) + 18, HT)
    assert max(p[0] for p in w10) - min(p[0] for p in w10) > max(p[0] for p in w9) - min(p[0] for p in w9)


def test_cell_text_alignment(frames):
    fb = frames["full"]
    t = ink(fb, cx(0), cx(0) + 62, ry(1), ry(1) + 18, BLACK)          # A2 "Apples": left
    assert t and min(p[0] for p in t) <= cx(0) + 3
    n = ink(fb, cx(1), cx(1) + 62, ry(2), ry(2) + 18, BLACK)          # B3 12.5: right
    assert n and max(p[0] for p in n) >= cx(1) + 58 and min(p[0] for p in n) > cx(1) + 30
    m = ink(fb, cx(1), cx(1) + 62, ry(3), ry(3) + 18, BLACK)          # B4 -0.33333333: 11 chars
    assert m and min(p[0] for p in m) < cx(1) + 15
    b = ink(fb, cx(2), cx(2) + 62, ry(4), ry(4) + 18, BLACK)          # C5 TRUE: centred
    mid = (min(p[0] for p in b) + max(p[0] for p in b)) / 2
    assert abs(mid - (cx(2) + 31)) <= 2
    e = ink(fb, cx(2), cx(2) + 62, ry(5), ry(5) + 18, BLACK)          # C6 #N/A: centred
    assert abs((min(p[0] for p in e) + max(p[0] for p in e)) / 2 - (cx(2) + 31)) <= 2
    # text stays inside the cell interior: baseline band
    assert all(ry(1) + 5 <= p[1] <= ry(1) + 16 for p in t)
    # D5 "hello world" is clipped at its cell's right edge
    hw = ink(fb, cx(3), cx(4) + 62, ry(4), ry(4) + 18, BLACK)
    assert hw and max(p[0] for p in hw) <= cx(3) + 61


def test_active_cell_outline(frames):
    fb = frames["full"]
    x, y = cx(0), ry(1)                       # A2 (left edge clamped to x 31)
    for p in [(x, y + 9), (x + 62, y + 9), (x + 63, y + 9),
              (x + 30, y - 1), (x + 30, y), (x + 30, y + 18), (x + 30, y + 19),
              (x + 65, y + 21), (x + 61, y + 17)]:
        assert px(fb, *p) == GREEN, p
    assert px(fb, x + 1, y + 9) == WH and px(fb, 30, y + 9) == BRD  # column A: left ring clamped to x 31


def test_formula_bar_and_name_box(frames):
    fb = frames["full"]
    assert len(ink(fb, 4, 103, 152, 171, BLACK)) > 20                # "A2"
    fx = ink(fb, 161, 1275, 152, 171, BLACK)                          # "Apples"
    assert fx and min(p[0] for p in fx) <= 166 and max(p[0] for p in fx) < 220
    fi = frames["inc"]
    assert len(ink(fi, 4, 103, 152, 171, BLACK)) > 20                 # "C3"
    fz = ink(fi, 161, 1275, 152, 171, BLACK)                          # "=1+2" (formula text)
    assert fz and min(p[0] for p in fz) <= 166


def test_incremental_redraw(frames):
    fb, fi = frames["full"], frames["inc"]
    assert ink(fi, cx(0), cx(0) + 62, ry(0), ry(0) + 18, BLACK) == []   # A1 cleared
    assert ink(fi, cx(2), cx(2) + 62, ry(8), ry(8) + 18, BLACK)         # C9 "new"
    x, y = cx(0), ry(1)                                                 # old outline (A2) erased
    assert px(fi, x, y + 9) == WH and px(fi, 30, y + 9) == BRD
    assert px(fi, x + 63, y + 9) == GRID and px(fi, x + 65, y + 21) == WH
    assert px(fi, cx(2) - 1, ry(2) + 9) == GREEN                        # new outline at C3
    assert frames["aw"] == (2, 2)
    # unchanged cells were not repainted wrongly
    a2 = ink(fb, cx(0), cx(0) + 62, ry(1), ry(1) + 18, BLACK)
    assert ink(fi, cx(0), cx(0) + 62, ry(1), ry(1) + 18, BLACK) == a2


# ---------- leaf networks


def read_buf(h, start=BUF):
    s, i = "", 0
    while h.mem[start + i]:
        s += chr(int(h.mem[start + i])); i += 1
    return s


@pytest.mark.parametrize("x,text", [
    (0, "0"), (5, "5"), (-2, "-2"), (0.5, "0.5"), (1234.5, "1234.5"), (1 / 3, "0.333333333"),
    (-1 / 3, "-0.33333333"), (2 / 3, "0.666666667"), (123456.123456, "123456.1235"),
    (12345678901, "12345678901"), (9.99999999999, "10"), (0.001, "0.001"), (-0.25, "-0.25")])
def test_fnum_general(x, text):
    h = u.harness()
    h.run(131, u.regs(APAY=x, ATAG=1, P0=BUF, LR=u.HALT_OK), max_steps=100)
    assert read_buf(h) == text


@pytest.mark.parametrize("c,text", [(0, "A"), (25, "Z"), (26, "AA"), (51, "AZ"), (52, "BA"), (701, "ZZ")])
def test_fcol(c, text):
    h = u.harness()
    h.run(132, u.regs(T1=c, P0=BUF, LR=u.HALT_OK), max_steps=10)
    assert read_buf(h) == text


@pytest.mark.parametrize("ofs,text", [(0, "Book1 - Excel"), (108, "TRUE"), (113, "FALSE"),
                                      (126, "#DIV/0!"), (166, "#GETTING_DATA"), (226, "#CALC!")])
def test_str_rom(ofs, text):
    h = u.harness()
    h.run(130, u.regs(T0=ofs, P0=BUF, LR=u.HALT_OK), max_steps=100)
    assert read_buf(h) == text


@pytest.mark.parametrize("s", ["", "a", "abc", "abcd", "hello world"])
def test_heap_copy(s):
    h = u.harness()
    H = 0x302100
    h.mem[H] = len(s)
    cs = [ord(c) for c in s] + [0, 0]
    for i in range(0, len(s), 3):
        h.mem[H + 2 + i // 3] = cs[i] + cs[i + 1] * 65536 + cs[i + 2] * 2**32
    h.mem[BUF:BUF + 20] = 9
    h.run(133, u.regs(T0=H, P0=BUF, LR=u.HALT_OK), max_steps=100)
    assert read_buf(h) == s


def test_glyph_measure_and_draw():
    h = u.harness()
    for i, ch in enumerate("Ab1"):
        h.mem[BUF + i] = ord(ch)
    out = h.run(129, u.regs(P0=BUF, T0=10, T5=-1, T8=1, T3=1 << 20, LR=u.HALT_OK), max_steps=50)
    assert out[29] == 10 + 8 + 7 + 7               # advances A 8, b 7, 1 7
    h.run(129, u.regs(P0=BUF, T0=10, T1=20, T2=1, T3=1279, T5=-1, LR=u.HALT_OK), max_steps=2000)
    fb = h.mem[u.FB:u.FB + u.W * u.H].astype(np.int64)
    assert px(fb, 14, 20) == 1                     # apex of A (col 4 of row 0)
    assert px(fb, 11, 28) == 1 and px(fb, 17, 28) == 1   # A legs on the baseline row
    assert px(fb, 10, 28) == 0                     # left bearing column stays blank
    assert ink(fb, 10, 40, 29, 31, 1) == []        # no descenders in "Ab1"


def test_fill_pattern_and_clip():
    h = u.harness()
    h.run(128, u.regs(N0=1270, N1=190, T0=1270, T1=1290, T2=200, T3=WH, T4=GRID, T5=1, T6=1,
                      T7=1279, T8=197, LR=u.HALT_OK), max_steps=1000)
    fb = h.mem[u.FB:u.FB + u.W * u.H].astype(np.int64)
    assert px(fb, 1270, 196) == WH and px(fb, 1270, 195) == GRID
    assert px(fb, 1270, 198) == 0                  # clipped below y 197
    assert px(fb, 0, 191) == 0                     # no wrap past x 1279 into the next row
