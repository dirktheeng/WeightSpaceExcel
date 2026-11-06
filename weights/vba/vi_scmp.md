# Weight block notes: vi_scmp (id 433), vi_scl (id 447)

Hand-written. Not generated. Log: log/vba-agent.md "vi_scmp". VSTR records: encodings/vba.md section 2.

**Computes.** `=  <>  <  <=  >  >=` (OP 24..29) when vi_bin (427) sees a string operand; a = words 13, 14, b = 15, 16. Option Compare Binary: UTF-16 units compared as integers, first difference decides, a proper prefix is smaller.
- **vi_scmp (433), entry, one step.** Tag triangles: String (24) or Empty (0) on both sides, else ERR 13 -> vi_halt. Handles: PAY + 3772416 [Empty] (Empty's PAY is 0, so Empty becomes VSTR_EMPTY 0x399000, length 0). HA (49), HB (50), LA = LB = 0 (51, 52), PH = 0 (53), FIRST = 1 (63); block read 9 at HA -> vi_scl.
- **vi_scl (447), loop, input 74 = state + 9 block words.** Every read is 9 words at HA or HB, so word 0 is the record length on the first read and the unit before the chunk later; words 1..8 are the next 8 units.
  - PH 0: LA = b0 if FIRST (gated product gA (b0 - LA)); A0..A7 (words 54..61) = b1..b8; read 9 at HB; PH = 1.
  - PH 1: LB likewise. For i = 0..7: va = [i < LA], vb = [i < LB], gt, lt on A_i - B_i (integers, thresholds at +-0.5). both = va AND vb; dgt, dlt = both AND gt/lt; endB = va AND NOT vb; endA = NOT va AND vb. stop_i = 1 - both + dgt + dlt; the first stop is f_i = step(stop_i - sum_{j<i} stop_j - 0.5) (one linear layer). plus = f AND (dgt or endB), minus = f AND (dlt or endA). any = sum f, pl = sum plus, mi = sum minus; truth by op: = any - pl - mi, <> pl + mi, < mi, <= any - pl, > pl, >= any - mi (each ANDed with the op one-hot by a step).
  - Done (PH 1 and any): block write [27, -truth] (Boolean) at SP - 4, SP -= 2, IP += 2, next vi_fetch 421. Otherwise HA, HB += 8, LA, LB -= 8, read 9 at HA, PH = 0.
- Data muxes (A_i, addresses) are mul-gated, so garbage in the other phase never meets a relu.

**Cost.** 1 + 2 ceil((common prefix + 1) / 8) steps, then fetch. Parameters: vi_scmp about 110, vi_scl about 5,200 (mostly zeros of the 26 x 65 output layer and the 32 x 28 and 40 x 32 compare layers).
**Limits.** Option Compare Text is not done. A string compared with a number is ERR 13 even when the string is numeric (VBA converts "5" = 5 to a numeric comparison); Null operands are not handled.
**Multi-role weights.** Words 49..63 are loop registers only inside the comparison. **Tests.** test_src_string_compare (9 pairs x 6 operators), test_src_string_compare_empty_and_mismatch.
