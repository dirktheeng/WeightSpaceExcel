# weights/prim/idivmod.wt: DIVMOD(x, d) with a variable integer divisor

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "idivmod". Decisions D15, P-D4.

**Computes.** x = A.PAY, integer, |x| < 2^49; d = B.PAY, integer, 1 <= d <= 2^49. T0 = floor(x / d), T1 = x - d floor(x / d) in [0, d). Basis of MOD, QUOTIENT and integer date arithmetic.

**v3 (dense 4x1).** State [d, 0, 1, 0]: two pairs (d and S = 2^-e), each value held in one word of its pair and 0 in the other, so a pair sum is exact.
**NORM down stages k = 32, 16, 8, 4, 2, 1 (5 layers each, v4..v33).** D1 rows: 2^k - xd (R3 sign exact), xd, 2^-k xd, S, 2^-k S (exact power-of-two scalings; pair sums have one zero term). step gives u = [xd < 2^k] (keep). D2 builds [u, 1 - u, u, 1 - u, xd, xs, S, Ss]; mul 0 4 4 8 gives the new pairs [u xd, (1 - u) xs, u S, (1 - u) Ss]. Greedy halving by 2^32 .. 2 leaves md = d 2^-e in [1, 2) for any d < 2^64, and S = 2^-e exactly.
**v34 (RECIP start).** y0 = 24/17 - (8/17) md (weights -0.47058823529411764, bias 1.411764705882353): the minimax line for 1/m on [1, 2], relative error at most 1/17. (encodings/primitives.md gives 48/17 - (32/17) m, which is the line for [0.5, 1]; decision P-D4.)
**Newton x4 (v37..v56).** t = md y (mul), u = 2 - t (R3), y = y u (mul). Relative error 1/17, 3.5e-3, 1.2e-5, 1.5e-10, then rounding level (a few ulps).
**v60..v64.** yd = y S (exact scaling), z = fl(x yd), q0 = round(z). |z - x/d| <= |x|/d * 6e-16 < 0.33 for |x| < 2^49, so q0 is f = floor(x/d) or f + 1.
**v66 (mul).** dq = d q0, an integer product below 2^50, exact. **v69, v70.** lo = [x - dq < 0], hi = [x - dq >= d] (R4 rows). **v73 (mul).** [lo d, hi d] (exact 0/1 gating). **v78.** q = q0 - lo + hi, r = x - dq + lo d - hi d.

**Limits.** d >= 1 (callers pass |d| and fix signs; d = 0 must be caught before, it gives garbage, finite). |x| < 2^49 keeps q0 within one of f. Cost: 6 + 2 step units, 753 parameters, 78 layers (the 8x10 D2 copy matrices dominate; nonzero weights are about 120).
**Multi-role weights.** None. **Tests.** test_idivmod (15 cases incl. 2^49 - 1 over 3, over itself and over 2^49, negatives, exact multiples): pass.
