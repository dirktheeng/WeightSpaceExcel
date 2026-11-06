# Weight block notes: ev_pow0 (114), ev_pow1 (117)

Hand-written. Not generated. Log: log/eval-agent.md. SAFE_MUL blocks retyped from weights/prim/safe_mul.wt (P-D3).

ev_pow0: |b| by relu pair, FLOOR(|b|), non-integer flag, cap |b| >= 2^31, a = b = 0; error -> #NUM!; else r = 1, x = a, n = |b|, nb = [b < 0]. 178 params. ev_pow1: one bit per step, h = FLOOR(n / 2), odd = n - 2h; r = r x if odd, x = x x, both by SAFE_MUL; overflow of r x, or of x x while bits remain, -> #NUM! (if |a| > 1 every later product overflows too); n = 0: B = (1, r), or for b < 0 route to ev_div with (1, r). 969 params. Steps: about 32 + 1 per exponent bit.

**Limits.** Non-integer exponents give #NUM! (correct for negative bases, wrong for positive ones such as 2^0.5; needs EXP and LN, stage 3). Repeated multiplication can differ from Excel's POWER by a few ulps for inexact results (inside the 1e-12 tolerance). **Multi-role weights.** None. **Tests.** ^ cases in test_eval.py.
