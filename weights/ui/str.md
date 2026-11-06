# Weight block notes: weights/ui/str.wt (id 130, constant string ROM)

Hand-written. Log: log/ui-agent.md; decision U4.
**Computes.** Copies the string starting at ROM offset T0 into the buffer at P0, one unit per step including its 0 terminator, then returns to (LR, LP) with P0 at the terminator.
**ROM.** 15 x 16 table (v15). Row a holds offsets 16a..16a+15 as decimal UTF-16 units, so each line of the file reads as 16 consecutive characters. Lookup: a = floor(s/16) = ROUND(s/16 - 15/32), b = s - 16a; one-hot(b) times the table gives column b of every row; the mul with one-hot(a) and a sum pick the unit.
**Offsets.** 0 "Book1 - Excel", 14 "File", 19 "Home", 24 ribbon tab labels "Insert    Page Layout    Formulas    Data    Review    View    Help", 92 "fx", 95 "Sheet1", 102 "Ready", 108 "TRUE", 113 "FALSE", then error texts in ERROR.TYPE order: 119 #NULL!, 126 #DIV/0!, 134 #VALUE!, 142 #REF!, 148 #NAME?, 155 #NUM!, 161 #N/A, 166 #GETTING_DATA, 180 #SPILL!, 188 #CONNECT!, 198 #BLOCKED!, 208 #UNKNOWN!, 218 #FIELD!, 226 #CALC! (prod.wt holds the same offsets).
**Limits.** 240 units of capacity (233 used). **Parameters.** about 1,010. **Steps.** length + 1. **Multi-role weights.** None. **Tests.** test_str_rom.
