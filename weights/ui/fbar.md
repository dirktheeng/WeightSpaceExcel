# Weight block notes: weights/ui/fbA..fbJ, fbX (ids 159..169, name box and formula bar)

Hand-written. Log: log/ui-agent.md; decision U1.
| Id | Step |
|---|---|
| 159 fbA | fill the name box interior x 4..103, y 152..171 white |
| 160 fbB | fcol(L3) into BUF |
| 161 fbC | fnum(L2 + 1) appended (P0 at fcol's terminator) |
| 162 fbD | aligned text X 6, left, top 156, clip 101 |
| 163 fbE | fill the formula box interior x 161..1275, y 152..171 white |
| 164 fbF | CELL_GET of the active cell |
| 165 fbG | found: read FORMULA (slot + 3); blank: return |
| 166 fbH | formula: read record word 0 (typed text handle); constant: prod(A) with links 168/169 |
| 167 fbI | heap copy of the formula text |
| 168 fbJ | aligned text X 163, left, top 156, clip 1272, return to (L22, L23) |
| 169 fbX | return to (L22, L23) (nothing to show) |
**Limits.** A constant number shows in General display form, not Excel's full-precision edit form. The formula text is shown as typed. There is no edit-mode caret, and typing does not echo into the bar until the entry is committed.
**Parameters.** about 400 for the group. **Steps.** about 24,000 per frame (the two box repaints dominate). **Tests.** test_formula_bar_and_name_box.

**Edit echo (edD, 187; fbE change, 2026-11-06).** While a cell is being edited (L4 >= 1 typed units, L5 = 0) the typed text is shown left-aligned in the active cell and in the formula bar. edD phases: 0 write UI_EDLEN (0x44) = L4; 1 write -1 to the cell's display-cache TAG (so its row is repainted after the entry ends); 3 read 0x44 and enter the heap copy at hc1 with T0 = HS (the units are already packed in the heap by ev_decode, kernel commit.md); 4 fill the cell interior; 5 aligned text, then fbA. fbE routes to edD phase 7 (copy again, then the formula box text) instead of fbF when editing. Echo is skipped for active rows below the visible 28 (e2 = [1000 L5 + r >= 28]). Limits: the echo is clipped to the active cell (Excel widens the edit box over neighbours); no caret. Tests: test_edit_echo.
