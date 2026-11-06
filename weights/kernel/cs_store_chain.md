# Weight block notes: cell store chain networks (ids 18 to 26)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decision K2. Files: cs_ltag.wt, cs_lpay.wt, cs_cntr.wt, cs_cntw.wt, cs_wtag.wt, cs_wpay.wt, cs_wform.wt, cs_genr.wt, cs_wcalc.wt, all in weights/kernel/. Interface: weights/kernel/cs_hash.md.

Each is one step: a small dense "head" from a gathered slice of the input, giving words 0..6 (and PC or STATUS when it returns), concatenated with PASS slices for every other word. Addresses are integer rows (R4); written values are single weight-1 copies (R1, exact for any double) or integer rows.

| Id | File | Input word 0 | Step | next | Params |
|---|---|---|---|---|---|
| 18 | cs_ltag | TAG | A.TAG = x0; read P0 + 2 | 19 | 24 |
| 19 | cs_lpay | PAY | A.PAY = x0; STATUS 0; PC = LP | LR | 27 |
| 20 | cs_cntr | | read CELL_COUNT (0x0C) | 21 | 14 |
| 21 | cs_cntw | count | write count + 1 to 0x0C | 22 | 14 |
| 22 | cs_wtag | | write A.TAG at P0 + 1 | 23 | 21 |
| 23 | cs_wpay | | write A.PAY at P0 + 2 | 24 | 21 |
| 24 | cs_wform | | write P1 at P0 + 3 | 25 | 21 |
| 25 | cs_genr | | read CALC_GEN (0x08) | 26 | 14 |
| 26 | cs_wcalc | gen | write 4 gen + 1 at P0 + 6; STATUS 0; PC = LP | LR | 45 |

**Step counts (including the hash and probe steps).** Get hit: 4 steps plus 1 per extra probe. Get miss: 2 plus probes. Set of an existing cell: 6. Set of a new cell: 9. (Tests count one more for the HALT_OK step they return into.)

**Limits.** CALC is written dirty with the current generation; this is the mark the recalculation engine will look for. **Multi-role weights.** None.
