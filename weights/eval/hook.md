# Weight block notes: hk_commit (80), hk_delete (81)

Hand-written. Not generated. Log: log/eval-agent.md "recalc networks"; decisions E1, E5. Registers: README.md.

**Computes.** Entered as the return of CELL_SET. Saves AR1, AC1 to HR, HC, P0 (slot base) to CS, P1 to T6, sets RET = 14 (hk_commit, Enter path, back to c_done_rd) or 8 (hk_delete, Delete path, back to ev_next). nz = step(P1 - 0.5). P1 != 0: read FL_COUNT (0x15), next rc_chain PC 0 (record precedents). P1 = 0: read CALC_GEN (8), rc_chain PC 7 (recalculate only). Rows: addr = 8 + 13 nz, PC = 7 - 7 nz, all CONST or one-weight copies.

**Kernel change needed (not made by this agent).** weights/kernel/c_set.wt, layer v7, bias 9 (LR row, currently 14) -> 80. weights/kernel/ev_decode.wt, final dense biases line "# biases (29)", 9th bias (word 8 LR, currently 8) -> 81. Nothing else changes: CELL_SET already returns P0 = slot base and preserves P1 and the address register.

**Parameters.** 20 each. Steps: 1. **Limits.** None. **Multi-role weights.** None.
**Tests.** every test in tests/output/eval/test_eval.py enters through hk_commit.
