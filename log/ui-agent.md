# UI agent log (weights/ui/, stage 2 minimal UI)

## 2026-11-06, Stage 2: design so far

- Read GOAL.md, docs/*, harness/FORMAT.md, harness.py, encodings/*, weights/kernel notes (main_loop, ev_decode, commit, boot, cell store), weights/prim/CONVENTIONS.md and log/WORKLOG.md.
- Constraint that drives everything: one memory operation per step, so every pixel costs one step. A full 1280 x 800 frame is about 1.02 million steps. Incremental frames must touch only what changed.
- Architecture (decision U2 in WORKLOG, to be written): one network per step kind, routed by `next`, like the kernel (K1). Ids from the rendering range 128..191:
  - 128 ui_fill: rectangle fill, one pixel per step. Solid colour, or the grid pattern (line colour where (x - 31) mod 64 = 63 and/or (y - 196) mod 20 = 19, else background), with a clip box. The pattern is computed from (x, y) by two FLOORs, so the grid, both header strips and any later repaint are each one rectangle call with no overdraw.
  - 129 ui_glyph: draws (or measures, 1 step per char) a 0-terminated text run from a one-unit-per-word buffer. Font ROM is a 96 x 13 dense block typed glyph by glyph: each glyph row is one decimal number whose digits are the pixels (visual typing, e.g. 0001000), and column 13 is the advance width times 10^12. Pixels are extracted by repeated ROUND(r / 10) (exact because digits are 0 or 1).
  - 130 ui_str (constant strings ROM), 131 ui_fnum (General number to text), 132 ui_fcol (column letters), 133..137 heap string copy, 138..139 aligned text (measure, then draw left, right or centred), 140..142 header loops, 143..151 visible cell loop with a displayed-value cache (only changed cells are repainted), 152 ui_scene (frame command ROM), 153 ui_redraw (incremental entry), 154..158 active cell outline, 159..168 name box and formula bar.
- Dirty scheme: a cache of the last drawn (TAG, PAY) per visible cell in UI_STATE (0x0F1000 + 2 (20 r + c)). Each frame looks up every visible cell, compares with the cache and repaints only changed cells. This catches commits, deletes and recalculated formulas without any per-commit kernel hook. The active cell outline is erased by repainting exactly its 5 rectangles with the grid pattern (they never overlap text), using the previous active cell kept at UI zero page 0x40, 0x41.
- Layout (Excel 2016 to 2021 "Colorful", 100 percent zoom): title bar and tab strip y 0..54 #217346; ribbon body y 55..146 #F3F3F3; border y 147 #D4D4D4; formula band y 148..175 with name box x 3..104 and formula box x 160..1276 (border #C6C6C6); column headers y 176..195 (#EFEFEF, separators #D4D4D4); row headers x 0..30; grid origin (31, 196); column width 64 px, row height 20 px (8.43 chars and 15 pt); gridlines #E1E1E1; sheet tab bar from y 756, status bar to 799. Font: 12-row glyph box, cap height 9, x height 7, descender 3, digit advance 7 px.
- Kernel hooks needed (I may not edit weights/kernel): boot's final route 4 -> 152, and ev_next's batch-done route 4 -> 153. Details in the final report.

## 2026-11-06, first preview
- Coordinator asked for an early PNG. Writing ui_fill first and a PNG dump helper.
- ui_fill (128) written by hand. Forward pass 1: a 4 x 2 rectangle took 9 steps and was exact. A 1280 x 101 grid band took 129,281 steps in 7.4 s (about 57 us per step), with gridlines at x 30 and 94 and y 195 and 215 as derived. Preview PNG from 16 fill calls (1.08M steps): tests/output/ui/out/preview_fill.png. Reported to the coordinator.

## 2026-11-06, font and text
- Font format decision U4: each glyph row is a decimal number whose digits are the pixels, so the bitmap reads visually in the file and needs no binary-to-decimal arithmetic by hand. The ROM is laid out with one glyph per W row ([e_y, 1] input) so each glyph's block is contiguous. ADV rides in a 13th column times 10^12.
- Drew all 96 glyphs by hand (32..126 plus the box) in glyph.wt. Forward pass 1: "Ab1,gy" measured 38 px in 9 steps and drew correctly (459 steps). Worked on the first run.
- str (130): forward pass 1 returned all 23 strings exactly.
- atx0/atx1 (138, 139): left, right and centre of "12.5" in a 60 px box landed at ink 101..122, 137..158 and 119..140 as derived. (A first harness load failed with "unknown layer type 0" while another agent's file was mid-write; it loaded fine on retry and all my files load individually.)
- fcol (132): A, B, T, Z, AA, AB, AZ, BA, ZZ correct.
- fnum (131): the 12 DIGITS chains were retyped from weights/prim/digits.wt and renumbered. 16 cases correct on the first run, including 1/3, -1/3, 2/3, 123456.123456 -> 123456.1235, the 9.99999999999 -> 10 carry, and 0.001.
- Rule note: while starting fnum.wt I left an empty shell `for` loop (with no body output) in a heredoc command. It emitted nothing, and every weight row was typed by hand afterwards. Recorded for transparency; no loops were used after that.
- Heap copy chain (133..137): '', 'a', 'ab', 'abc', 'abcd', 'hello world' and 'Total 2026' correct.

## 2026-11-06, loops and frame
- Headers (140..142): 48 labels in 6,411 steps; the zoomed PNG showed A..F and 1..5 centred.
- Cells (143..151), outline (154..158), formula bar (159..169), scene ROM (152) and redraw (153) written. First full frame after typing 9 cells: 1,109,082 steps, 64 s, FAULT 0. tests/output/ui/out/frame_full.png looks like Excel 2016: green title and tabs, ribbon, name box "B2", formula bar "12", headers, grid, text, outline with fill handle, Sheet1 tab, Ready.
- Incremental: typed C4, cleared A1, moved to D6, then ran 153. 31,906 steps. A1 erased, C4 drawn, old outline erased exactly to the grid pattern, new outline drawn, name box D6.
- Coordinator spotted "12" left-aligned. The cell held TAG 1 (checked in memory), so the renderer was at fault. Forward pass of ce7 alone showed align 0 for every tag: v1 sliced input 13 (STATUS) instead of input 14 (A.TAG). Fixed the slice to `slice 0 14 15`. Rerun: tag 1 gives align 1, tag 2 gives 0, tags 3 and 4 give 2. Numbers are now right-aligned.
- Added a test fixture whose active cells have content: A2 "Apples" in the full frame and C3 "=1+2" in the incremental frame. The formula bar shows them (the formula comes from the record's text handle).
- tests/output/ui/test_ui.py: the first run failed 1 of 40. The test expected a 2-pixel left ring for column A, but U1 clamps it to x 31. The test expectation was corrected; the weights are unchanged. Second run: 40 passed in 68 s. The compliance check flagged ui_util's PNG writer (open() with a non-static path); it now uses Path.write_bytes (write only). test_harness_frozen fails because of the harness-v2 agent's edits, not this work.
- Steps per frame on harness v1: full frame about 1.10M (chrome fills 1.02M, headers 6.4k, cells scan 3.4k plus about 1.3k per non-blank cell, outline about 1k, formula bar about 24k). Incremental frame about 30k plus about 1.3k per changed cell.
- Next: once log/harness-v2-agent.md publishes the block-write encoding, fill (128) becomes one step per scanline run (about 800 steps for the full frame) and glyph one step per glyph row.
