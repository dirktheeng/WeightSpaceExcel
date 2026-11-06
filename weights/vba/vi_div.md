# Weight block note: vi_div (id 434)

Hand-written. Not generated. Log: log/vba-agent.md "vi_div". Opcodes: encodings/vba.md section 7.

**Computes.** `/` (19), `\` (20), `Mod` (21), `^` (22) for numeric operands a = words 13, 14 and b = words 15, 16 (VBA tags), routed from vi_bin (427). Two phases on PC (word 7).
- PC 0: op class from three thresholds on OP (word 47). ra, rb = ROUND half to even by the magic constant 3 2^51 (two dense layers; exact for |x| < 2^51). Errors: `/` with b = 0 gives 11, 0 / 0 gives 6 (VBA's overflow); `\` and Mod with ra or rb outside the Long range give 6, with rb = 0 give 11. Otherwise it calls a math-agent core by the ABI with link LR = 434, LP = 1: fm_dv1 (267) through its plain quotient gate gQ (word 38 = 1, words 30..37 = 0) with x = word 14 (a, or ra), m = word 16 (b, or rb); or fm_pw0 (268) with T0 = 3 (POWER), A = (1, a), B = (1, b). It saves aP, bP, ra, rb and typI (both operands of Integer rank: Empty, Boolean, Integer, Byte) in words 49..53, which both callees pass through.
- PC 1: A = (tag, value) from the callee. `/`: Double; an error tag (overflow) gives ERR 6. `^`: Double; 0 ^ 0 = 1 (VBA; Excel POWER says #NUM!); an error gives 5 when a <= 0 (domain) and 6 otherwise (overflow). `\` and Mod: r0 = ROUND(q), R0 = ra - rb r0 (exact, |rb r0| < 2^33), then the sign fix: if ra > 0 and R0 < 0, Q = r0 - sgn(rb), R = R0 + |rb|; if ra < 0 and R0 > 0, Q = r0 + sgn(rb), R = R0 - |rb|. So Q is truncated toward zero and R has the sign of ra (VBA). Result type Integer if typI else Long, range checked (ERR 6, for example -32768 \ -1 as Integer).
- The PC 1 arithmetic inputs are gated to 0 by the phase and class first, so garbage in the saved words can never overflow a product.
- Exit: block write [rT, rP] at SP - 4, SP -= 2, IP += 2, next vi_fetch (421); errors go to vi_halt (423) with a block read of 0 words (every step uses a block op, VB6).

**Reuse.** fm_dv1 and fm_pw0/fm_pw1 are the func-math agent's networks (weights/func/math/fm_div.md, fm_pow.md), called, not copied. This replaces the plan of retyping weights/prim/div.wt.
**Cost.** 3 steps for `/`, `\`, Mod (vi_div, fm_dv1, vi_div), 4 for `^`; plus fetch and dispatch. Parameters about 2,400 (mostly zeros of the 36-column output layer).
**Limits.** `^` inherits POWER's accuracy (fm_pow.md: relative error up to |b ln a| 2^-53). A negative base with an integer exponent that overflows reports 5, not 6. Byte \ Byte gives Integer (VBA gives Byte). Single operands give Double.
**Multi-role weights.** Words 49..53 hold the saved operands only between PC 0 and PC 1. **Tests.** test_div_family (20 cases), test_src_div_mod_pow.
