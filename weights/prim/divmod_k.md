# weights/prim/divmod_k.wt: DIVMOD_K(x, 10)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 1". Decision P-D6.

**Computes.** x = A.PAY, an integer with |x| < 2^51. T0 = floor(x / 10), T1 = x mod 10 in [0, 10).

**v2, v3.** q0 = round(fl(0.1 x)): one R1 row with the weight 0.1 (not exact), bias C, then bias -C. Error: fl(0.1) differs from 1/10 by under 2^-56 relatively and the product rounds once, so |fl(0.1 x) - x/10| < 2^51 / 10 * 1.7e-16 < 0.04. Hence q0 is f = floor(x / 10) or f + 1, never f - 1. Using ROUND instead of FLOOR here saves the FLOOR compare (decision P-D6). **v5 (dense 4x2 over [q0, x]).** q0, r0 = x - 10 q0, -r0, r0 - 9.5 (R4, exact). **v7 (step on the last two).** lo = [r0 < 0], hi = [r0 >= 10]. **v10 (dense 2x4).** q = q0 - lo + hi, r = r0 + 10 lo - 10 hi.

**Limits.** Integers, |x| < 2^51. For another constant d, use the weight fl(1/d) and the constants d and d - 0.5; the error argument needs |x| / d * 2^-52 < 0.5. Cost: 2 step units, 26 parameters, 10 layers.
**Multi-role weights.** None. **Tests.** test_divmod_k (12 cases incl. negatives, 10^15, 2^51 - 1): pass.
