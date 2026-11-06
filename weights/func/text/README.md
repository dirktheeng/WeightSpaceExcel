# weights/func/text: Text function cores (ids 312 to 343)

Hand-written. Not generated. Log: log/func-text-agent.md; decisions T1 to T4 in log/WORKLOG.md ("2026-11-06, Stage 3: Text function cores").

The seven cores (312 to 318) were written before encodings/functions.md existed, so each is a **core subroutine** with explicit register inputs and outputs, called with the encodings/control.md convention (LR, LP set by the caller; the last step returns to (LR, LP) with the result in A). The ABI layer (tx_abi.md) wraps them and the later drivers. Tests: tests/output/func_text/test_func_text.py (cores) and test_text_abi.py (ABI level and drivers).

| Id | File | Function(s) | Note |
|---|---|---|---|
| 312 | tx_len.wt | LEN core | tx_len.md |
| 313 | tx_code.wt | CODE (Windows-1252) / UNICODE (surrogate pairs) core | tx_code.md |
| 314 | tx_case.wt | UPPER / LOWER core | tx_case.md |
| 315 | tx_exact.wt | EXACT core | tx_exact.md |
| 316 | tx_mid.wt | MID core (LEFT, RIGHT) | tx_mid.md |
| 317 | tx_char.wt | CHAR / UNICHAR core | tx_char.md |
| 318 | tx_t.wt | T core | tx_t.md |
| 319 to 323 | tx_w0, tx_av, tx_ld, tx_fin, tx_rgt | ABI entry, argument conversion, loader, return, RIGHT start | tx_abi.md |
| 324 to 329 | tx_cp, tx_cpf, tx_f1, tx_cc, tx_rp, tx_rl | unit copier and CLEAN, TRIM, PROPER, CONCAT(ENATE), TEXTJOIN, REPT, REPLACE | tx_cp.md |
| 330 to 334, 339 to 343 | tx_unp, tx_unw, tx_fs, tx_fm, tx_sb, tx_bc, tx_bw, tx_pk, tx_pkw, tx_sl | unpacking, FIND / SEARCH matcher, SUBSTITUTE | tx_match.md |
| 335 to 338 | tx_val, tx_tx, tx_tx2, tx_tx3 | VALUE, TEXT (format engine) | tx_abi.md |

Every id from 312 to 343 is used. 32 networks, 32,250 dense parameters (zeros included, counted from the layer headers). FUNC_TABLE: every Text fid listed in tx_abi.md maps to 319.



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
