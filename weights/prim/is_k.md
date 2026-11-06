# weights/prim/is_k.wt: IS_K(x, 3)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 1".

**Computes.** T0 = 1 if x = 3 else 0, x = A.TAG (an integer, encodings/value.md V2). encodings/primitives.md IS_K with k = 3.

**v2 (dense 2x1).** Weights 1, 1; biases -2.5, -3.5: the rows are x - k + 0.5 and x - k - 0.5. For an integer x both are half-integers, never 0, so the following step is decided with a 0.5 margin.
**v3 (step).** [x > 2.5, x > 3.5]. **v4 (dense 1x2).** [1, -1]: the first minus the second is 1 only for x = 3. Every value is a small integer or half-integer, exact under R4.

**Limits.** For non-integer x the block reports 1 for x in (2.5, 3.5]. Any finite x is safe. Cost: 2 step units, 7 parameters, 3 layers.
**Multi-role weights.** None.
**Tests.** test_is_k (6 cases): pass.
