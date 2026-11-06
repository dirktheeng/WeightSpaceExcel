# weights/func/lookup: Lookup and reference functions (ids 360 to 383)

Hand-written. Not generated. Log: log/func-lookup-agent.md; decision LK1 in log/WORKLOG.md. ABI: encodings/functions.md. Search core: core.md (ids 360 to 374). Tests: tests/output/func_lookup/test_core.py (115) and test_functions.py (131), helpers in lkbb.py.

## 1. Ids and flow

| Id | File | Role | Params |
|---|---|---|---|
| 360..374 | lk_start .. lk_wb | search core (core.md) | 8219 |
| 375 | lk_ent | FUNC_TABLE entry of every function below: block read of 10 words at SP - 2 (n - 1) | 21 |
| 376 | lk_args | block consumer: arguments a1..a6 into registers, missing ones as (8, 0) | 1212 |
| 377 | lk_dr | dereference loop (CELL_GET for scalar arguments given as cell references), dispatch | 5057 |
| 378 | lk_hr | ROW, COLUMN, ROWS, COLUMNS, AREAS, TRANSPOSE, INDEX, OFFSET, CHOOSE | 22978 |
| 379 | lk_hl | MATCH, VLOOKUP, HLOOKUP, LOOKUP, XMATCH, XLOOKUP: checks, mode, frame, core call | 12401 |
| 380 | lk_k | continuations: PC 0 core returned, PC 1 value read returned, PC 2 AREAS walk, PC 3 pair read | 444 |
| 381 | lk_hc | after the search: index, not-found value, or the result cell (CELL_GET) | 2702 |
| 382, 383 | | reserved for ADDRESS and INDIRECT (not built; lk_dr already routes those fids there) | |

    FUNC_TABLE[fid] = 375 -> lk_ent -> lk_args -> lk_dr (-> CELL_GET -> lk_dr)* ->
       reference functions: lk_hr -> FN_RET (257) | lk_k PC 2 (AREAS of a union) | lk_k PC 3 (CHOOSE argument 7+)
       lookup functions:    lk_hl -> FN_RET (errors) | lk_start ... lk_fin -> lk_k PC 0 -> lk_hc -> FN_RET | CELL_GET -> lk_k PC 1 -> FN_RET
                            (lk_hc -> lk_hc PC 1 when the return array is a range record)

Step counts (tests): ROW(C7) 5 steps; CHOOSE(2, ...) 5; AREAS of a 3-area union 12; VLOOKUP exact over 5 rows 36; XLOOKUP 44; MATCH approximate 24.

## 2. Registers after lk_args (all in the ABI's free set)

| Words | Content |
|---|---|
| 15, 16 (B) | a1 (lookup value, reference or CHOOSE index) |
| 17, 18 (C) | a2 |
| 32, 33 / 34, 35 / 36, 37 / 38, 39 | a3 / a4 / a5 / a6 (a6 holds the last argument when n >= 6) |
| 28 (N1) | n |
| 31 (T2) | 64 + fid (kept until the core is called) |

Preserve set (functions.md section 2): never written, except 56 (SCR, advanced by 8 when INDEX or OFFSET returns a new range record). The core saves and restores 22..27 and 40..47 itself.

## 3. Network notes

**lk_ent (375).** addr = SP - 2 n + 2, value = 64 2^20 + 10, next 376; everything else passes. Words past argument n - 1 are stale stack memory and are ignored by lk_args.

**lk_args (376).** Thermometer t_k = [n >= k], k = 1..6. a_i = t_(i+1) stored_i + (t_i - t_(i+1)) B + 8 (1 - t_i) on the tag, the same without the 8 on the pay; a6 = t6 B + 8 (1 - t6). Products by one mul layer (22 products; stored words may be any finite double), sums with one nonzero term each.

**lk_dr (377).** PC = k (1..6) after CELL_GET means "A replaces slot k" (slot MUX by mul, gates p_k from a PC thermometer). One-hot of the 17 fids (34 step units, codes 64 + fid). Per fid a mask of slots that are scalar arguments: ADDRESS 1..5; CHOOSE 1; HLOOKUP/VLOOKUP 1, 3, 4; INDEX 2, 3, 4; INDIRECT 1, 2; LOOKUP 1; MATCH 1, 3; OFFSET 2..5; XLOOKUP 1, 4, 5, 6; XMATCH 1, 3, 4; none for AREAS, COLUMN(S), ROW(S), TRANSPOSE. pend_i = mask_i and tag_i = 9; the lowest pending slot (f_i = pend_i and no lower pend) is read: K = PAY unpacked by two FLOORs (C = K - 2^14 q, S = FLOOR(q 2^-20), R = q - 2^20 S), CELL_GET with LR 377, LP = i. When none is pending: reference class -> block read of 6 words at a1's record (if tag 5, else address 0) to 378; lookup class -> the same for a2, to 379; ADDRESS -> 382, INDIRECT -> 383.

**lk_hl (379).** Table range: tag 5 record from the block, or the unpacked key of a tag 9 (both selected by mul). Indicator layers (named in the file): fid one-hot; tag classes of a1..a6 (text, error, missing, other); vector shape (w = 1 vertical, h = 1 horizontal, else 2-D), wide = w > h; numeric arguments compared with 0, 1, w + 1, h + 1; IS_K banks for match_mode {-1, 0, 1, 2} and search_mode {1, -1, 2, -2}; FLOOR of the column/row index. Mode M: MATCH 1 -> 7, 0 -> 1 + W, -1 -> 8 (by sign); VLOOKUP/HLOOKUP TRUE (or missing, or nonzero) -> 7, FALSE -> 1 + W; LOOKUP -> 7; XMATCH/XLOOKUP by the 16 (search, match) pairs: (1: 2 1 3 1), (-1: 5 4 6 4), (2: 7 11 9 11), (-2: 10 12 8 12) for match -1 0 1 2, W for match 2 with search +-1. Errors, in this order: lookup value error, table error, first error among the used numeric arguments, then #VALUE! (non-reference table, missing or text index, index < 1, bad mode, non-reference return array), #N/A (2-D vector), #REF! (index > width or height). Weighted vetoes (step(x - 4 y - 0.5)) give the precedence. On an error the network still block-writes, with N = 0 words, so that only 64 words are forwarded to FN_RET. Otherwise it writes the frame [kind, S, F2, F3, F4, nf.tag, nf.pay, 0] to 0x0BEF00 and calls the core (AS = S, AR1 = R1, AC1 = C1, N1 = n, T2 = dir, T3 = M, T7 = W, LR 380, LP 0); kind 0 index (MATCH, XMATCH), 1 cell of the table (F2/F3 = row/column base, F4 = 1 when the result runs down), 2 cell of the return array (F2/F3 = its tag and pay, F4 = direction, -1 = by its own shape for LOOKUP).

**lk_k (380).** p0..p3 from a PC thermometer. PC 0: block read of the frame -> 381. PC 1: next 257. PC 2: c = [A is a union node]: T3 += 1, P0 = PAY - 1, read [PAY] -> cs_ltag (18), cs_lpay (19) returns here with the left child; else A = (1, T3 + 1). PC 3: read [P0 + 1] -> 18 with LR 380, LP 1.

**lk_hc (381).** Gates gRetIdx, gNF, gC1, gC9, gR5, gBad as ANDs of PC, STATUS, kind and the return array tag. Result cell = base + MUX_INT(dR; idx) down and MUX_INT(1 - dR; idx) across, base and the not-found value selected by mul. A range record return array is read by a block read of 8 words into lk_hc itself (PC 1), with F4 kept in T4.

**lk_hr (378).** Features as in lk_hl (fid one-hot, a1 class: scalar, error, range, missing, cell, union, numeric). TRUNC of a1..a5 = FLOOR + [x < 0 and x not integer] (5 lanes in parallel). Comparison bank (33 rows) on the integer quantities h, w, T1..T5, n. Gates (32 + 24 + 5 + 4 + 20 rows) implement:
- ROW/COLUMN: no argument -> HR + 1 / HC + 1; reference -> R1 + 1 / C1 + 1; error -> itself; else #VALUE!.
- ROWS/COLUMNS: reference -> h / w; scalar -> 1; union -> #REF!; error -> itself.
- AREAS: cell or range -> 1; union -> walk (lk_k PC 2); else #VALUE!.
- TRANSPOSE: scalar, cell or 1 x 1 range -> the argument; larger range -> #VALUE! (needs arrays).
- INDEX(ref, r, [c], [area]): one row and c missing -> column r; one column and c missing -> row r; r or c 0 -> whole column or row (new range record); r < 0 or c < 0 -> #VALUE!; r > h or c > w -> #REF!; area other than 1 -> #REF!; result tag 9 for one cell.
- OFFSET(ref, r, c, [h], [w]): new top-left R1 + r, C1 + c; size h, w defaulting to the reference's; size < 1 or outside the sheet -> #REF!; tag 9 for 1 x 1, else a new range record.
- CHOOSE(i, ...): j = TRUNC(i); j < 1 or j > n - 1 -> #VALUE!; text or blank index -> #VALUE!; argument j + 1 from slots 2..5, slot 6 (when it is the last), or the operand stack through lk_k PC 3. The chosen argument is returned as it is (a reference stays a reference, an error is returned only if chosen).
Range outputs: oR1 = R1 + MUX_INT(gr; T2 - 1) + MUX_INT(ofOK; T2) and likewise for the other corners; K = S 2^34 + oR1 2^14 + oC1; a record [S, oR1, oC1, oR2, oC2, S, 0, 0] is block-written at SCR when the result is a range (N = 8, SCR += 8), N = 0 otherwise.

## 4. Known limits and deviations

- ADDRESS and INDIRECT are not built (ids reserved). FUNC_TABLE must not point their fids at 375 yet: lk_dr would route them to the TRAP network.
- TRANSPOSE needs arrays (stage 10 dynamic arrays): only single-cell and scalar arguments work.
- Arrays (tag 6) as table, vector or reference arguments are not supported (#VALUE!). MATCH(5, 5, 0) is #VALUE! here (Excel treats a scalar as a 1-element array).
- XLOOKUP returns the value of the result cell, not a reference (so XLOOKUP(...):B5 does not work), returns the first column (or row) of a 2-D return array, and does not check that the return array has the lookup array's size.
- INDEX supports one area only (area_num 1); INDEX of a scalar is #VALUE!. OFFSET with negative height or width is #REF! (Microsoft documents height and width as positive).
- Text-to-number coercion of numeric arguments ("2" as a column index) gives #VALUE! (ev_t2n is a stub).
- AREAS counts unions whose right children are leaves (left-nested unions, as the parser builds them).
- The core's limits (core.md section 6) apply: text order by code unit after ASCII folding, exact number equality, binary search skipping rule for interior blanks.

## 5. Multi-role words

- **B** is a1 on entry, the lookup value for the core (preserved by it), and is never returned.
- **T2** is 64 + fid until lk_hl, then the core's direction input; the core does not return it, so nothing after the core reads it (lk_hc uses the frame).
- **T3** is a3's TAG in lk_args/lk_dr/lk_hl, the core's mode, then the result index after the core, and the AREAS counter in lk_k PC 2 (lk_hr sets it to 0 for that path). Each reader runs only after the previous role is finished.
- **T4** is a3's PAY before the core and the stashed F4 in lk_hc PC 1.
- **PC** of lk_dr is the slot being filled (LP of its CELL_GET call); of lk_k and lk_hc the continuation phase.
- The 8 payload words of lk_hl and lk_hr are the result frame and the new range record; the block write length N (8 or 0) decides whether they are written.
Crosstalk: test_functions.py mixes these paths in one Sheet (MATCH with wildcards after XLOOKUP, CHOOSE beyond slot 6 after INDEX records).
