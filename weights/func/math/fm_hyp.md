# Weight block notes: fm_hy0 (282), fm_hy1 (283), fm_ah0 (284), fm_ah1 (285): hyperbolic and inverse hyperbolic functions

Hand-written. Not generated. Log: log/func-math-agent.md (2026-11-06). Factorial constants as in fm_trig.wt; the link packing (LR 2^16 + LP in word 25, unpacked by FLOOR with the 1.5 2^52 constant) as in fm_lg.

**fm_hy0 (282), fm_hy1 (283).** T0: 0 SINH, 1 COSH, 2 TANH, 3 SECH, 4 CSCH, 5 COTH. x = A, a = |x|.
- 282 PC 0: coercion (tags 0, 1, 3), first error, #VALUE!; a > 710.4758600739439 (where cosh overflows): SINH, COSH #NUM!, SECH, CSCH 0; CSCH(0), COTH(0) #DIV/0!. These return to (LR, LP).
- a < 1: Taylor S = sinh a (to a^19), C = cosh a (to a^20) by a two-lane Horner in z = a^2 (a is gated to 0 first when a >= 1 so z stays finite); goes to 283 with w20 = S, w14 = C, w21 = 1.
- a >= 1: xe = a, except TANH/COTH clamp to 25 when a > 25 (tanh 25 rounds to 1; the clamp is a two-way mux, a - u a is exactly 0, so 1e308 is safe) and the other four use a - 1 (exact) when a > 709 (hi = 1). EXP(xe) (268 T0 = 0) returns to 282 PC 1, which stores E in w20 and calls EXP(-xe), returning to 283.
- 283: P = E/2 (hi: E e/2), M = E2/2 (hi: 0), sh = P - M, ch = P + M (small route: sh = S, ch = C, by an exact mux), shs = (1 - 2 neg) sh. SINH and COSH return shs, ch to the unpacked link; TANH shs/ch, SECH 1/ch, CSCH 1/shs, COTH ch/shs go to fm_dv1 (267, gQ = 1) with LR, LP = the unpacked link.
- Saved words (passed through by fm_pw0/fm_pw1): w17 neg, w18 hi, w19 sel, w20, w21, w25 link, w28 xe.

**fm_ah0 (284), fm_ah1 (285).** T0: 0 ASINH, 1 ACOSH, 2 ATANH, 3 ACOTH.
- 284 PC 0: coercion, errors, domain #NUM! (ACOSH x < 1, ATANH |x| >= 1, ACOTH |x| <= 1). Routes: ASINH or ATANH with a < 0.125: series in 285 (PC 1, y = a). ASINH or ACOSH with a > 2^26: LN(a) + ln 2. ASINH: SQRT(a^2 + 1); ACOSH: SQRT((x - 1)(x + 1)) (a gated to at most 2^26 before squaring), back to 284 PC 1. ATANH: (1 + a)/(1 - a); ACOTH a > 8: 1/a (series flag); ACOTH: (a + 1)/(a - 1), through fm_dv1 back to 284 PC 2.
- 284 PC 1: ACOSH with sq < 0.125: series asinh(sq) (acosh x = asinh sqrt(x^2 - 1), avoids ln(1 + tiny)); else LN(a + sq). PC 2: series flag: atanh(1/a); else LN(q). LN calls (268 T0 = 1) return to 285 PC 0.
- 285: PC 0 r = h L + add (h = 1/2 for ATANH, ACOTH, else 1; add = ln 2 for the big route); PC 1 series: asinh y = y + y z PA(z) with PA coefficients (-1)^k C(2k, k)/(4^k (2k + 1)), k = 1..9 (-1/6, 3/40, -5/112, 35/1152, -63/2816, 231/13312, -143/10240, 6435/557056, -12155/1245184, typed as decimals), atanh y = y + y z PT(z) with 1/(2k + 1); |y| < 0.125, so the first omitted term is below 2^-56 relative. Result (1 - 2 neg) r to the unpacked link.
- Saved words: w17 neg, w18 sel, w19 a, w20 series flag, w21 h, w25 link, w28 add. The series flag is read as the product ph2 w20 (gate pair G23), not as a step literal, because in phase 0 w20 is the caller's word and can hold any value.

**Steps.** SINH, COSH 2 (|x| < 1) or 7; TANH, SECH, CSCH, COTH one more (fm_dv1). ASINH 2 (series), 4 (big) or 7; ACOSH 4 or 7; ATANH 2 or 6; ACOTH 4 (|x| > 8) or 6. **Parameters.** Not tallied yet.

**Limits.** A few ulps: EXP and LN each round, and the combination adds one or two roundings. For 709 < |x| <= 710.476 cosh = EXP(|x| - 1) e/2 (e/2 rounded). ASINH for 0.125 <= |x| < 0.5 goes through LN(|x| + sqrt(x^2 + 1)) and can be about 4 ulps off. ACOSH just above the 0.125 switch (x about 1.0078) likewise.

**Multi-role weights.** Word 14 carries the argument for EXP/LN/SQRT, the numerator for fm_dv1 or C (small sinh route), selected by route gates (exclusive). **Tests.** test_hyp (39 cases), test_ahyp (30 cases), test_abi (10 hyperbolic cases through fm_ent/fm_go), all pass.
