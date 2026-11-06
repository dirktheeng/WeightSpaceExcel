# weights/prim/onehot.wt: ONEHOT(x; 0, 1, 2, 3, 4)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 1".

**Computes.** T0..T4 = [x = 0], [x = 1], ..., [x = 4] for x = A.TAG. This is the TAG indicator bank of encodings/value.md (blank, number, text, boolean, error).

**v2 (dense 10x1).** Rows 2k and 2k + 1 have weight 1 and biases 0.5 - k and -0.5 - k (IS_K for k = 0..4 stacked in one layer). **v3 (step).** **v4 (dense 5x10).** Row k is +1 at column 2k and -1 at column 2k + 1. Exact as in is_k.md.

**Variant (not built).** For consecutive values the thermometer form uses n + 1 step units: GE_k = step(x - k + 0.5) for k = 0..5 and IS_k = GE_k - GE_(k+1). Retype that form when units matter more than one extra row.
**Limits.** Integer x; any value outside 0..4 gives all zeros. Cost: 10 step units, 75 parameters, 3 layers.
**Multi-role weights.** None. **Tests.** test_onehot (8 cases): pass.
