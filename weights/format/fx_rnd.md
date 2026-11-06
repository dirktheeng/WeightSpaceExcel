# Weight block note: fx_rnd (id 193), rounding to the shown digits

Hand-written. Not generated. Log: log/format-agent.md "numeric core"; decision F1.

**Computes.** From e, m (fx_dec), k = AC2, nint = N0, sci = N1: q = e + 1 + k (fixed) or max(nint, 1) + k (scientific) significant digits are kept, rounding half away from zero on the decimal digits of m (Excel rounds the 15-digit value: 1.005 with "0.00" shows 1.01). Out: AC1 = M, the digit stream left-aligned so the next digit is floor(M / 1e14); AR2 = R, integer digits in the stream (fixed: max(e + 1, 0), 0 for zero; scientific: max(nint, 1)); AS2 = X = e - max(nint, 1) + 1 (+ 1 on carry). next = T9. Params 525, 74 layers.

**Derivation.** D = 10^(15 - q) for q in 0..14 is selected by a one-hot built as [q >= i][q < i + 1] with one mul layer (no N x N matrix). y = m + D/2 is an exact integer; q0 = ROUND(y / D) (one multiply by fl(1/D), error below 0.25) is floor or floor + 1, corrected by the sign of the exact residual y - q0 D (q0 D < 2^53, integer product exact): Mr = D floor(y / D). q >= 15 keeps m; q < 0 gives 0. For values below 1 the stream starts at the 10^-1 digit: M = Mr 10^-(-e - 1), rounded (exact because Mr is a multiple when k <= 15). M = 1e15 is a carry: M = 1e14 and R + 1 (fixed) or X + 1 (scientific).

**Limits.** Fixed formats with more than 15 - (-e - 1) decimals on values below 1 lose digits beyond 15 places; e <= -17 gives 0. Multi-role weights: none. Tests: test_fx_rnd_fixed (11), test_fx_rnd_sci (5).
