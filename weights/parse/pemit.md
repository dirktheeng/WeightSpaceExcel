# Note: weights/parse/pemit.wt (id 74)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Phase table.** 1: write TV at OUTP + 1, OUTP += 2, NT += 1; then TK 2 -> 2, TK 8 or 9 -> parse (re-run after a missing argument), else -> idle (RDOK 0). 2: write 7 at OUTP. 3: write TV2 at OUTP + 1, OUTP += 2, NT += 1 -> idle. 4: write TOPA at OUTP + 1 (operand of a popped operator or call), OUTP += 2, NT += 1. 5: read 0x2000 + SP - 1, SP -= 1, PP = 1 -> parse. 6: write 0 at OUTP + 1 (end token operand). 7: [FT] = HS. 8: [FT + 1] = FT + 8. 9: [FT + 2] = NT. 10: HEAP_TOP = HT. 11: FORMULA_TOP = OUTP + 2, P1 = FT -> restore.
**Blocks.** ph_k one-hot from PC; TK 2, 3, 8, 10 thresholds for the PC 1 branches; addresses and integer values by MUX_INT (M = 2^23), TV and TV2 by mul gates (TV is any double). mem_op = 2 - ph5.
**Limits.** 1,092 parameters. **Multi-role weights.** None.
