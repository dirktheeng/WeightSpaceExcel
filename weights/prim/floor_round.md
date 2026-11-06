# weights/prim/floor_round.wt: FLOOR, CEIL, ROUND (half even), TRUNC, ROUND half away

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 1". Decision D5 (ROUND by magic constant), P-D7.

**Computes.** x = A.PAY, |x| < 2^51. T0 FLOOR(x), T1 CEIL(x), T2 ROUND(x) ties to even (the internal ROUND primitive), T3 TRUNC(x), T4 ROUND half away from zero (what Excel's ROUND(x, 0) does).

**v2 (dense 2x1).** x + C and -x + C with C = 1.5 * 2^52 = 6755399441055744: R3 rows. The sum lies in [2^52, 2^53), where doubles are spaced 1, so IEEE rounding drops the fraction, ties to even. **v3 (dense 2x2, biases -C).** r1 = round(x), r2 = round(-x), exact by Sterbenz.
**v5 (dense 6x3 over [r1, r2, x]).** e = r1 - x and r2 + x (R2 rows, exact because |e| <= 0.5 and r1, x share a binade or r1 = 0), x, -x, e + 0.5 and 0.5 - e (one subtraction then one bias add; signs exact). **v6 (step).** g1 = r1 > x (rounding went up), g2 = r2 > -x, s = x > 0, sn = x < 0, u1 = e > -0.5, u2 = e < 0.5.
**v8 (dense 7x9).** s, 1 - s, FLOOR = r1 - g1, CEIL = g2 - r2 (= -FLOOR(-x)), ROUND = r1, up argument s - u1 - 0.5 (AND of s and NOT u1), down argument sn - u2 - 0.5. Integers, exact. **v9 (mul).** [s FLOOR, (1 - s) CEIL]: TRUNC selects FLOOR for x > 0 and CEIL otherwise (both are 0 at x = 0). **v11 (step).** up = [x > 0 and x - r1 = 0.5], down = [x < 0 and x - r1 = -0.5]: exactly the ties that round-half-even sent toward zero. **v15 (dense 5x7).** Copies plus TRUNC = m1 + m2 (one term 0) and ROUND_HALF_AWAY = r1 + up - down.

**Limits.** |x| < 2^51 (x + C must stay in [2^52, 2^53)); larger doubles are integers already and need a range check by the caller. Results -0 can appear for CEIL of small negatives; they compare equal to 0. Cost: 6 step units in one layer plus 2 in another, 144 parameters, 15 layers (FLOOR alone: 5 layers as in the poc).
**Multi-role weights.** None. **Tests.** test_floor_round (18 cases incl. ties, 0.49999999999999994, 2^51 - 0.5): pass.
