# Weight block notes: evaluator networks (ids 95..102, 104..109, 116)

Hand-written. Not generated. Log: log/eval-agent.md; decisions E5, E6, E8..E12 in log/WORKLOG.md. Token format: encodings/memory-map.md sections 6 and 13. Values: encodings/value.md.

**Fetch protocol.** A step that issues read [TP] routes to ev_disp PC 0, which receives OPC and either reads OPND (TP + 1) for the handler or reads the left operand TAG (SP - 2) for binary operators. Operators that finish without a memory write issue the next OPC read themselves (TP += 2).

| Id | File | Computes | Params |
|---|---|---|---|
| 95 | ev_start | PC 0 HR, HC from KEY (FLOOR of (x0 - 1) 2^-14); PC 1 P1 = record; PC 2 TP, SP = 0x1000, SCR = 0xB0000, read first OPC | 393 |
| 96 | ev_disp | class by 13 thresholds on OPC: end, literal/ref/range/sheet prefix (1..6, 8), unary minus (C = (1, 0), op 23), percent (C = B, B = (1, 100), op 21), binary (19..30, 32 union, 33 intersection), function (>= 64), skip (7, 9..15, 17 unary plus, 31, 34..63) | 702 |
| 97 | ev_push | T2 = mode + 4096 SHEET. Modes: 1..4 literal (OPC, OPND); 5 reference (9, K), K = S 2^34 + ROW 2^14 + COL, or #REF!; 6 range corner 1 -> T3..T5 (ROW, COL, bad), reads corner 2; 7 corner 2 -> T6..T8 -> ev_rng; 8 sheet operand (T2 = 9 + 4096 S), reads next OPC; 9 next OPC (5 or 6), reads its OPND. Modes 1..5 write B.TAG at SP. x0 is clamped to [0, 65536] before any 4096 x0 term (literals reach 1e308) | 1599 |
| 88 | ev_rng | PC 0: normalised range record [S, min R, min C, max R, max C, S] block-written at SCR, A = (5, SCR) or #REF! -> ev_push2 PC 0. PC 1 union: node [C.TAG, C.PAY, B.TAG, B.PAY] at SCR, B = (10, SCR) -> ev_disp PC 1. SCR += 6 | 714 |
| 108 | ev_ref1 | block consumer (71 inputs). Area of the operand (TAG 9 from K, TAG 5 from the record). PC 0, 1 implicit intersection (legacy): single row or column, or home row/column inside, else #VALUE!. PC 2, 3 intersection operator: errors left first, different sheets #VALUE!, empty #NULL!, one cell (9, K), else new range record | 1394 |
| 98 | ev_push2 | write B.PAY, SP += 2, TP += 2, B = A | 172 |
| 100 | ev_pop | C.TAG = x0, read C.PAY | 18 |
| 101 | ev_dref | mode merge (C or B from A, C.PAY from x0, T2N result fix to #VALUE!), then in priority: CELL_GET for TAG 9 (sheet from K), implicit intersection (block read, ev_ref1) for TAG 5 / 10, left operand first, never for 32/33; ev_t2n for text in arithmetic, ev_totext for non-text in &; else dispatch on op incl. 32 -> ev_rng PC 1, 33 -> block read of C's record -> ev_ref1 PC 2 | 1976 |
| 102 | ev_arith | coercion, error precedence C error, C bad, B error, B bad; SAFE_ADD (+, - by sign gating) and SAFE_MUL retyped from weights/prim/safe_add.wt, safe_mul.wt (P-D3); / -> ev_div, ^ -> ev_pow0 | 930 |
| 104 | ev_cmp | classes number < text < boolean, blank adopts the other class, numeric tolerance 2^-50 (|a| + |b|) on quarter-scaled values (rows 1 -+ 2^-50, exact literals), text -> ev_scmp_a, 6 AND units for the 6 operators | 2049 |
| 105 | ev_scmp_a | lengths, L = max, empty strings equal | 437 |
| 106 | ev_scmp_b | per packed word: mask past length, UNPACK3 by two FLOORs, fold A..Z (12 step units), compare 48-bit keys | 710 |
| 107 | ev_end | blank -> 0, range -> #VALUE!; write TAG, PAY at CS + 1, CS + 2 -> rc_done PC 1 | 97 |
| 109 | ev_t2n | text to number: PC 0 block-writes HT to HEAP_TOP; PC 1 block-writes words 8..39 to RET_STACK and calls the parser's constant entry 78 (LR 109, LP 2); PC 2 block-reads them -> ev_t2nb. All phases are block ops (output 96 words) | 183 |
| 115 | ev_t2nb | block consumer (97 inputs): restores words 8..12, 15..39, keeps 40..63, A = parser result or #VALUE! when rejected, returns to the saved link | 42 |
| 116 | ev_func | function call dispatch point: stub #NAME?, drops argc - 1 entries | 222 |

**Excel behaviours covered.** Left-to-right error precedence per operand; TRUE/FALSE/blank coercion; text to number coercion with Excel's entry rules (spaces, sign, '(4)', '$', thousands commas, exponent, '%'; text TRUE, dates and other text give #VALUE!); overflow #NUM!; #DIV/0!; comparisons without coercion and with type ordering; case-insensitive text compare; trailing spaces significant; ranges with corners in any order, whole rows and columns; intersection operator (#NULL! when empty); union (a value use gives #VALUE!); legacy implicit intersection of a range used as a value; Sheet!A1 and Sheet!A1:B2.

**Reference values on the operand stack.** TAG 9 cell (PAY = K with sheet), TAG 5 range (PAY = pointer to a 6-word record [S, R1, C1, R2, C2, S] in EVAL_SCRATCH, normalised), TAG 10 union (PAY = pointer to a node [left TAG, left PAY, right TAG, right PAY]). Function arguments are pushed as such (not dereferenced), so function networks see references.

**Why ev_t2n calls the parser (decision E8).** One set of number rules for entry and coercion, nothing duplicated; cost about 48 steps per coercion (spill and restore of the parser are 25 of them).

**Limits.** Text order is UTF-16 code-unit order after ASCII case folding. Unprefixed references resolve on sheet 0 (no home-sheet register; formulas stored on other sheets with relative references are not supported yet). No dynamic-array spill: a multi-cell range as a value follows legacy implicit intersection. A union operand of an intersection gives #VALUE!. Ranges and intersections record no precedents (only cell references do), so a range-dependent formula is ordered only by entry order. 3D references are not produced by the parser. Functions all return #NAME? (ev_func stub, ABI pending). CANCEL_SNAP is not applied. Equality tolerance 2^-50 (open question with D3). Dates in text coercion are out of scope.

**Multi-role weights.** B.PAY on ev_arith's output carries the result, or b when routing to ev_div/ev_pow0 (exclusive gates). The ev_dref LP output encodes which operand a call returns into (0 C, 1 B, 4 and 5 after ev_t2n). ev_push's T2 carries mode and sheet in disjoint integer ranges (mode < 16, sheet times 4096), split exactly by one FLOOR. ev_ref1's A, B and T3..T8 outputs are phase-exclusive. **Tests.** tests/output/eval/test_eval.py (135 cases).
