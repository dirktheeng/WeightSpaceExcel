# Weight block notes: recalculation networks (ids 82..94)

Hand-written. Not generated. Log: log/eval-agent.md; decisions E1..E4 in log/WORKLOG.md. Registers and memory: README.md. Each network is one step; PC selects phases. Gated register updates use MUX_INT relu rows (encodings/primitives.md D14, M = 2^23, or 2^40 for packed keys); gates are thermometer step units on PC; every address and value row is an integer row (R4) except mul-gated doubles.

| Id | File | Step(s) | Params |
|---|---|---|---|
| 82 | rc_chain | p0 x0 = FL_COUNT n: T3 = n, write CS at CALC_CHAIN + n; p1 write n + 1 at 0x15; p2 read DEP_TOP; p3 T4 = DT, read P1 + 1; p4 TP = x0, T5 = HEAD = 0, read [TP] -> rc_scan; p5 write DT at DEP_TOP; p6 read CALC_GEN; p7 GEN = x0 + 1, write it; p8 read FL_COUNT; p9 FLN = x0, FLI = CIRCV = DEPTH = 0, read HEAP_TOP; p10 HT = x0 -> rc_next | 1100 |
| 83 | rc_scan | token walk: OPC 0 -> write HEAD at T6 + 6 (record word 6), rc_chain p5; OPC 5 -> read OPND, rc_ref PC 0 with T7 = sheet if entered at PC 2 (right after a prefix) else 0; OPC 8 -> read OPND, TP += 2, rc_ref PC 1; else TP += 2, read next OPC. PC 1 = advance after an edge | 270 |
| 84 | rc_ref | PC 0: resolve OPND (FLOOR on 2^-36, 2^-15 scalings, flags by thermometer, relative rows by relu, range check by 4 step units); write HEAD at DT + 1; CELL_GET on sheet T7 (LR 85) or skip if outside the grid. PC 1: T7 = sheet operand, read [TP] -> rc_scan PC 2 | 330 |
| 85 | rc_got | found: write P0 at DT, HEAD = DT, DT += 2, P1 = T6; absent: CELL_SET a blank cell (so every precedent has a slot), back to itself | 164 |
| 86 | rc_next | FLI < FLN: read CALC_CHAIN[FLI] -> rc_edge PC 0; else write CIRCV to CIRC_FLAG -> rc_fin. LOW = -1 marks "at root" | 61 |
| 87 | rc_fin | write HT to HEAP_TOP, next = RET; Delete path also L8 = HT + 2, L9 = HT | 126 |
| 89 | rc_enter | write CALC = 4 GEN + 2 (visiting), write DEPTH into the cell's PAY, read record word 6 -> rc_loop PC 1 | 120 |
| 90 | rc_loop | CE != 0: read edge -> rc_edge PC 1; CE = 0 and CYC: write TAG 1 -> rc_done PC 0; else read KEY -> ev_start | 94 |
| 91 | rc_edge | PC 0: P = list slot, FLI += 1; PC 1: P = edge slot, read next; PC 2: CE = next; read CALC of P -> rc_class | 189 |
| 92 | rc_class | PC 0 x0 = CALC: s = x0 - 4 GEN: 3 done (skip), 2 visiting (rc_back), else read FORMULA; PC 1: 0 skip, else enter (root: write visiting itself; inside: push the packed frame) | 729 |
| 93 | rc_back | LOW = min(LOW, stack index of P), CYC = 1, first cycle: read KEY of P into CIRCV | 173 |
| 94 | rc_done | PC 0 cycle value 0; PC 1 CALC = 4 GEN + 3; PC 2 pop or rc_next; PC 3 unpack frame (3 FLOORs), Tarjan merge: prop = [LOWc <= DEPTH], LOW = min, CYC = OR | 741 |

**Cycle rule.** A cell is set to 0 without evaluation when its frame's CYC is set, that is when a back edge or a child's low link reached it or an ancestor (Tarjan). Dependents of a cycle evaluate normally and see 0 (case cir10). CIRC_FLAG = K + 1 of the first back-edge target; reset to 0 by every recalculation.

**Limits.** Full recalculation of every formula cell on every commit (each commit marks all cells stale through CALC_GEN, so "dirty" = all). The formula list is append only (a cell re-entered as a formula appears twice; the second visit is a done-skip, about 4 steps). Range tokens (6, 7) record no precedents (ranges only matter for functions, stage 3). WORK_STACK depth limit 2047 frames (frame packing); no overflow fault yet. Cross edges into an already finished part of a cycle can leave such a cell evaluated instead of 0 (Tarjan without an SCC stack), not reachable by the stage 1 cases. Edge nodes of replaced formulas are not freed (DEP_FREE unused).

**Step counts (measured, tests/output/eval).** Commit of =1+2 into an empty sheet: 62 steps including CELL_SET (9) and the kernel's 7 trailing steps; a 4-cell chain entered top-down: 136 steps for the final commit.

**Multi-role weights.** The cell PAY word holds the DFS frame index while CALC state is 2 and the value otherwise (exclusive by CALC state; only rc_back reads it in state 2). The value word of rc_class carries a packed frame (push) or 4 GEN + 2 (root enter), exclusive gates. **Tests.** test_references_and_edit_recalc, test_dependents_entered_before_precedents, test_diamond_and_text_chain, test_replaced_formula_no_longer_depends, test_self_cycle, test_cycle_dependent_and_break, test_three_cycle, test_error_clears_after_fix.
