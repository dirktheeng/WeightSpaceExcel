# Weight block notes: weights/kernel/boot.wt (id 0, BOOT)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decisions K1 and K4.

**Computes.** Run with `run(0, zeros(65))`. Ten steps selected by PC (word 7):

| PC | Writes | Next |
|---|---|---|
| 0 | HEAP_TOP (0x01) = 0x302002 | 0 |
| 1 | FORMULA_TOP (0x02) = 0x090000 | 0 |
| 2 | DEP_TOP (0x04) = 0x0C0000 | 0 |
| 3 | NET_NEXT (0x05) = 512 | 0 |
| 4 | ITER_MAX (0x0A) = 100 | 0 |
| 5 | ITER_DELTA (0x0B) = 0.001 | 0 |
| 6 | SCRATCH_TOP (0x0D) = 0x0B0000 | 0 |
| 7 | SHEET_COUNT (0x0F) = 1 | 0 |
| 8 | STAGING_TOP (0x11) = 0x3C0000 | 0 |
| 9 | none; MODE = 1, PC = 0 | 4 (main_poll) |

Every step also sets RSP = 0x100 (empty return stack), L8 = 0x302004 and L9 = 0x302002 (main loop edit buffer pointers, weights/kernel/main_loop.md). All other zero page words start as 0, which is their documented initial value (FAULT, DEP_FREE, CUR_SHEET, CALC_MODE automatic, CALC_GEN, ITER_ON off, CELL_COUNT, STYLE_COUNT, NAME_COUNT, CIRC_FLAG, DATE_1904, REJECT_COUNT), so no write is spent on them. Values from encodings/memory-map.md section 3.

**Derivation.** v2/v3: thermometer t_k = step(PC - k + 0.5), k = 0..9 (GE_K). v4: one-hot o_k = t_k - t_(k+1), o_9 = t_9 (integer rows). v6 is a ROM (encodings/primitives.md): each row has at most one nonzero term per active one-hot, so the address and value are exact, including the non-integer 0.001 (a single product 0.001 * 1 plus exact zeros). Row PC = PC + 1 - 10 o_9 (0 when entering the main loop). Row MODE = o_9.

**Parameters.** 298. Steps: 10, then the main loop.

**Limits.** PC above 9 is not trapped (it is reachable only by a wrong route into id 0). **Multi-role weights.** None.

**Tests.** test_boot_initialises_zero_page_and_halts_on_empty_queue.
