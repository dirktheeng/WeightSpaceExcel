# Weight block notes: ev_pow0 (114), ev_pow1 (117)

Hand-written. Not generated. Log: log/eval-agent.md. SAFE_MUL blocks retyped from weights/prim/safe_mul.wt (P-D3).

ev_pow0: |b| by relu pair, FLOOR(|b|), non-integer flag, cap |b| >= 2^31, a = b = 0; error -> #NUM!; else r = 1, x = a, n = |b|, nb = [b < 0]. 178 params. ev_pow1: one bit per step, h = FLOOR(n / 2), odd = n - 2h; r = r x if odd, x = x x, both by SAFE_MUL; overflow of r x, or of x x while bits remain, -> #NUM! (if |a| > 1 every later product overflows too); n = 0: B = (1, r), or for b < 0 route to ev_div with (1, r). 969 params. Steps: about 32 + 1 per exponent bit.

ev_pow0 (rewritten, session 2): big = non-integer b or |b| >= 2^31; big and a > 0 -> ev_pow2 (99) with T4 = a, T7 = b; big and a < 0 -> #NUM!; big and a = 0 -> square and multiply with n = 1 (0^0.5 = 0, 0^-0.5 = #DIV/0!); a = b = 0 -> #NUM!. 260 params.

ev_pow2 (99), one step, 302 values, 1772 params. Blocks (reusable primitives, documented here because weights/prim is not this agent's): NORM2 (11 two-sided exponent stages, factors 2^-c gd + 2^c gu + (1 - gd - gu) so no rounding of 2^-c - 1), fold to [sqrt(1/2), sqrt(2)], LN by 2 atanh(s) with s = (m - 1)/(m + 1) (reciprocal by chord start and 4 Newton steps, series to s^21), ln2 split hi/lo (fdlibm constants), guarded y = b L (ys = (b 2^-512) L; |y| above about 1341 means overflow or underflow), EXP by k = round(y/ln2), r = (y - k ln2_hi) - k ln2_lo, Taylor degree 14, exact overflow test (Q 2^k >= 2^1024 iff k >= 1025 or k = 1024 and Q >= 1), 11 exact scaling stages. Measured: 2^0.5 1 ulp below correct rounding; 1e308^0.5 relative error 7e-15.

**Limits.** Relative error grows like |b ln a| ulp (b ln a is formed in double), up to about 1e-13 near overflow; inside the 1e-12 tolerance, not bit-exact with Excel. Subnormal results are double rounded. Repeated multiplication (integer exponents) can differ from Excel's POWER by a few ulps. **Multi-role weights.** None. **Tests.** ^ cases in test_eval.py (SINGLE and POW).
