# weights/prim/mux.wt: MUX (mul gating) and MUX_INT (relu big-M)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 1". Decision D14.

**Computes.** g = C.PAY in {0, 1}, a = A.PAY, b = B.PAY. T0 = MUX(g; a, b) = a if g = 1 else b, for any finite doubles. T1 = the same by MUX_INT, valid for integers with |a|, |b| < 2^22.

**MUX, v6 (dense 4x3).** [g, 1 - g, a, b]: R1 copy rows and one row -g + 1 (exact for g in {0, 1}). **v7 (mul 0 2 2 4).** [g a, (1 - g) b]: each product is exactly 0 or exactly the value. **v8 (dense [1, 1]).** One term is 0, so the add is exact. Requires V1: 0 times infinity would be NaN.
**MUX_INT, v9 (dense 4x3), M = 2^23 = 8388608.** Rows a + M g - M, -a + M g - M, b - M g, -b - M g. With g = 1 the first two are a and -a and the last two are below -M + 2^22 < 0; with g = 0 the roles swap. All integers below 2^24, exact (R4). **v10 relu, v11 dense [1, -1, 1, -1].** relu(v) - relu(-v) = v for the live pair, 0 for the dead pair.

**Limits.** MUX: g must be exactly 0 or 1. If a = -0 and g = 1 the result is +0 when b >= 0 (Excel has no -0). MUX_INT: integers only; a - M rounds for large reals and a + M can overflow, so never use it on doubles. Cost: MUX 19 parameters, 3 layers; MUX_INT 21 parameters, 4 relu units, 3 layers.
**Multi-role weights.** None. **Tests.** test_mux_int_and_mul (6 cases), test_mux_doubles (4 cases with MAXD and subnormals): pass.
