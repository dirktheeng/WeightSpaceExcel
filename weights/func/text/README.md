# weights/func/text: Text function cores (ids 312 to 343)

Hand-written. Not generated. Log: log/func-text-agent.md; decisions T1 to T4 in log/WORKLOG.md ("2026-11-06, Stage 3: Text function cores").

encodings/functions.md (the function ABI) did not exist when these were written, so each network is a **core subroutine** with explicit register inputs and outputs, called with the encodings/control.md convention (LR, LP set by the caller; the last step returns to (LR, LP) with the result in A). ABI wrappers (argument fetch, coercion, FUNC_TABLE entry) are to be added once the ABI exists; until then nothing routes here and the cores are tested directly (tests/output/func_text/test_func_text.py).

| Id | File | Function(s) | Inputs | Steps | Params |
|---|---|---|---|---|---|
| 312 | tx_len.wt | LEN | A | 2 | 208 |
| 313 | tx_code.wt | CODE, UNICODE (first unit) | A | 3 | 302 |
| 314 | tx_case.wt | UPPER (N0 = 0), LOWER (N0 = 1) | A, N0 | 3 + 2 ceil(L/3) | 1547 |
| 315 | tx_exact.wt | EXACT | A, B | 3 + 2 ceil(L/3) when lengths match, else 3 | 1311 |
| 316 | tx_mid.wt | MID, and LEFT / RIGHT through wrappers | A, B (start), C (count) | 4 + 2 ceil(n/3) | 2808 |
| 317 | tx_char.wt | CHAR (N0 = 0), UNICHAR (N0 = 1) | A, N0 | 1 (one block write) | 758 |
| 318 | tx_t.wt | T | A | 1 | 111 |

Parameter counts are dense weights plus biases, zeros included, counted by hand from the layer shapes. Ids 319 to 343 are free for the remaining Text functions and the wrappers.

## Shared conventions (all cores)

- **Registers read**: x0, PC (7), LR (8), LP (9), A (13, 14), B (15, 16), C (17, 18), HT (23), N0 (27) as mode, plus the loop registers each note lists. **Clobbered**: P0, P1, N1, T1 to T4 as listed per note. Everything else, including L0 to L23, passes through (slices), so the cores never spill.
- **HT = word 23** is the text heap top, the register the evaluator keeps during recalculation (weights/eval/README.md; ev_cat uses the same word). Cores that build a string allocate at HT and return HT advanced past it; they never touch HEAP_TOP in the zero page.
- **Arguments are already coerced**: a core expects text (tag 2) or an error (tag 4) where a string is wanted, and a number (tag 1) or an error where a number is wanted. Turning numbers, booleans and blanks into text (LEN(123) = 3) or text into numbers is the wrapper's job (ev_totext id 110 and ev_t2n id 109 exist for that). An error argument is returned unchanged, first error in argument order.
- **New strings**: length word written, packed words written; the reference count word is written as 1 only by tx_char (block write). The looping cores leave it as fresh memory (0), as the parser does for literals; reclaiming is open question Q-M2.
- **Phase decoding**: thermometer bits q_k = step(PC - k + 0.5); phase indicators are their differences, used linearly. Routing and register updates use MUX_INT (relu(v - M (1 - g)), M = 2^23 for addresses, ids, phases and lengths) and the mul layer for doubles or for values that can be large garbage in phases where they are not used (packed words, read results). This keeps V1: every gated value is finite.
- **UNPACK3** (encodings/primitives.md) is two FLOOR(x 2^-16) stages with the D5 rounding constant C = 1.5 2^52.

## Multi-role words

- A.PAY holds a handle on entry and the result (number, handle, boolean or error code) on return; the role changes only at the return step, selected by the outcome gates, so no step reads it in two roles.
- N0 is a mode selector in tx_case and tx_char only.
- T1 holds a length in one phase and a packed word in another (tx_exact, tx_mid); each phase writes it before the next phase reads it, and the phase gates are exclusive.
