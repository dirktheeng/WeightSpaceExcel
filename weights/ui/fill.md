# Weight block notes: weights/ui/fill.wt (id 128, rectangle fill)

Hand-written. Not generated. Log: log/ui-agent.md 2026-11-06; decisions U1 (layout), U2 (network split), U3 (registers) in log/WORKLOG.md.

**Computes.** One pixel per step. Pixel (x, y) = (N0, N1) is written with colour `L ? line : bg`, where L = (fx AND gx) OR (fy AND gy), gx = [(x - 31) mod 64 = 63], gy = [(y - 196) mod 20 = 19] (grid origin and 64 x 20 cell pitch, U1). The write happens only if x <= clipR and y <= clipB. Then x advances, wrapping to x0 and y + 1 after x1. After pixel (x1, y1) it returns to (LR, LP).

**Encodings.** Args N0 x, N1 y, T0 x0, T1 x1, T2 y1, T3 bg, T4 line, T5 fx, T6 fy, T7 clipR, T8 clipB (encodings/control.md register map). Address 0x100000 + 1280 y + x, pixel word 0xRRGGBB (encodings/glyph.md D17).

**Derivation.** qx = floor((x - 31)/64) = ROUND(x/64 - 31/64 - 63/128) (fractions are multiples of 1/64, so subtracting 63/128 never lands on a tie). qy = floor((y - 196)/20) = ROUND(0.05 y - 10.275) (fractions are multiples of 0.05, margin 0.025 far above rounding error). mx = x - 31 - 64 qx, so gx = step(x - 64 qx - 93.5); likewise gy = step(y - 20 qy - 214.5). ex = [x >= x1], ey = [y >= y1], done = ex AND ey. Selects are MUX_INT with M = 2^25 (colours < 2^24, ids and coordinates small).

**Limits.** x0 <= x1 and y0 <= y1 are required, otherwise the loop never ends. Pixels clipped away still cost a step. The address field is a pixel address on skipped steps too (rule A2 is not followed; this is harmless because mem_op is 0).
**Parameters.** 514 (hand count of the dense shapes). **Steps.** (x1 - x0 + 1)(y1 - y0 + 1).
**Multi-role weights.** None. **Tests.** tests/output/ui/test_ui.py test_fill_pattern_and_clip, test_grid_geometry, test_headers.
