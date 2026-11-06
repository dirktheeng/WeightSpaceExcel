# weights/prim/safe_mul.wt: SAFE_MUL(a, b)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 2". Decision P-D3.

**Computes.** a = A.PAY, b = B.PAY, finite. T0 = fl(a b) when finite, else 0; T1 = overflow flag.

**v4 (dense 2x2), S = 2^-512 = 7.458340731200207e-155 (verified exact).** [a S, b S], exact unless they underflow, which needs |a| or |b| < 2^-510, and then |a b| < 2^514 cannot overflow. **v5 (mul).** s = fl(a b 2^-1024), always finite. **Why the test is exact.** fl(a b) overflows iff |a b| >= 2^1024 (1 - 2^-54) (MAXD plus half an ulp). Scaled, iff X = |a b| 2^-1024 >= 1 - 2^-54, and fl(X) >= 1 exactly then (the midpoint 1 - 2^-54 rounds to the even 1). So ov = [|s| >= 1].
**v6, v7.** [1 - s, 1 + s], step: [s < 1, s > -1]. **v9 (dense 5x4).** g, g, a, b, ov = 2 - t1 - t2. **v10, v11 (mul, mul).** fl((g a)(g b)): the IEEE product or 0.

**Deviation.** encodings/primitives.md scales by 2^-600 with threshold 2^-176; 2^-512 with threshold 1 is equivalent and uses a literal already verified (P-D3).
**Limits.** Underflow to 0 or subnormals is the IEEE result, as in Excel. Cost: 2 step units, 35 parameters, 13 layers.
**Multi-role weights.** None. **Tests.** test_safe_mul (11 cases incl. MAXD (1 + 2^-52) overflowing and 2^512 2^511 = 2^1023 not): pass.
