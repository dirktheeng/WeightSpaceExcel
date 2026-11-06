# Weight block notes: evaluator networks (ids 95..102, 104..109, 116)

Hand-written. Not generated. Log: log/eval-agent.md; decisions E5, E6 in log/WORKLOG.md. Token format: encodings/memory-map.md sections 6 and 13. Values: encodings/value.md.

**Fetch protocol.** A step that issues read [TP] routes to ev_disp PC 0, which receives OPC and either reads OPND (TP + 1) for the handler or reads the left operand TAG (SP - 2) for binary operators. Operators that finish without a memory write issue the next OPC read themselves (TP += 2).

| Id | File | Computes | Params |
|---|---|---|---|
| 95 | ev_start | PC 0 HR, HC from KEY (FLOOR of (x0 - 1) 2^-14); PC 1 P1 = record; PC 2 TP, SP = 0x1000, SCR = 0xB0000, read first OPC | 393 |
| 96 | ev_disp | class by 11 thresholds on OPC: end, literal/ref/range, unary minus (C = (1, 0), op 23), percent (C = B, B = (1, 100), op 21), binary, function (>= 64), skip (7..15, 17 unary plus, 31, 32, 34..63) | 656 |
| 97 | ev_push | literal (OPC, OPND); reference (9, K) or #REF!; range #VALUE!; write B.TAG at SP | 271 |
| 98 | ev_push2 | write B.PAY, SP += 2, TP += 2, B = A | 172 |
| 100 | ev_pop | C.TAG = x0, read C.PAY | 18 |
| 101 | ev_dref | mode merge (C or B from A, C.PAY from x0, T2N result fix to #VALUE!), then CELL_GET for tag 9 operands (left first), ev_t2n for text in arithmetic, ev_totext for non-text in &, else dispatch on op | 1132 |
| 102 | ev_arith | coercion, error precedence C error, C bad, B error, B bad; SAFE_ADD (+, - by sign gating) and SAFE_MUL retyped from weights/prim/safe_add.wt, safe_mul.wt (P-D3); / -> ev_div, ^ -> ev_pow0 | 930 |
| 104 | ev_cmp | classes number < text < boolean, blank adopts the other class, numeric tolerance 2^-50 (|a| + |b|) on quarter-scaled values (rows 1 -+ 2^-50, exact literals), text -> ev_scmp_a, 6 AND units for the 6 operators | 2049 |
| 105 | ev_scmp_a | lengths, L = max, empty strings equal | 437 |
| 106 | ev_scmp_b | per packed word: mask past length, UNPACK3 by two FLOORs, fold A..Z (12 step units), compare 48-bit keys | 710 |
| 107 | ev_end | blank -> 0, range -> #VALUE!; write TAG, PAY at CS + 1, CS + 2 -> rc_done PC 1 | 97 |
| 109 | ev_t2n | text to number hook, stub: #VALUE! | 30 |
| 116 | ev_func | function call dispatch point: stub #NAME?, drops argc - 1 entries | 222 |

**Excel behaviours covered.** Left-to-right error precedence per operand; TRUE/FALSE/blank coercion; overflow #NUM!; #DIV/0!; comparisons without coercion and with type ordering; case-insensitive text compare; trailing spaces significant.

**Limits.** Text to number coercion is a stub (17 stage 1 coercion cases fail until ev_t2n calls a number lexer; the parser entry 78 preserves L12..L23 but clobbers B, C and T registers, so a spill is needed first). Text order is UTF-16 code-unit order after ASCII case folding (Excel uses locale collation for punctuation and non-ASCII). Ranges as values give #VALUE! (no implicit intersection or spill); intersection (op 33, network 108) and union are not built (the parser does not emit them yet). Functions all return #NAME?. CANCEL_SNAP is not applied. The equality tolerance 2^-50 is a chosen value (open question shared with D3). Sheet 0 only.

**Multi-role weights.** B.PAY on ev_arith's output carries the result, or b when routing to ev_div/ev_pow0 (exclusive gates). The ev_dref LP output encodes which operand a call returns into (0 C, 1 B, 4 and 5 after ev_t2n). **Tests.** tests/output/eval/test_eval.py (91 cases).
