# weights/prim/compare.wt: GT, EQ, LT, SIGN on doubles

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 1".

**Computes.** a = A.PAY, b = B.PAY, any finite doubles. T0 = [a < b], T1 = [a = b], T2 = [a > b], T3 = SIGN(a) in {-1, 0, 1}. encodings/primitives.md "Real comparisons".

**v4 (dense 4x2).** Rows [1, -1], [-1, 1], [1, 0], [-1, 0], biases 0. The first two are R2 rows: one IEEE subtraction each, and for finite doubles fl(a - b) > 0 exactly when a > b (gradual underflow means fl(a - b) = 0 only if a = b). The last two are R1 rows (a and -a, exact).
**v5 (step).** [a > b, b > a, a > 0, a < 0]. If a - b overflows to an infinity, only this step layer reads it, so V1 holds for every dense or mul input.
**v6 (dense 4x4).** LT = s2; EQ = 1 - s1 - s2 (bias 1); GT = s1; SIGN = s3 - s4. Small integers, exact.

**Limits.** -0 and +0 compare equal and SIGN(-0) = 0, as in Excel. NaN and infinities never occur as inputs (V1). Cost: 4 step units, 32 parameters, 3 layers. The block for one predicate alone (GT) is 1 R2 row plus 1 step unit.
**Multi-role weights.** None. **Tests.** test_compare (12 cases, including +-MAXD, subnormals and one-ulp gaps): pass.
