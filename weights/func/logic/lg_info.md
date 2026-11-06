# Weight block note: lg_info (id 296)

Hand-written. Not generated. Log: log/func-logic-agent.md. Blocks: GE_K thermometers, ROUND by C = 1.5 * 2^52, MUX by mul (encodings/primitives.md).

**Computes.** One step, one forward pass (57 values). Selector T0 (word 29): 1 ISBLANK, 2 ISNUMBER, 3 ISTEXT, 4 ISLOGICAL, 5 ISERROR, 6 ISERR, 7 ISNA, 8 ISNONTEXT, 9 ISREF, 10 N, 11 TYPE, 12 ERROR.TYPE, 13 NOT, 14 ISEVEN, 15 ISODD, 16 NA, 17 TRUE, 18 FALSE. Argument A (words 13, 14) as a value (encodings/value.md; a dereferenced value, or tag 5 for a reference). Result in A; STATUS = 0; next = LR, PC = LP. Words 8 to 11 and 15 to 63 pass. Clobbers words 0 to 7, STATUS, A.

**Blocks.**
- v4, v5: one dense of thresholds then step: tag >= k (k 0..9), selector >= k (k 1..19), pay > 6.5, pay > 7.5, pay > 0, -pay > 0. Integer rows are exact (R4); pay rows have one unit weight and a bias (R3).
- v7: tag one-hot I0..I8 = G_k - G_k+1, I9 = tag >= 9. v9: selector one-hot S1..S18. v11: e7 = [pay = 7], z = [pay = 0] = 1 - [pay > 0] - [-pay > 0].
- v12 to v28, parity: ax = relu(pay) + relu(-pay) (one nonzero term, exact); B = [ax > 2^50]; q = ax (1 - B) / 2 by one mul (exact: power-of-two scale times a 0/1 gate); r = ROUND(q); u = r - q (exact, Sterbenz); s1 = [u > 0], t = [u + 0.5 > 0]; odd = s1 or not t. Derivation: q - FLOOR(q) is in [0.5, 1) exactly when trunc(ax) is odd; with round half to even, u > 0 covers fractional parts above 0.5 and odd halves, and u = -0.5 covers even k + 0.5 (q = 2.5 for ax = 5).
- v32, v33: conjunctions by step of sums: ISERR = I4 and not e7, ISNA = I4 and e7, Nz = (I1 + I3) and z (NOT of a number or boolean is TRUE when the payload is 0, since FALSE has payload 0), OK1 = number and not big, NB = number and big, EVENok, ODDok.
- v35, v36: gated payloads Npay = (I1 + I3 + I4) pay (N keeps numbers, booleans as 0/1, error codes), Epay = I4 pay, one mul each, exact.
- v39 D: 5 variable tags (N, ERROR.TYPE, NOT, ISEVEN, ISODD) and 15 payloads. Integer rows (R4) except Npay, which has a single unit weight (R1). TYPE = I0 + I1 + 2 I2 + 4 I3 + 16 I4 + 16 I5 + 64 I6 + 128 I7 + I8. NOT payload = I0 + I8 + Nz + Epay + 3 (I2 + I5 + I6 + I7 + I9) with tag 3 + I2 + I4 + I5 + I6 + I7 + I9. ISEVEN payload = I0 + I8 + EVENok + Epay + 3 (non-number tags) + 6 NB with tag 4 - I0 - I8 - OK1; ISODD the same with ODDok and no I0, I8.
- v44 to v48: gates [S10, S12..S15, S1..S15] times D (one mul), then one 2 x 38 row pair adding constant tags (3 for IS functions, TRUE, FALSE; 1 for TYPE; 4 for NA) and constant payloads (NA 7, TRUE 1) straight from S. Exactly one selector is 1, so each sum has one nonzero term.

**Excel behaviour covered.** IS functions never propagate errors. N: number itself, TRUE 1, FALSE 0, text and blank 0, error propagates. TYPE: 1 number or blank, 2 text, 4 boolean, 16 error, 64 array, 128 lambda (tag 7); tag 5 gives 16 (unverified against Excel for multi-cell references). ERROR.TYPE: code for errors, #N/A otherwise. NOT: numbers by = 0, blank TRUE, text #VALUE!, errors propagate. ISEVEN / ISODD truncate toward zero; blank is even; booleans and text #VALUE!; errors propagate.

**Limits.** ISEVEN / ISODD of |x| > 2^50 return #NUM! (Excel's limit unverified). Numeric text ("4") is not coerced for ISEVEN / ISODD / NOT (Excel coerces; needs ev_t2n). Text "TRUE" / "FALSE" is not coerced by NOT. Array arguments are not lifted elementwise. A selector outside 1..18 gives (0, 0).

**Parameters.** 1302. **Tests.** tests/output/func_logic/test_info.py (85 cases); used through lg_un in test_un.py.
