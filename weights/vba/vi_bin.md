# Weight block note: vi_bin (id 427)

Hand-written. Not generated. Log: log/vba-agent.md "interpreter core"; decision VB4. Opcodes: encodings/vba.md section 7; tags section 3.

**Computes.** Block consumer of a (65, 66) and b (67, 68). 23 thresholds on OP give op classes; 12 thresholds per operand tag give Empty/Boolean/Integer/Long/Double/String classes (Byte with Integer, Single and Date with Double). Ranks: RD = OR(aD, bD), RL = AND(OR(aL, bL), not RD). For unary NEG and NOT the a operand is forced to rank Integer and Boolean (aNe, aDe, aLe, aBe), so only b counts.
**Arithmetic.** s = a + b and d = a - b are two-term unit rows on inputs gated to 0 when the halves test overflows (|0.5 a +- 0.5 b| >= 2^1023); p = (nM a) b with nM = [|a 2^-512 b 2^-512| < 1]. The constants 2^-512 and 2^1023 are built inside the pass by squaring the exact literals 2^-64 and 2^64 (no long decimal literal trusted). Integer and Long results are range-checked (ERR 6).
**Comparisons.** gt = step(a - b), lt = step(b - a) in their own layer (an infinite difference only meets a step, V1). Result Boolean -1/0.
**Logic.** ra, rb = ROUND(a), ROUND(b); And = max, Or = min, Xor = min - max, Eqv = max - min - 1, Imp = min(-ra - 1, rb), Not = -rb - 1: exact for 0 and -1 (Booleans), wrong for other integers (limit). The candidates are formed scaled by 2^-12 and the result row multiplies by 4096, so huge Double operands stay finite before the gating mul (bug found with 1e308 + 1e308, log).
**Result.** 11 candidates times 11 op gates in one mul layer, summed; tag from MUX_INT rows (18 + RL + 3 RD for arithmetic, Boolean 27 for comparisons, Boolean or Integer/Long for logic).
**Routes.** & and string + -> vi_cat 432; string comparisons -> vi_scmp 433; / \ Mod ^ -> vi_div 434. Errors: Like 5, Is 424, bad opcode 51, mismatch 13.
**Parameters** about 9,000 (mostly zeros of the 50- and 71-wide rows). **Multi-role weights.** Words 13..16 carry a and b for routed ops only; they are caller-saved. **Tests.** test_binary, test_unary, test_errors.
