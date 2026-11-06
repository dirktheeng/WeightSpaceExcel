# Weight block notes: weights/poc/round_floor.wt

Hand-written. Not generated. Proof of concept only; not part of the application. Produced by log/WORKLOG.md entry "2026-11-06 Stage 1: shared encodings design", decision D5 (ROUND by magic constant).

**What it computes.** Input x = input[1] (input length 8, smoke-test layout). Output length 8: `[0, 2, 0, floor(x), 0, 0, 1, round(x)]`, that is, write floor(x) to address 0, halt, and leave round(x) (round half to even) in word 7. Encodings: encodings/primitives.md, blocks ROUND and FLOOR.

**Layer 1 (dense 1x8).** Weight 1 on input column 1, bias C = 6755399441055744 = 1.5 * 2^52. The double sum x + C lies in [2^52, 2^53) for |x| < 2^51, where the spacing of doubles is exactly 1, so IEEE round to nearest even rounds the fractional part of x away. Result y = C + round(x).

**Layer 2 (dense 1x1).** Weight 1, bias -C. y and C are both in [2^52, 2^53), so y - C is exact (Sterbenz lemma). Result r = round(x), ties to even.

**Layers 3, 4.** slice and concat with no weights; they gather [r, x] for the next dense.

**Layer 5 (dense 1x2).** Weights [1, -1], bias 0. Two terms with unit weights, so the dense row is a single IEEE subtraction r - x; its sign is exact for finite doubles.

**Layer 6 (step).** g = 1 exactly when r > x, which is exactly when rounding went up past x.

**Layer 8 (dense 8x3).** Row 3: floor(x) = r - g (integers, exact). Row 7 copies r. Row 1 bias 2 (write), row 6 bias 1 (halt). All other rows zero.

**Forward passes (ad hoc, not committed).** x = 2.5: floor 2, round 2. 3.5: 3, 4. -2.5: -3, -2. 7: 7, 7. -0.0001: -1, 0. 1e15 + 0.25: 1e15, 1e15. -3: -3, -3. 0.49999999999999994 (largest double below 0.5): 0, 0. 2^51 - 0.5: 2^51 - 1, 2^51 (tie to even). All as derived.

**Limits.** Valid for |x| < 2^51. Larger |x| are already integers but x + C then leaves the [2^52, 2^53) band; callers must range check (encodings/primitives.md). NaN or inf input is never allowed (encodings/value.md invariant V1).

**Multi-role weights.** None.
