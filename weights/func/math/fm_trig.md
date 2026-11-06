# Weight block note: fm_trig (id 270)

Hand-written. Not generated. Log: log/func-math-agent.md (2026-11-06). FLOOR by the 1.5 2^52 constant (weights/prim/floor_round.wt).

**Computes.** T0: 0 SIN, 1 COS, 2 TAN, 3 SEC, 4 CSC, 5 COT of x = A. One step; TAN, SEC, CSC and COT continue in fm_dv1 (267) through its plain quotient gate gQ (T9) and return from there to (LR, LP).

**Blocks.**
- v4..v18: coercion (tags 0, 1, 3), lim = |x| >= 2^27 (#NUM!, Excel's limit), xg = (1 - lim) x.
- v19..v28: k = ROUND(xg 2/pi); r = ((xg - k h1) - k h2) - k C2. Constants split by hand from fl(pi/2) = 0x3FF921FB54442D18: h1 = 0x1.921FB5p0 = 1.570796310901641845703125 (25 significant bits, decimal worked out as 1 + 1187765 * 5^24 / 10^24), h2 = 0x4442D18 2^-52 = 1.58932547122958567342720925807952880859375e-8 (24 significant bits), C2 = 6.123233995736766e-17 (pi/2 - fl(pi/2)). k has at most 27 bits, so k h1 and k h2 are exact; xg - k h1 is exact by Sterbenz; the other two subtractions round once each, relative to r.
- v29..v36: quadrant q = k - 4 FLOOR(k/4), thermometer u1..u3.
- v37..v65: z = r^2; two-lane Horner (sin: 1/17! .. -1/3!; cos: 1/16! .. -1/2!), sin r = r + (r z) Ps, cos r = 1 + z Pc. |r| <= 0.79: truncation below 7e-17 relative.
- v66..v69: quadrant rotation by an 8-pair exact mux.
- v70..v87: errors (#VALUE!, propagate, #NUM!, #DIV/0! for CSC and COT when sin x = 0, which for doubles below 2^27 means x = 0); numerator and denominator (TAN s/c, SEC 1/c, CSC 1/s, COT c/s); dv = divide route.
- v88..v108: next = LR + dv (267 - LR), word 14 = direct result or numerator, word 16 = denominator, words 30..38 = [0 x 8, 1].

**Limits.** Accuracy a few ulps (the division adds one rounding for TAN etc.). Reduction error grows with k only through C2's truncation (about k 1e-33). **Parameters.** Not tallied yet. Steps: 1 (SIN, COS) or 2. **Multi-role weights.** Word 14 carries the result (direct) or the numerator (divide route), selected by dv. **Tests.** test_trig (33 cases), all pass.
