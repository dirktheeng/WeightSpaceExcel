# Weight block notes: weights/ui/scene.wt (id 152), redraw.wt (id 153)

Hand-written. Log: log/ui-agent.md; decisions U1 (layout, colours), U2.
**scene.** PC selects one ROM command per step (one-hot by pt_m qt_(m) products). The ROM is a dense 17 x 34 block, one row per argument field, with entries as columns. LP, N1 and L23 are PC + 1 (linear), and LR and L22 are 152, so every callee returns to the next entry. Entries: 0..13 chrome rectangles, 14..27 seven constant texts (str then aligned text), 28 headers, 29 cells, 30 outline, 31 formula bar, 32 io 1 (present), 33 next 4 (main_poll), MODE 1. Every step also sets L12 = L13 = 0 and L17/L18 = 150/151 for the subroutines.
**Layout table (U1).**
| Entry | Rect (x0..x1, y0..y1) | Colour |
|---|---|---|
| 0 | 0..1279, 0..54 title bar and tab strip | #217346 |
| 1 | 46..99, 31..54 selected Home tab | #F3F3F3 |
| 2 | 0..1279, 55..146 ribbon body | #F3F3F3 |
| 3 | 0..1279, 147 ribbon border | #D4D4D4 |
| 4 | 0..1279, 148..175 formula band | #FFFFFF |
| 5, 6 | 3..104 / 160..1276, 151..172 name box and formula box borders | #C6C6C6 |
| 7 | 0..1279, 176..195 column header (pattern, separators) | #EFEFEF / #D4D4D4 |
| 8 | 0..30, 196..755 row header (pattern) | #EFEFEF / #D4D4D4 |
| 9 | 31..1279, 196..755 grid (pattern) | #FFFFFF / #E1E1E1 |
| 10, 11 | tab bar line y 756; bar and status bar 757..799 | #D4D4D4, #F3F3F3 |
| 12, 13 | Sheet1 tab 60..129, 757..777 and underline 776..777 | white, #217346 |
Texts: title centred white at top 10; "File" X 14; "Home" centred in 46..99 in green; other tabs from X 112; "fx" X 136 top 156 (#444444); "Sheet1" centred in 60..129 top 761 green; "Ready" X 8 top 783.
**redraw (153).** One step: MODE 4, enter scene at PC 29.
**Parameters.** scene about 1,500 (578 of them the ROM); redraw 14. **Steps.** Full frame 1.10 to 1.11 million (chrome about 1.02M); incremental frame about 30,000. **Tests.** test_chrome_colours and every frame test.

**Changes 2026-11-06 (block ops).** Entry 8 is gband (174) for the whole grid (28 steps); entry 9 is a 1-pixel no-op fill. Entry 29 is the scan gate (176), entry 31 the header highlight dispatcher (186, then edit echo 187, then the name box and formula bar). A new output row sets AC1 (text background for glyph v2) from the entry one-hot. Steps: boot frame about 2,750 on an empty sheet (was 1.1 million), 0.33 s wall untraced.
