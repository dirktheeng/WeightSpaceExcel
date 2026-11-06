# Weight block note: fm_unary (id 264)

Hand-written. Not generated. Log: log/func-math-agent.md (2026-11-06 entries). Blocks retyped from weights/prim/floor_round.wt (ROUND by C = 1.5 * 2^52, FLOOR = r - step(r - u)) and the ONEHOT / MUX patterns of encodings/primitives.md.

**Computes.** One step, one forward pass (55 values). Selector T0 (word 29): 0 ABS, 1 SIGN, 2 INT, 3 TRUNC with one argument, 4 PI, 5 EVEN, 6 ODD, 7 DEGREES, 8 RADIANS. Argument A (words 13, 14, encodings/value.md). Result in A; next = LR, PC = LP, STATUS = 0; words 8 to 11 and 15 to 63 pass through. Clobbers only A, STATUS, words 0 to 7.

**Interim contract.** encodings/functions.md did not exist when this was written; this is a computational core to be wrapped (or called) by the ABI dispatch. Selector values are local to this network.

**Blocks (value numbers as in the .wt comments).**
- v3..v8: tag thermometer s_k = [tag >= k], k = 1..5, and selector thermometer t_k = [sel >= k], k = 1..8 (GE_K banks, R4 exact).
- v9, v10: isnum = 1 - s2 + s3 - s4 (tags 0, 1, 3); x = isnum * PAY by a mul (0 or PAY exactly; a text handle never reaches arithmetic).
- v11..v17: p = relu(x), n = relu(-x), sp, sn = signs; b = [|x| > 2^51] (every such double is an integer; the ROUND constant needs |u| < 2^51); ok = [|x| < 1e306] so DEGREES cannot overflow (57.3 * 1e306 < MAXD).
- v19, v20: gated inputs xs = (1 - b) x, hxs = (1 - b) |x| / 2, hx1s = (1 - b)(|x| / 2 + 1/2), xg = ok x, bx = b x. Each gate product is 0 or the value exactly; |x| / 2 is exact; + 1/2 is one correctly rounded add.
- v21..v27: four parallel FLOORs of u = [xs, -xs, -hxs, -hx1s]: r = (u + C) - C, g = [r > u], F = r - g. F1 = FLOOR(x), -F2 = CEIL(x), -F3 = CEIL(|x|/2), -F4 = CEIL((|x|+1)/2).
- v30, v31: sign corrections by mul with sn: T = CEIL(x) - FLOOR(x), E = 2 CEIL(|x|/2), O' = 2 CEIL((|x|+1)/2) - 1 + b. Note O' = 0 when b = 1 (all r, g are 0), so the big path is clean.
- v33 candidates: ABS = p + n; SIGN = sp - sn; INT = F1 + bx; TRUNC = F1 + sn T + bx; PI = 3.141592653589793 (bias, the double nearest pi); EVEN = E - 2 sn E + bx; ODD = O' - 2 sn O' + bx (gives ODD(0) = 1); DEGREES = 57.29577951308232 xg; RADIANS = 0.017453292519943295 x (the doubles nearest 180/pi and pi/180). Every integer row is exact by R4 (integers below 2^52); in every real row at most one term is nonzero, so it is exact (R1).
- v34..v37: 9-way one-hot of sel (ind0 = 1 - t1, ind_j = t_j - t_j+1, ind8 = t8), mul with candidates, one sum row with one nonzero term (exact).
- v39, v40: E = iserr and not PI (iserr = s4 - s5), V = non-coercible tag and not PI (isval = s2 - s3 + s5), D = DEGREES and not ok.
- v43..v46: TAG = E tag - E + 3V + 3D + 1, PAY = E pay + 3V + 6D + N val with N = 1 - E - V - D. Error passes unchanged; #VALUE! = (4, 3); #NUM! = (4, 6).
- v47..v55: return fields and pass-through by slice and concat.

**Parameters.** 967 dense weights and biases (zeros included). Steps: 1.

**Limits.** Text arguments give #VALUE! (Excel coerces "3" to 3 for a direct text argument; coercion belongs to the ABI layer, which can call ev_t2n). For 2^51 < |x| < 2^53, EVEN and ODD return x unchanged (true for EVEN of an even integer; ODD of an even integer in that range is off by one; Excel's EVEN/ODD there is untested). DEGREES is x times fl(180/pi), one rounding instead of Excel's two (x * 180 / pi), so it can differ from Excel in the last bit (15-digit tests pass). Reference and array arguments are not handled here (ABI layer). A result may be negative zero (for example TRUNC(-0.5)); it compares equal to 0 and is tested as 0, but display of -0 by the formatter is unchecked.

**Multi-role weights.** None beyond the shared selector one-hot, whose 9 outputs gate disjoint candidates (exclusive gating).

**Tests.** tests/output/func_math/test_func_math.py, test_unary: 52 cases, all pass.
