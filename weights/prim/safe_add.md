# weights/prim/safe_add.wt: SAFE_ADD(a, b)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 2", "constant check".

**Computes.** a = A.PAY, b = B.PAY, finite. T0 = fl(a + b) when that is finite, else 0; T1 = 1 when fl(a + b) would overflow. The operator network turns T1 into #NUM! (encodings/primitives.md SAFE rule).

**v4 (dense [0.5, 0.5]).** h = fl(a/2 + b/2): the halvings are exact for normal values, one rounding, never overflows. **Why the test is exact.** fl(a + b) overflows iff |a + b| >= 2^1024 - 2^970 (MAXD plus half an ulp, the tie rounds to the even 2^1024). Halving, |(a + b)/2| >= 2^1023 - 2^969, which is the midpoint between MAXD/2 and 2^1023, so it holds iff fl((a + b)/2) >= 2^1023. Subnormal halvings that round only matter when |h| is tiny.
**v5 (dense 2x1), T = 2^1023 = 8.98846567431158e307.** [T - h, T + h]; may be infinite but only the step reads it. **v6.** [h < T, h > -T]. **v8 (dense 5x4).** g, g, a, b, ov with ov = 2 - s1 - s2 and g = 1 - ov. **v9 (mul), v10 (R2 row).** fl(g a + g b): the plain IEEE add of a and b, or 0 + 0.

**Limits.** None within finite inputs. The literal T was verified exact by a debug forward pass. Cost: 2 step units, 35 parameters, 12 layers.
**Multi-role weights.** None. **Tests.** test_safe_add (11 cases incl. MAXD + 1e292 overflowing and MAXD + 9e291 not): pass.
