# Weight block notes: weights/ui/hd0, hd1, hd2 (ids 140..142, header labels), hx (185), hdD (186)

Hand-written. Log: log/ui-agent.md; decisions U1, U9 (highlight).
**Loop (140..142).** L12 = j and L13 = mode (0 = columns A..T, j 0..19; 1 = rows 1..28, j 0..27). hd0 produces the label (fcol, or fnum of j + 1). hd1 calls aligned text, centred, in #444444 on #EFEFEF (AC1): columns X = 31 + 64 j, Wb 63, top 180, clip min(93 + 64 j, 1279); rows X 0, Wb 30, top 201 + 20 j, clip 29. hd2 advances j and returns to (L22, L23) after row 28.
**hx (185).** Paints one header cell: job L14 = j + 1024 mode, return link L21 = id + 1024 phase. Highlighted when it is the active column (mode 0, j = L3) or row (mode 1, j = L2), as in Excel 2016: background #D2D2D2, label #217346, and a green line on the grid side (column: y 195 via fy; row: x 30 via fx). Phase 0 fill, 1 label (fcol or fnum), 2 aligned text.
**hdD (186).** Phases PC 32..38 (the scene enters with PC 32). Reads UI_HLDONE (0x42); if the active cell moved (L15, L16 from the outline versus L2, L3) or on the first frame, repaints old column and row normal and new ones highlighted, then continues to the edit echo (187).
**Derivation.** Unpacking by ROUND(x/1024 - (1/2 - 1/2048)). Phase gating by MUX_INT (M = 2^22, colours M = 2^25).
**Limits.** No scrolling. An off-screen active cell paints nothing visible (fills are clipped, glyph rows below y 799 are dropped).
**Parameters.** hd0 37, hd1 110, hd2 104, hx about 1,300, hdD about 650. **Steps.** 48 labels at boot about 1,000; a moved highlight about 4 x 40. **Tests.** test_headers, test_header_highlight.
