# Weight block notes: CSV export chain (ids 455 to 459, return through 454)

Hand-written. Not generated. Log: log/files-agent.md 2026-11-06. Tests: tests/output/files/test_csv_export.py (5 pass).

**Use.** Call xp_imp (455) with LR, LP and N0 = harness file id. Writes the used range of sheet 0 (A1 to the largest occupied row and column) to the file transfer region and requests io 3. Rows end in CRLF, fields are separated by commas, a field is quoted when it contains , " CR or LF and its quotes are doubled, text is UTF-8 (no BOM, as Excel's "CSV UTF-8" without the BOM). Values: text as stored, numbers and booleans through ev_totext (110, General format, 15 digits), errors as their text. Returns via csv_ret (454) with L0..L11 restored.

| Id | Network | Phases |
|---|---|---|
| 455 xp_imp | spill [LINK, L0..L11], RSP += 13; L0 = 0, L1 = L2 = -1, L4 = N0, L5 = L6 = 0, L7 = 0x201001 | 1 |
| 456 xp_scan | read KEY of every slot (65,536 steps); for 1 <= KEY <= 2^34: row = FLOOR((KEY - 1) 2^-14), col = KEY - 1 - 2^14 row, L1 = max row, L2 = max col (max(a, b) = a + relu(b - a), gated); then read HEAP_TOP -> 457 PC 9 | 0, 1 |
| 457 xp_cell | PC 9 L3 = HEAP_TOP (scratch for value text, never committed); 0 finish (byte count at 0x201000, io 3) or CELL_GET (r, c); 1 comma if c > 0, dispatch on TAG; 3 handle -> xp_str; 2 next column or CR; 4 LF, next row; 8 block read the spill -> 454 | 7 |
| 458 xp_str | PC 0 read len; 1 init or return on empty; 2 scan words for special units; 7 read word 0; 3, 5 one output byte per step (UTF-8 1 to 3 bytes, doubled quote); 4 read next word; 6 closing quote | 8 |
| 459 xp_err | error code -> heap string by one block write [len, 1, w0..w4] (packed constants worked out by hand: word = c0 + 2^16 c1 + 2^32 c2) | 1 |

**Derivations.** UNPACK3 (two FLOOR blocks) on the word, the unit at position T9 by relu MUX (M = 2^17), FLOOR(u / 64) and FLOOR(u / 4096) for the UTF-8 bytes (192 + a; 224 + b, 128 + a - 64 b; 128 + u - 64 a), each byte term a relu gated by (emit phase, class, byte index). x0 is gated by mul (exact) wherever it may hold a cell value.

**Parameters.** xp_imp 110, xp_scan 290, xp_cell 1,794, xp_str 5,718, xp_err 888 (counted by hand from the layer shapes). **Steps.** 65,540 for the scan, then per cell about 10 (CELL_GET) plus 1 per output byte plus value text conversion.

**Limits.** Sheet 0 only; the used range ignores formatting-only cells (none exist yet). Numbers use ev_totext's General text, not the column-width-dependent display Excel writes for narrow columns (Q-F4). Characters outside the BMP are written as two 3-byte sequences (CESU-8), not one 4-byte sequence. Output limited by the transfer region (2^20 bytes). **Multi-role weights.** None beyond phase-exclusive gating.
