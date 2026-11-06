# Weight block notes: fill (128), fill_rd (170), fillP (171), fillL (172), fillLz (173), gband (174)

Hand-written. Not generated. Log: log/ui-agent.md 2026-11-06 (block ops); decisions U1, U6 in log/WORKLOG.md. Harness v2 block operations (harness/FORMAT.md).

**Computes.** Rectangle fill, one block write per scanline. Args as before: N1 y (= y0), T0 x0, T1 x1, T2 y1, T3 bg, T4 line, T5 fx, T6 fy, T7 clipR, T8 clipB; returns to (LR, LP).
- fx = 0 (128 loops on itself): row colour a = line if fy and (y - 196) mod 20 = 19, else bg. The row vector is a broadcast built by concat doubling (no weights).
- fx = 1: 128 writes a 2560-word pattern ROM at 0x0F8000 in absolute x phase (period 64: c30 at x mod 64 = 30, i.e. (x - 31) mod 64 = 63), fill_rd block-reads ROM + x0 (1280 words, K = 64), and the row networks keep that row in their forwarded state (K = 1344): fillP writes it, fillL writes a line-colour row, fillLz writes the last row when it is a line row and returns (K = 64). Pattern versus line is chosen by routing (which network runs next) because an elementwise select of two 1280-vectors would need a 1280 x 2560 dense.
- gband (174): one cell row of the combined row header + grid band per step (20 full scanlines, 25,600 contiguous words); N1 = first cell row, T2 = last.

**Derivation.** floor((y - 196)/20) = ROUND(0.05 y - 10.275) (fractions multiples of 0.05, no ties). Width w = relu(min(x1, clipR) - x0 + 1), min by x1 - relu(x1 - clipR). N = w when y <= clipB else 0, and the address is gated to 0 (128) or clamped to y 799 (171..173) on clipped rows so an off-screen rectangle never addresses outside memory. Selects are MUX_INT (relu with big M). Identity layers (or a 64-row broadcast dense) materialise the 64-word period so the harness copies pieces, not 2560 scalars.

**Limits.** y0 <= y1. Clipped rows still cost a step each. The pattern ROM is shared scratch (rewritten per pattern fill).
**Parameters.** fill about 420, fill_rd 190, fillP 560, fillL 520, fillLz 400, gband 60 (hand counts of dense shapes). **Steps.** Solid: rows. Pattern: rows + 2. gband: cell rows (28 for the grid).
**Multi-role weights.** None. **Tests.** tests/output/ui/test_ui.py test_fill_pattern_and_clip, test_fill_solid_grid_line_row, test_gband_equals_pattern_fills, test_grid_geometry, test_headers.
