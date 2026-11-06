"""Early preview (observation only): drives the ui_fill network (id 128) once per layout
rectangle of decision U1 and dumps a PNG. Superseded by the scene network (id 152)."""
import ui_util as u

G, RIB, BRD, WH, BOX, HDR, GRID = 0x217346, 0xF3F3F3, 0xD4D4D4, 0xFFFFFF, 0xC6C6C6, 0xEFEFEF, 0xE1E1E1
RECTS = [  # x0, y0, x1, y1, bg, line, fx, fy
    (0, 0, 1279, 54, G, 0, 0, 0), (46, 31, 99, 54, RIB, 0, 0, 0), (0, 55, 1279, 146, RIB, 0, 0, 0),
    (0, 147, 1279, 147, BRD, 0, 0, 0), (0, 148, 1279, 175, WH, 0, 0, 0),
    (3, 151, 104, 172, BOX, 0, 0, 0), (4, 152, 103, 171, WH, 0, 0, 0),
    (160, 151, 1276, 172, BOX, 0, 0, 0), (161, 152, 1275, 171, WH, 0, 0, 0),
    (0, 176, 1279, 195, HDR, BRD, 1, 1), (0, 196, 30, 755, HDR, BRD, 1, 1),
    (31, 196, 1279, 755, WH, GRID, 1, 1), (0, 756, 1279, 756, BRD, 0, 0, 0),
    (0, 757, 1279, 799, RIB, 0, 0, 0), (60, 757, 129, 777, WH, 0, 0, 0), (60, 776, 129, 777, G, 0, 0, 0)]

if __name__ == "__main__":
    h = u.harness()
    total = 0
    for x0, y0, x1, y1, bg, ln, fx, fy in RECTS:
        _, n = u.run_counted(h, 128, u.regs(N0=x0, N1=y0, T0=x0, T1=x1, T2=y1, T3=bg, T4=ln,
                                            T5=fx, T6=fy, T7=1279, T8=799, LR=u.HALT_OK))
        total += n
    print(total, u.dump_png(h, "preview_fill.png"))
