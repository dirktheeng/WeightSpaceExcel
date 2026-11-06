# Weight block notes: weights/kernel/cs_hash.wt (id 16, cell store entry)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decision K2. Spec: encodings/address.md sections 3 and 4.

**Interface (CELL_GET and CELL_SET).** Caller sets next = 16, LR, LP, address register (AS, AR1, AC1) = (SHEET, ROW, COL), T1 = 0 for get or 1 for set; for set also A = (TAG, PAY) and P1 = formula record address (0 for a constant). Returns to (LR, LP).
- Get: STATUS 0 and A = the stored value, or STATUS 1 and A = (0, 0) (blank) if absent. P0 = slot base (found slot, or the empty slot where the probe stopped).
- Set: STATUS 0, P0 = slot base. Writes KEY (new cells), TAG, PAY, FORMULA = P1, CALC = 4 CALC_GEN + 1 (dirty), and increments CELL_COUNT for new cells.
- Clobber set: words 0..7, STATUS, A (get), P0, T0, T1. Locals L0..L23, B, C, P1, N0, N1 and the address register are preserved.
- NS is fixed at 0 (cells). Row, column and auxiliary namespaces need a NS argument (open item K-Q1).

**This network.** t = 1000003 S + 40503 R + 65599 C (R4 integer row, t < 2^42). q = t 2^-16 (R1 exact), r = ROUND(q), g = step(65536 r - t) (rounded up), slot = t - 65536 (r - g). addr = P0 = 0x10000 + 8 slot, written as the integer row 8 t - 524288 r + 524288 g + 65536 (exact). T0 = S 2^34 + R 2^14 + C + 1 = K + 1 (exact, below 2^50). Reads the key word at P0; next 17.

**Parameters.** 76. Steps: 1.

**Limits.** SHEET, ROW, COL inside encodings/address.md ranges. **Multi-role weights.** None. T1 passes through untouched.

**Tests.** test_set_then_get_roundtrip, test_collision_probes_linearly, test_probe_wraps_at_table_end, test_sheets_are_separate.
