# Weight block note: lg_un (id 299)

Hand-written. Not generated. Log: log/func-logic-agent.md. ABI: encodings/functions.md sections 2, 4, 6.

**Computes.** ABI entry for one-argument Information functions and NA, TRUE, FALSE. Phases:

| PC | Condition | Action | Next |
|---|---|---|---|
| 0 | B is tag 9 and function is not ISREF | AS, AR1, AC1 = unpacked key, T1 = 0, LR = 299, LP = 1 | CELL_GET 16 |
| 0 | ISFORMULA, B not tag 9 | A = #VALUE! | FN_RET 257 |
| 0 | otherwise | A = B (tag 9 shown as 5), T0 = selector, LR = 257, LP = 0 | lg_info 296 |
| 1 | ISFORMULA, STATUS 0 | read word P0 + 3 (FORMULA), PC 2 | 299 |
| 1 | ISFORMULA, STATUS 1 (empty cell) | A = FALSE | 257 |
| 1 | otherwise | T0 = selector, LR = 257, LP = 0, A = cell value | 296 |
| 2 | | A = (3, [FORMULA word > 0]) | 257 |

**Blocks.** v2 to v4: selector from T2 = 64 + fid. 19 thresholds at the served values of T2 in increasing order; selector = sum of jump * [T2 >= value], the jumps (12, 6, -17, 5, -1, 9, 5, -15, 3, 1, -6, 13, -6, -6, 7, 6, -3, 4, -6) are the differences of consecutive selector values (219 ERROR.TYPE 12, 229 FALSE 18, 320 ISBLANK 1, 321 ISERR 6, 322 ISERROR 5, 323 ISEVEN 14, 324 ISFORMULA 19, 325 ISLOGICAL 4, 326 ISNA 7, 327 ISNONTEXT 8, 328 ISNUMBER 2, 329 ISODD 15, 331 ISREF 9, 332 ISTEXT 3, 383 N 10, 384 NA 16, 398 NOT 13, 545 TRUE 17, 549 TYPE 11). isref and f19 are differences of neighbouring thresholds. v20 to v39: key unpack (encodings/address.md section 3): q1 = FLOOR(K 2^-14), COL = K - 2^14 q1, SHEET = FLOOR(q1 2^-20), ROW = q1 - 2^20 SHEET; scalings are exact powers of two, FLOOR = r - [r > x] with r = ROUND(x). v46, v47: 12 gates times 12 values in one mul; v49 output rows, each a sum with at most one nonzero real term.

**Limits.** Argument count is not checked (a wrong count gives a result from the B register). Tag 5 ranges are passed to lg_info as they are (ISREF TRUE, TYPE 16, other IS functions FALSE, N 0); Excel would intersect or spill. ISFORMULA of a non-reference returns #VALUE! (unverified). ISOMITTED (fid 266, stage 10) is not served.

**Parameters.** 1158. **Steps.** Direct argument: 2 (lg_un, lg_info) + FN_RET. Reference: + CELL_GET. **Tests.** test_un.py (48 cases).
