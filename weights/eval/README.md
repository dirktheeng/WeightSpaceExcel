# weights/eval: formula evaluator and recalculation (ids 80..117)

Hand-written. Not generated. Log: log/eval-agent.md; decisions E1..E7 in log/WORKLOG.md ("2026-11-06 Stage 1: evaluator and recalculation"). Notes: hook.md (80, 81), recalc.md (82..94), evaluator.md (88, 95..109, 115, 116), format.md (110..113), ev_div.md (103), pow.md (99, 114, 117). Ids 80..117 are all in use after session 2.

## Register use (encodings/control.md section 2)

| Word | Name | Owner / meaning |
|---|---|---|
| 7 | PC | phase inside a network |
| 8, 9 | LR, LP | links for CELL_GET, ev_t2n, ev_totext calls |
| 13, 14 | A | CELL_GET result, call argument, scratch |
| 15, 16 | B | top of the operand stack (TOS) |
| 17, 18 | C | left operand of a binary operator |
| 19..21 | AS AR1 AC1 | CELL_GET address; in ev_fmt*/ev_cat: Q, pc, m / S, SN, SW |
| 22 | GEN | current CALC_GEN during recalculation |
| 23 | HT | heap top during recalculation (written back by rc_fin) |
| 24 | CYC | current DFS frame is in a cycle |
| 25 | P0 | CELL_GET slot; ev_fmt*: dp; ev_cat: SWN |
| 26 | P1 | formula record of the cell being entered or evaluated |
| 27 | N0 | ev_fmt*: tail code queue T |
| 28 | N1 | CE, next precedent edge |
| 29, 30 | T0, T1 | ev_fmt*: tc, OH; ev_cat: OH in T1 |
| 31 | T2 | current operator code (remapped: unary minus 23, percent 21) |
| 32..39 | T3..T10 | record phase n, DT, HEAD, saved P1; DFS precedent P (T3); compare handles and loop (T3..T10); append WA, ACC, POS, LEN (T3..T6) |
| 52..56 | TP SP HR HC SCR | token pointer, operand stack pointer, home row/col, scratch pointer |
| 57..63 | CS DEPTH FLI FLN LOW CIRCV RET | DFS current slot, stack depth, formula list index and count, Tarjan low link (-1 = at root), first cycle cell K + 1, hook return id |

Kernel locals L0..L11 (words 40..51) pass through every network unchanged, except rc_fin, which sets L8 and L9 on the Delete path.

## Memory used (encodings/memory-map.md)
- FL_COUNT = zero page 0x15 (from the stage 1 reserved range): number of entries in the formula list at CALC_CHAIN 0x0E0000 (one cell slot base per word).
- Formula record word 6 (spare in section 6): head of the cell's precedent edge list.
- DEP_POOL nodes [precedent slot base, next] (2 words), allocated at DEP_TOP.
- WORK_STACK 0x3000: one packed word per DFS parent frame, CS + 2^20 CE + 2^40 LOW + 2^51 CYC.
- Cell slot PAY word holds the frame index while the cell is being visited (state 2).
- OPER_STACK 0x1000 (2 words per value below TOS), EVAL_SCRATCH 0xB0000 (reset per evaluation; unused so far), TEXT_HEAP from HEAP_TOP for & results.
- Value tag 9 (reserved for the cell engine, encodings/value.md): unresolved cell reference on the operand stack, PAY = K (sheet 0).

## Session 2 additions
- T2 (word 31) during a push carries mode + 4096 SHEET (ev_push); T3..T8 hold range corners between ev_push and ev_rng, and the left area of an intersection between ev_ref1 PC 2 and PC 3; T7 (word 36) holds the prefix sheet in the recalc token walk (rc_scan, rc_ref); T7 also carries b into ev_pow2.
- EVAL_SCRATCH (SCR) now holds 6-word range records and union nodes (reset per evaluation).
- Value tags used: 9 cell reference, 5 range reference, 10 union reference (reserved cell-engine range 9..15, encodings/value.md).
