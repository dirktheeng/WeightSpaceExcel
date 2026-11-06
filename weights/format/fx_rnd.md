# Weight block note: fx_rnd (id 193), rounding to the shown digits

Hand-written. Not generated. Log: log/format-agent.md "numeric core"; decision F1.

**Computes.** From e, m (fx_dec), k = AC2, nint = N0, sci = N1: q = e + 1 + k (fixed) or max(nint, 1) + k (scientific) significant digits are kept, rounding half away from zero on the decimal digits of m (Excel rounds the 15-digit value: 1.005 with "0.00" shows 1.01). Out: AC1 = M, the digit stream left-aligned so the next digit is floor(M / 1e14); AR2 = R, integer digits in the stream (fixed: max(e + 1, 0), 0 for zero; scientific: max(nint, 1)); AS2 = X = e - max(nint, 1) + 1 (+ 1 on carry). next = T9. Params 527, 78 layers.

**Derivation.** D = 10^(15 - q) for q in 0..14 is selected by a one-hot built as [q >= i][q < i + 1] with one mul layer (no N x N matrix). y = m + D/2 is an exact integer; q0 = ROUND(y / D) (one multiply by fl(1/D), error below 0.25) is floor or floor + 1, corrected by the sign of the exact residual y - q0 D (q0 D < 2^53, integer product exact): Mr = D floor(y / D). q >= 15 keeps m; q < 0 gives 0. For values below 1 the stream starts at the 10^-1 digit: M = Mr 10^-(-e - 1), rounded (exact because Mr is a multiple when k <= 15). M = 1e15 is a carry: M = 1e14 and R + 1 (fixed) or X + 1 (scientific).

**Session 3: fx_eng (231) and engineering exponents.** fx_rnd's scientific input is now U1 = T0 (it was nint): q_sci = U1 + k, R_sci = U1, X = e - U1 + 1 + carry. fx_eng (one step, called as fx_dec's continuation by fx_sec and fx_gen, then next = 193) writes T0 = u + 1 with u = e - n floor(e / n), n = nint clamped to 1..6 (0 counts as 1); floor(e / n) = ROUND((e - (n - 1)/2) / n) by + C - C, exact for integer e. n = 1 gives u = 0 (plain scientific, General). fx_rnd clears T0 on exit (the emitter's CUR). Params 217 (fx_eng); fx_rnd 527. Carry in an engineering section bumps X by 1 only ("100.0E+1" for 999.96 with "##0.0E+0"). Tests: test_fx_rnd_sci (5), test_emit_sci (engineering cases).

**Limits.** Fixed formats with more than 15 - (-e - 1) decimals on values below 1 lose digits beyond 15 places; e <= -17 gives 0. Multi-role weights: none. Tests: test_fx_rnd_fixed (11), test_fx_rnd_sci (5).
