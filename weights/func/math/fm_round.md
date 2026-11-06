# Weight block note: fm_round (id 265)

Hand-written. Not generated. Log: log/func-math-agent.md (2026-11-06). FLOOR blocks retyped from weights/prim/floor_round.wt.

**Computes.** One step. T0 = 0 ROUND, 1 ROUNDUP, 2 ROUNDDOWN. x = A, digits d = B. Result in A, STATUS 0, next = LR, PC = LP. Clobbers words 0 to 7, 12 to 14 only.

**Blocks.**
- v5..v12: tag thermometers for A and B (k = 1..5); isnum = 1 - s2 + s3 - s4; x, d gated by mul (exact).
- v14..v16: d truncated toward zero by thresholds with trunc semantics: z_k = [d > k - 1] for k = -14..0, z_k = [k > d] for k = 1..15; t_k = z_k or 1 - z_k; one-hot over j = -15..15 is the bidiagonal difference (ind_-15 = 1 - t_-14, ind_15 = t_15), so d outside the range clamps to -15 or 15.
- v17 ROM (one nonzero term per row, exact): P = 10^j, Q = 10^-j (the doubles nearest), Thr = 2^51 10^-j.
- v24..v31: big = |x| > Thr (no digit at position d below 2^51; the result is x); ay = (1 - big)|x| P, one rounding.
- v32: nudge by 2^-50 relative (about 4 ulps): w = [ay(1 + 2^-50) + 1/2, ay(1 + 2^-50), -ay(1 - 2^-50)]. This stands in for Excel's 15-significant-digit decimal view of x: 2.675 * 100 = 267.49999999999997 rounds as 267.5, so ROUND(2.675, 2) = 2.68 as in Excel, and 0.1 * 3 = 0.30000000000000004 rounds up at 1 digit to 0.3, not 0.4.
- v33..v42: three FLOORs (r = (w + C) - C, g = [r > w]); ROUND = FLOOR(w1) (half away from zero on |x|), ROUNDDOWN = FLOOR(w2), ROUNDUP = CEIL = -FLOOR(w3); 3-way select by sel.
- v45..v50: sign restored by (1 - 2 sn), times Q (one rounding; for d > 0 Q is inexact, so the result is within an ulp of the decimal value, inside 15 digits), plus big x.
- v51..v58: first error in argument order: A error, A non-numeric (#VALUE!), B error, B non-numeric; else (1, val).

**Parameters.** 1884 (dense weights and biases, zeros included; tallied by hand from the layer headers). Steps: 1.

**Limits.** d is clamped to [-15, 15]: ROUND(x, -16) or below gives the multiple of 10^15 instead of 0 for |x| < 5e15 (Excel gives 0). The nudge can move a value whose decimal expansion is genuinely within 4 ulps below a rounding boundary (for example a typed 2.67499999999999 would still round down, since it is far more than 4 ulps away; only results of floating arithmetic land that close). Text arguments give #VALUE! (coercion is the ABI wrapper's job).

**Multi-role weights.** None. **Tests.** test_round (39 cases), all pass.
