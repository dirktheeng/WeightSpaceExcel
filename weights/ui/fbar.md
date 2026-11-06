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
