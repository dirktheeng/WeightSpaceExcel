# Weight block notes: weights/kernel/ret.wt (id 2, RET trampoline)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decision K1. Spec: encodings/control.md section 4 ("Return through the stack").

**Computes.** Input word 0 holds LINK = LR 2^16 + LP, read from RET_STACK by the caller's pop step (the caller has already decremented RSP and checked underflow). Output next = floor(LINK / 2^16), PC = LINK - 2^16 next, mem_op none, everything from word 8 on copied unchanged.

**Derivation.** v2: R1 row with weight 2^-16 = 0.0000152587890625 (exact power-of-two scale) plus bias C = 1.5 2^52 (ROUND, decision D5, weights/poc/round_floor.md); v3 subtracts C, giving r = round(LINK 2^-16), ties to even. v5 = 65536 r - LINK is an integer row (R4, exact), positive exactly when rounding went up; v6 = step gives g. v8 row next = r - g (FLOOR), row PC = LINK - 65536 r + 65536 g. All integers below 2^32, exact.

**Parameters.** 39. Steps: 1. Clobber set: words 0..7.

**Limits.** LINK must be a non-negative integer below 2^51 (ids and phases below 2^16 by control.md). **Multi-role weights.** None.

**Tests.** tests/output/kernel/test_kernel.py::test_ret_unpacks_link (LP 0, 7, 65535).
