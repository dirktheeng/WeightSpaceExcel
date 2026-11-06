# weights/prim/mod2k.wt: MOD2K(x, 16)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 1".

**Computes.** x = A.PAY, an integer with |x| < 2^51. T0 = x mod 65536 in [0, 65536), T1 = floor(x / 65536). Used by HASH, UNPACK3 and key unpacking (encodings/address.md, memory-map.md).

**v2 (dense 2x1).** Weights 2^-16 = 0.0000152587890625 (exact power of two, R1), biases C and 0: [y + C, y], y = x 2^-16 exactly. **v3 (dense 2x2).** r = round(y) (bias -C), y. **v4, v5.** g = step(r - y) (R2 row, exact sign). **v8 (dense 2x4 over [r, y, g, x]).** mod = x - 65536 r + 65536 g; q = r - g. Integer terms below 2^52, exact (R4); y has weight 0.

**Limits.** Integers only (a fractional x gives a fractional remainder that is still x - 65536 floor(x / 65536)). Other powers 2^k: replace both 2^-16 weights by 2^-k and 65536 by 2^k. Cost: 1 step unit, 23 parameters, 8 layers.
**Multi-role weights.** None. **Tests.** test_mod2k (10 cases incl. negatives and 2^51 - 1): pass.
