# Weight block notes: interpreter core (ids 420..426, 428, 429, 431, 435, 446)

Hand-written. Not generated. Registers, bytecode and frames: encodings/vba.md sections 5 and 7. Log: log/vba-agent.md "interpreter core"; decisions VB3, VB4, VB6.

| Id | File | Computes | Steps |
|---|---|---|---|
| 420 | vi_start | IP = 0x390000, SP = FP = 0x3A0000, DOUT, MOUT, ERR = 0; fetch | 1 |
| 421 | vi_fetch | block read [OP, ARG] at IP | 1 |
| 422 | vi_disp | 16 thresholds on OP give 14 classes; each class's first memory op, next id, IP and SP updates are linear in the class one-hot; address terms that involve ARG, SP, FP, IP are products from one mul layer (gates gA = JMP + 2 LOAD + 4 CALL, gS, gF, gI), so a PUSH of any double never meets a relu (no MUX_INT on ARG). PUSH writes its payload [OP - 64, ARG] directly | 1 |
| 423 | vi_halt | block write [DEBUG_LEN, MSG_LEN, ERRNUM] at VGLOB, halt | 1 |
| 424 | vi_load | slot value -> stack | 1 |
| 425 | vi_store | vt = ROUND(ARG 2^-12) (exact while slot < 2048); class thresholds on the value tag and on vt; Integer/Long/Byte by ROUND (half even, magic constant) with range check, Boolean as -[x != 0], String keeps strings, Empty -> VSTR_EMPTY | 1 |
| 426 | vi_jz | truth = [PAY != 0] by two steps; jump flag 1 - t - isJNZ + 2 AND(t, isJNZ); IP MUX_INT; fetches the next instruction itself | 1 |
| 428 | vi_call | FPn = SP - 2 (np + 1), link [IP + 2, FP] at FPn - 2, IP = entry | 1 |
| 435 | vi_zero | zeroes locals 8 words per step, then fetches | ceil(locals / 4) + 1 |
| 429 | vi_ret | slot 0 moves to FP - 2, FP and IP restored | 1 |
| 431 | vi_for | cond = (step >= 0 and i <= limit) or (step < 0 and i >= limit) | 1 |
| 446 | vi_obj | object model hook: ERR 438 | 1 |

Typical cost: 3 steps per instruction (fetch, dispatch, handler), 2 for JMP and POP. Parameters (all written, zeros included): vi_disp about 700, vi_store about 1000, the rest under 200 each.
**Limits.** Slots < 2048 per procedure; By-value parameters only; no Variant overflow widening; string to number coercion raises 13; For operands are not type checked. **Multi-role weights.** vi_disp's address row serves every class (exclusive one-hot gates). vi_store's PAY row sums three gated products, at most one nonzero. **Tests.** test_store_coercion, test_errors, test_for_loop_in_called_proc, test_function_call_returns_value.
