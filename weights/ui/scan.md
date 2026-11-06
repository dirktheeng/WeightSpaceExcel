# Weight block notes: cell scan and row repaint: sg0 (176), sg1 (177), sr (178), scan (179), su (180), rp (181), dt0 (188), dt1 (189), cd7 (182), cd8 (183), cd9 (184)

Hand-written. Not generated. Log: log/ui-agent.md; decisions U8 (gate and one-step scan), U10 (row repaint, overflow), U11 (display table).

| Id | Step | next |
|---|---|---|
| 176 sg0 | block read zero page 0x01..0x43 | 177 |
| 177 sg1 | key = (HEAP_TOP - 0x302002) + 2^20 CELL_COUNT; equal to UI_SCANKEY: return; else store it, r = c = 0 | (L22, L23) or 178 |
| 178 sr | block read the cache row of r (48 words), T10 = 1 | 179 (scan) or 181 (repaint mode L20 = 1) |
| 179 scan | one cell per step: compare the 8-word slot of (r, c) with the cached (TAG, PAY); hash and probe as encodings/address.md 4 | 179, 180, 174 (row dirty), 178, or return |
| 180 su | block write the new (TAG, PAY) to the cache, c + 1 | 178 |
| 181 rp | right to left over the cache row after gband + hx repainted the row: blank cells count a run (and clear their DISPLAY_TABLE entry), others go to prod with L17 = 188 | 181, 149, 178 or return |
| 188 dt0, 189 dt1 | copy BUF (31 units + 0) into DISPLAY_TABLE (r, c) | 182 |
| 182 cd7 | measure BUF | 129 then 183 |
| 183 cd8 | overflow: text (tag 2) wider than 61 px spreads over kk = min(run, floor((w + 2)/64)) blank cells to the right; their interiors and the gridlines between are filled white | 128 or 184 |
| 184 cd9 | aligned text with clip min(92 + 64 (c + kk), 1278) | 139, then 178 |

**Why rows.** Overflow couples neighbours (a new value to the right clips a left neighbour; clearing a cell lets it overflow further). Repainting the whole cell row (gband, 1 step) and redrawing its non-blank cells right to left handles every case with one rule. The cost is one row repaint per changed row.
**Gate.** Every commit moves HEAP_TOP (the typed string is allocated), deletes change CELL_COUNT, so an unchanged key means no visible value can have changed; navigation-only batches skip the 560-step scan.
**Limits.** Formula results that change without HEAP_TOP or CELL_COUNT moving (none in this stage) would be missed until the next commit. No scrolling: rows 1..28, columns A..T. Numbers do not overflow (Excel shows ###; we clip). DISPLAY_TABLE keeps at most 31 units.
**Parameters.** scan about 1,500, rp about 700, sg1 90, others 15 to 200. **Steps.** Gate 2; scan 560 + 28 + 1 per probe + 2 per changed cell; row repaint 1 (gband) + about 45 (row header) + 20 (rp) + per non-blank cell about 8 + measure + glyph rows.
**Multi-role weights.** None. **Tests.** test_cell_text_alignment (overflow), test_incremental_redraw, test_display_table, test_no_fault_and_step_counts.
