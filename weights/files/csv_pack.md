# Weight block notes: CSV import chain (ids 449 to 454)

Hand-written. Not generated. Log: log/files-agent.md 2026-11-06; decisions F1, F2 in log/WORKLOG.md. Tests: tests/output/files/test_csv_import.py (6 pass).

**Use.** Run csv_scan (448) with P1 = FILE_SCRATCH 0x3B0000, then call csv_imp (453) with LR, LP, P0 = 0x3B0000 (token stream), AR1, AC1 = top left target cell (sheet 0). Returns to (LR, LP) with STATUS 0, RSP balanced and L0..L11 restored (they are spilled at entry, so callers lose nothing). Each nonempty field is committed as if typed: parser 78 (weights/kernel/commit.md contract), CELL_SET 16, and the recalculation hook, so formulas record precedents and recalculate (a formula imported before the cells it uses still ends correct). A field the parser rejects is stored as text (decision F3). Empty fields leave the cell blank.

| Id | Network | Steps |
|---|---|---|
| 453 csv_imp | block write [LINK = 65536 LR + LP, L0..L11] at RSP, RSP += 13; L0 = P0, L1 = AR1, L2 = L8 = AC1, L9..L11 = 0 | 451 |
| 451 csv_back | read HEAP_TOP | 449 PC 1 |
| 449 csv_pack | PC 1: HS = L3 = x0, waddr L7 = x0 + 2, len = acc = pos = 0; apply pending separator L9 (1 FE: col + 1; 2 RE: row + 1, col = L8; 3 END: block read spill, RSP -= 13 -> 454); else read token. PC 2: token: byte -> UTF-8 step and maybe one UTF-16 unit packed at pos of acc (word written when full -> PC 3); separator with len 0 -> its action at once; with len > 0 -> write the partial word, L9 = kind, -> 452. PC 3: read token. | |
| 452 csv_commit | PC 0 write len at HS; 1 refcount 1; 2 HEAP_TOP = waddr + [pos > 0]; 3 call parser (A = (2, HS), address (0, L1, L2), P1 = 0, LR 452 LP 4); 4 ok = [STATUS = 0]: A, P1 kept, else A = (2, HS), P1 = 0; call CELL_SET (T1 = 1, LR = 450) | 16 |
| 450 hk_file | the hk_commit block (weights/eval/hook.md) retyped with RET = 451, so rc_fin returns to csv_back | 82 |
| 454 csv_ret | block consumer of the 13 spill words: L0..L11 restored, next = FLOOR(LINK 2^-16), PC = LINK - 65536 next, STATUS 0 | LR |

**UTF-8 (csv_pack).** Bytes < 128 are units; C0..DF, E0..EF, F0..F7 lead bytes set cp = b - lead base and need = 1, 2, 3; a continuation byte sets cp = 64 cp + b - 128, need - 1, and emits cp when need was 1. cp >= 65536 (4-byte sequences) emits U+FFFD (limit: no surrogate pair yet); a stray continuation emits U+FFFD. U+FEFF at the start of a field is dropped (covers the BOM; a ZWNBSP at a field start is also dropped, a stated deviation). Bytes are always read as UTF-8, while Excel reads a BOM-less CSV in the system ANSI code page (Q-F2).

**Derivations.** Same toolkit as csv_scan.md: IS_K pairs, AND units step(sum - k + 0.5) gated by the phase, MUX_INT relu terms with M = 2^23 (addresses, counters), 2^30 (cp), 2^41 (token word), 2^50 (packed word acc < 2^48). The unit shift u 2^(16 pos) is one relu per position, gated by e_k = emitted and pos = k; FFFD enters as constants 65533 2^(16 k) gated the same way. csv_ret uses the FLOOR block of primitives.md. All rows integer and exact (R4) except the FLOOR rows (power of two scaling, R1 and R3).

**Registers.** csv_pack and csv_commit keep their state in L0..L11, which the parser, CELL_SET and the recalculation chain preserve (weights/eval/README.md). Clobbered for the caller: words 0..39 except RSP, MODE.

**Parameters.** csv_pack 4,618; csv_commit 918; csv_imp 119; csv_back 16; hk_file 20; csv_ret 39 (dense weights and biases, counted by hand from the layer shapes). **Steps.** About 2 per byte of text plus per committed field 6 + parser + CELL_SET + recalculation.

**Limits.** 65,535 tokens per scan (FILE_SCRATCH size; no chunking yet). Sheet 0 only. **Multi-role weights.** L9 holds the pending separator only between a commit and the next PC 1; L3..L7 are rebuilt at every PC 1.
