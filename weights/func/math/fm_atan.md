# Weight block notes: fm_at0 (id 271), fm_at1 (id 272)

Hand-written. Not generated. Log: log/func-math-agent.md (2026-11-06).

**Family.** T0: 0 ATAN(x), 1 ATAN2(x_num = A, y_num = B), 2 ACOT, 3 ASIN, 4 ACOS. angle = atan2(Y, X) with (Y, X) = (x, 1), (B, A), (1, x), (x, sqrt(1 - x^2)), (sqrt(1 - x^2), x).

**fm_at0 (271), two phases.** PC 0: coercion, first error (A, then B for ATAN2), ASIN/ACOS with |x| > 1 -> #NUM!, ATAN2(0, 0) -> #DIV/0!. ASIN/ACOS: w = (1 - x)(1 + x), call SQRT (268 with T0 = 4) returning to 271 PC 1, with x in word 28, selector in word 19, link LR 2^16 + LP in word 25 (the SQRT chain passes these words through). PC 1 or the other selectors: s = min(|Y|, |X|), b = max (exact muxes), off = [s > tan(pi/8) b]; num = s - off b, den = b + off s; route to fm_dv1 (gQ = 1) returning to fm_at1 (272), with sw = [|Y| > |X|] (17), off (18), Xneg (20), Yneg (21), link (25).
**fm_at1 (272).** t = num / den in [-tan(pi/8), 1]; atan t = t + t z P(z), P with the 20 coefficients (-1)^k / (2k + 1), k = 1..20 (truncation below 0.4143^43 / 43); a0 = atan t + off pi/4; a1 = pi/2 - a0 if sw; a2 = pi - a1 if X < 0; a3 = -a2 if Y < 0 (each an exact two-way mux after one subtraction). Link unpacked by FLOOR of LINK 2^-16. Returns (1, a3).

**Limits.** A few ulps. ATAN2(-0, x < 0) gives pi (Excel has no negative zero inputs). **Parameters.** Not tallied yet. Steps: 3 (ATAN, ATAN2, ACOT), 5 (ASIN, ACOS). **Multi-role weights.** Word 14 is the error, w or the numerator, by route (exclusive). **Tests.** test_atan (35 cases), all pass.
