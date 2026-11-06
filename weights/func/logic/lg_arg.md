# Weight block note: lg_arg (id 300)

Hand-written. Not generated. Log: log/func-logic-agent.md. Uses block operations (harness/FORMAT.md, v2).

**Computes.** ABI entry for AND, OR, XOR, IF, IFERROR, IFNA, IFS, SWITCH, and the argument fetch loop. Output is 66 words; every phase is a block operation with K = 64, so successors see the usual 65-word state (plus the 2 read words for the consumer).

| PC | Memory | Effect | Next |
|---|---|---|---|
| 0 | block write [SP, SP + 1] = B | N1 = 1, C = (0, 0), T3 = T4 = T5 = 0 | 300 PC 1 |
| 1 | block read 2 words at SP - 2 (N0 - N1) | | 302 if T2 in 282..285 or 513, else 301 (PC 0) |
| 2 | block write [SP - 2 (N0 - N1), +1] = A | T5 = 1 | 300 PC 1 |

**Blocks.** v4 to v6 phase one-hot and family bit fSel = [T2 >= 282] - [T2 >= 286] + [T2 >= 513] - [T2 >= 514]. v15, v16 MUX_INT (M = 2^20) for (ph1 + ph2)(2 N1 - 2 N0) and the keep-or-zero registers. v25 to v28 one mul choosing the payload (B at PC 0, A at PC 2) and C (zeroed at PC 0). value = 64 * 2^20 + 2 = 67108866.

**Why write B to memory.** It makes all n arguments uniform, so one fetch step and one consumer serve every argument. The two words are above the stack top; FN_RET discards them (functions.md section 6).

**Limits.** PC outside 0..2 is not trapped. **Parameters.** 350. **Tests.** test_abi_fold.py, test_abi_sel.py.
