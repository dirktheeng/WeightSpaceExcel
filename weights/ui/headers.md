# Weight block notes: weights/ui/hd0, hd1, hd2 (ids 140..142, header labels)

Hand-written. Log: log/ui-agent.md; decision U1.
**Loop.** L12 = j and L13 = mode (0 = columns A..T, j 0..19; 1 = rows 1..28, j 0..27). hd0 produces the label (fcol, or fnum of j + 1). hd1 calls aligned text, centred, in #444444: columns get X = 31 + 64 j, Wb 63, top 180, clip min(93 + 64 j, 1279); rows get X 0, Wb 30, top 201 + 20 j, clip 29. hd2 advances j, switches mode after column T, and returns to (L22, L23) after row 28.
**Derivation.** a = step(j - 18.5 - 100 mode) marks the last column only in mode 0; b = step(j + mode - 27.5) marks the last row only in mode 1. MUX_INT M = 2^20.
**Limits.** No scrolling: the top-left visible cell is fixed at A1. The active row and column headers are not highlighted. **Parameters.** hd0 37, hd1 98, hd2 104. **Steps.** about 6,400 for all 48 labels. **Tests.** test_headers.
