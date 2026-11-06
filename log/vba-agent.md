# VBA agent log (weights/vba, ids 384 to 447, encodings/vba.md)

## 2026-11-06, Stage 9 groundwork: reading
- Read docs/AGENT_BRIEF.md, GOAL.md, docs/RULES.md, docs/DOCUMENTATION.md, docs/HARNESS.md, harness/FORMAT.md (block ops v2), encodings/value.md, control.md, memory-map.md (sections 10 and 13), primitives.md, weights/prim/CONVENTIONS.md, idivmod.md, div.md, weights/parse/README.md, idle.md, numconv.md, weights/eval/evaluator.md, format.md, ev_div.md, tests/output/blackbox.py, tests/output/parse/test_parse.py, the tail of log/WORKLOG.md.
- Reusable from others (by call, never by copying weights): parse numconv (id 75; M, SIG, FRAC, DROP, EXPV, ESGN in words 56..61, returns to (X6, X7) = words 62, 63 with the double in word 54; k > 22 continues in numbig 123 with the same return); eval ev_totext (id 110; A = number, HT = Excel heap top in word 23, returns A = (2, packed handle) to (LR, LP)).
- Not reusable: ev_div (103) and ev_cat (113) end by routing to the evaluator's dispatcher, not to LR. VBA division is therefore my own loop network (bit-serial long division with guard and sticky bits); see decision VB4.
- Plan, in order: encodings/vba.md; interpreter core tested on hand-assembled bytecode; lexer; parser (expressions, then statements, then blocks).

## 2026-11-06, interpreter core (ids 420..446)
- Wrote encodings/vba.md (layout, Variant tags = 16 + VarType with Empty on tag 0, tokens, keyword keys, frames, bytecode).
- Keyword keys computed by hand by Horner's rule (x 64 + letter value), each product re-derived by splitting (for example 223,113,359 x 64 = 223,000,000 x 64 + 113,359 x 64). Function was computed twice (powers of 64 and Horner) and both gave 27846476075982.
- vi_start, vi_fetch, vi_disp, vi_halt first; PUSH and END ran. First bug: vi_disp has a 2-word payload, and on END (mem_op 0) the harness forwards the whole 66-word output, so vi_halt got 67 inputs. Rule adopted for every network with a payload: every step uses a block op (block read of 0 words where nothing is needed). Fixed vi_disp's mem_op and value rows for END, HOOK, BAD.
- vi_load, vi_store (coercion table), vi_jz: hand-assembled programs ran correctly (2.5 -> Integer 2, 3.5 -> Long 4, banker's rounding; 40000 -> Integer gives ERR 6; a string into Integer ERR 13; Empty into String gives VSTR_EMPTY).
- vi_bin: integer, long, double + - *, overflow 6 (30000 + 30000 Integer), Long widening, 0.1 + 0.2 = 0.30000000000000004, comparisons, And/Or/Xor/Eqv/Imp on True/False, NEG, NOT (Not 5 = -6, Not 2.5 = -3 as Long), ^ -> 5, Is -> 424, Integer + String -> 13. Bug found: 1e308 + 1e308 gave NaN: the logic candidates relu(ra + rb + 1) overflowed to inf before the gating mul. Fix: the logic rows work on values scaled by 2^-12 and the result row multiplies them back by 4096 (exact powers of two); the gated product is then finite. After the fix 1e308 + 1e308 and 1e200 * 1e200 give ERR 6.
- vi_call, vi_zero, vi_ret, vi_for: a For i = 1 To 3: s = s + i loop in a called procedure gives s = 6, i = 4 (165 steps). One test-program bug on my side (wrong JZ target), no weight bug.
- Output: vo_main, vo_num, vu_wr, vu_rd, vo_tail, vo_slen, vs_rd, vs_wr. Debug.Print 5 -> " 5 ", -3 -> "-3 ", True, False, 1/3 -> " 0.333333333333333 ", MsgBox 1E15 -> "1E+15", 40-char string copy. Bug: vo_main set SRC = vP + 1 for numbers too, and vu_wr's MUX_INT on SRC then broke (|SRC - h| > 2^23 with SRC = 1e15 + 1). Fix: SRC = (isStr vP) + 1 from the gated product.
- Unpack exit made a register (UXIT, word 62) so the CStr path can reuse vu_wr / vu_rd: vo_num sets 438, vc_cstr sets 445.
- vc_cstr, vc_cnum, vc_fin, vi_cat: "x = " & 5, True & "abc", "x = " + "abc", 2.5 & -7, Empty & "x = " all correct. Bug: vi_cat's LR bias sat in the LP column (index 9 instead of 8); fixed.

## 2026-11-06, memory relocation (coordinator: FILE_SCRATCH took 0x3B0000..0x3BFFFF, decision F2)
- VBA now fits in 0x380000..0x3AFFFF: VSTR 0x399000..0x39BFFF, DEBUG_OUT 0x39C000, MSG_OUT 0x39E000, VSTACK 0x3A0000..0x3A7FFF, OBJT 0x3A8000..0x3AFFFF. Edited vi_start (DOUT, MOUT biases) and vi_halt (length offsets) by hand; encodings/vba.md updated. Rerun of the "x = " & 5 / MsgBox program correct. Room is enough for the groundwork.

## 2026-11-06, rule slip (discarded)
- While starting vl_kw I used a shell `seq` loop to print the 110 unit weight rows of the keyword compare layer into a scratch file in /tmp. That is a pattern expander (RULES.md rule 2). Deleted unused; nothing reached weights/. The rows are typed by hand.

## 2026-11-06, lexer (ids 384..399)
- Protocol chosen: state networks are block consumers of the current char and emit tokens by block write, re-reading through vl_read (decision VB6 forced it: a single read cannot share a step with a payload).
- vl_idle: first load failed (30 instead of 29 rows in the final dense, an extra zero row); fixed. Punctuation, comments, continuation correct on the first run after vl_cmt's I and addr rows were fixed (signs of the stop term reversed).
- vl_word, vl_kw, vl_preg: keyword constants KL = KEY + 2^48 len summed by hand (every sum re-added digit by digit). First run all keywords, operator words, True, Rem and procedure registration correct.
- vl_num, vl_nend: first run gave 5 -> 1 and failures on multi-digit numbers: the M..ESGN and NDBL..NSUF rows of the final dense were one column to the left (reading c instead of M). Shifted by hand; all 13 number forms then correct, including 15-digit truncation.
- vl_str, vl_strq, vl_semit, vl_op2: two dense layers had a wrong column count for a constant row (3 vs 5, 1 vs 2); fixed. Strings with "" and empty strings, all six comparison operators correct.
- vl_date, vl_dser: three rows of vl_date wrong on review before running (next, value, address); fixed by hand; serials 36527, 36525, 2, 61, 45351 correct first run.
- Tests: tests/output/vba/test_vba.py, 49 passed (lexer from VBA source; interpreter from hand-assembled bytecode).

## 2026-11-06, status at hand-off
- Done: encodings/vba.md; lexer; interpreter core with frames, calls, For, Print, MsgBox, CStr, &.
- Not done: parser (ids 400..419, design in encodings/vba.md section 6); vi_div (/ \ Mod), vi_scmp (string comparison), ^, Like, bitwise And/Or on general integers, On Error.
