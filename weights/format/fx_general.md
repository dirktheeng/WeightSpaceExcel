# Weight block notes: General (ids 196, 197, 199)

Hand-written. Not generated. Log: log/format-agent.md "finisher and General"; decision F2.

**fx_gen (196, 1090 params).** After fx_dec. Wc = min(W, 11), W = 0 meaning 11. Fixed when it fits: e >= 0 needs s + e + 1 <= Wc, decimals Wc - s - e - 2 (0 at least); e < 0 uses decimals Wc - s - 2. For e < 0 scientific wins when it shows more digits: capS = ks + 1 > capF = Wc - s - 1 + e and m has more than capF significant digits (m not a multiple of 10^(15 - capF), tested with the exact residual of ROUND(m / D)); ks = Wc - s - 6, minus 1 when abs(e) >= 100 (3 exponent digits). A tie keeps fixed (0.00001 shows 0.00001). Saves m, e, ks, Wc in T5..T8 and calls fx_rnd with T9 = 197.
**fx_gen2 (197, 370 params).** A fixed result whose integer part grew past the width after rounding (99999999999.7) is redone in scientific (m restored from T5). Otherwise writes '-' for negatives, TP = 0xC900 (fixed) or 0xC910 (scientific), NC = 2, T3 = 2 exponent digits, clears T5 (SUB) and starts the emitter.
**fx_init (199, 120 params).** One block write of the two General records: '0', conditional point, ten '#' fraction digits (trailing zeros and the point vanish), and the same followed by E+ and two exponent digits. The token words are hand-computed biases (arg + 65536 code + 2^20 next code).

**Limits.** Width in characters, not pixels (Excel fits General by pixel width; open question). Tests: test_general (32 cases including widths 8, 6, 5, 3, 4, 7).
