# Weight block notes: fm_dv0 (id 266), fm_dv1 (id 267)

Hand-written except the DIV block in fm_dv1, which is copied unchanged from weights/prim/div.wt (prim agent, hand-written; note weights/prim/div.md), the same reuse as weights/eval/ev_div.wt. Not generated. Log: log/func-math-agent.md (2026-11-06).

**Family.** T0: 0 QUOTIENT, 1 MOD, 2 MROUND, 3 CEILING, 4 FLOOR, 5 CEILING.PRECISE and ISO.CEILING, 6 FLOOR.PRECISE, 7 CEILING.MATH, 8 FLOOR.MATH. x = A, m = B (divisor or significance; tag 8 missing gives 1 for selectors 5 to 8), mode = C (selectors 7, 8). Two steps: 266 then 267, which returns to (LR, LP) with A = result, STATUS 0.

**fm_dv0 (266), one step, 48 values.**
- v5..v14: tag thermometers for A, B, C at k = 1, 2, 3, 4, 5, 8, 9; isnum = 1 - s2 + s3 - s4 + s8 - s9 (tags 0, 1, 3, 8), iserr = s4 - s5, isval = s2 - s3 + s5 - s8 + s9; values gated by mul.
- v15..v17: signs and magnitudes of x, m, mode.
- v21..v28: three levels of AND gates (step of sums of 0/1 words, R4 exact): first error in order f1 A error, f2 A #VALUE!, f3 B error, f4 B #VALUE! (only when A is fine), f5, f6 for C (only selectors 7, 8 and A, B fine); okABC; sign errors f7 (MROUND with opposite signs; CEILING or FLOOR with x > 0 and m < 0: Excel's #NUM!); f8 #DIV/0! for QUOTIENT, MOD, FLOOR with m = 0; Z (result 0) for MROUND, CEILING and the PRECISE/MATH forms with m = 0.
- v30..v33: m' = m, or for selectors >= 5 |m| (or 1 when missing) as m + t5 (missB + 2 relu(-m)) (two terms, exact). Gates gT = QUOTIENT, gM = MOD, gR = MROUND, gC = CEILING forms plus FLOOR.MATH with mode and x < 0, gF = FLOOR forms plus CEILING.MATH with mode and x < 0. PEpay = first error's code.
- Writes A.PAY = x, B.PAY = m', T1..T8; next = 267.

**fm_dv1 (267), one step, 393 values.** Since the trig extension it also has gate gQ (T9, word 38): plain quotient q = x / m' (used by fm_trig, fm_at0, fm_lg, fm_comb, fm_gcd); fm_dv0 writes gQ = 0. With gQ and m' = 0 the result is 0, so callers exclude zero divisors themselves. v1..v338 DIV: q = fl(x / m'), ov, dz. Tail:
- big = |q| > 2^51 (q already an integer); five gated FLOORs of [q, -q, q + e|q|, -q + e|q|, (1 + e)|q| + 1/2], e = 2^-50 (nudge as in fm_round: CEILING(0.234, 0.01) = 0.24 needs FLOOR/CEIL of 23.400000000000002 to see 23.4).
- QUOTIENT = TRUNC(q) (no nudge); MOD = x - m' FLOOR(q) (one product, one subtraction, as Excel's n - d INT(n/d)); MROUND = m' sgn(q) FLOOR(|q| + 1/2); CEIL = m' CEIL(q - e|q|); FLOOR = m' FLOOR(q + e|q|).
- #NUM! when the quotient overflows or for MOD with |q| > 2^51 (Excel's MOD gives #NUM! for huge quotients); errors from fm_dv0 take priority, then Z.

**Parameters.** fm_dv1's DIV block 10470 (div.md); the fm_dv0 total and the fm_dv1 tail are not tallied yet. Steps: 2.

**Limits.** FLOOR(0, 0) gives #DIV/0! (Excel gives 0). Excel's exact MOD #NUM! threshold is not pinned (2^51 used). The nudge as in fm_round. CEILING and FLOOR with m' very small relative to x can overflow q and give #NUM! where Excel might return x.

**Multi-role weights.** None. **Tests.** test_divfam (66 cases), all pass.
