# Weight block notes: fm_rand (280), fm_rnd (281)

Hand-written. Not generated. Log: log/func-math-agent.md (2026-11-06).

**fm_rand (280).** PC 0: io 5 (the harness writes 64 fresh random bytes into the entropy region 0x301001; the network decides when, rule 5), PC 1. PC 1: block read of 6 words at 0x301001, K = 64, value 64 2^20 + 6 -> fm_rnd. Both phases from one dense row set over [ph]. **fm_rnd (281).** Block consumer (71 inputs). r = sum b_i 256^-(i+1): every partial sum is a multiple of 2^-48 below 1, so the row is exact in any order; 0 <= r <= 1 - 2^-48. RANDBETWEEN: lo = CEIL(A), hi = FLOOR(B) (FLOOR blocks, gated by |x| < 2^51), cnt = hi - lo + 1, value lo + FLOOR(r cnt) (r cnt < cnt for cnt < 2^48); cnt < 1 -> #NUM!; first error A then B.

**Limits.** 48-bit resolution (Excel's RAND resolution is not documented). Volatile recalculation is the evaluator's job (FUNC_TABLE flags bit 1). **Parameters.** Not tallied yet. Steps: 2. **Tests.** test_rand, test_randbetween (range, integrality, degenerate range, error order, more than one distinct value over 40 calls), pass.
