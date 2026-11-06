# Weight block notes: weights/ui/ce0..ce5, prod, ce7, ce8 (ids 143..151, visible cells)

Hand-written. Log: log/ui-agent.md; decisions U2 (dirty scheme by displayed-value cache), U5.
| Id | Step | next |
|---|---|---|
| 143 ce0 | CELL_GET (16) of (0, r = L12, c = L13) | 16, then 144 |
| 144 ce1 | read cached TAG at 0x0F1000 + 40 r + 2 c | 145 |
| 145 ce2 | L14 = cached TAG; read cached PAY | 146 |
| 146 ce3 | changed = TAG or PAY differs (four steps of R2 differences): write new TAG to cache | 147, or 151 if unchanged |
| 147 ce4 | write new PAY to cache | 148 |
| 148 ce5 | fill (128) the interior x 31 + 64c .. + 62, y 196 + 20r .. + 18 white | 128, then 149 |
| 149 prod | value text into BUF: number fnum, text heap copy, boolean str 108/113, error str by code; other tags go to L18 | producer, then L17 |
| 150 ce7 | aligned text: X 32 + 64 c, Wb 61, right for numbers, left for text, centre for booleans and errors, top 201 + 20 r, black, clip min(92 + 64 c, 1279) | 138, then 151 |
| 151 ce8 | next cell (row-major over 28 x 20); after (27, 19) return to (L22, L23) | 143 or L22 |
**Dirty scheme.** The cache holds the (TAG, PAY) last drawn for each visible cell. Every frame compares every visible cell with it and repaints only changed cells, so commits, deletes and recalculated formula values all redraw without any per-commit kernel hook. Zeroed memory means "all blank drawn", which matches a fresh grid. The cache is not invalidated, so a second full frame (152 from PC 0) would not redraw unchanged non-blank cells; the engine draws the full frame only once, at boot.
**Multi-role words.** In prod, PAY is a double for numbers and a handle or code otherwise. The handle reaches T0 only through mul by is2 (exact gating, V1 safe), and error and boolean paths use step tests on PAY, which are finite for every double. L17/L18 are the producer links: cells set 150/151 through the scene ROM, and the formula bar sets 168/169 (fbH). They never overlap because the scene runs the two subroutines in sequence.
**Limits.** Text never overflows into empty neighbour cells (Excel overflows left-aligned text); it is clipped at the cell edge. Same-value formula edits do not trigger a repaint, which is correct because the display is unchanged. 560 cells visible, no scrolling.
**Parameters.** about 1,100 for the group (prod is about 520 of it). **Steps.** About 6 per unchanged cell (about 3,400 per frame), plus 1,197 fill steps and the text for each changed cell. **Tests.** test_cell_text_alignment, test_incremental_redraw.
