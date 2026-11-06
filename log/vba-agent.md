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

## 2026-11-06, coordinator follow-up (parser, division, the rest of scope)
- Coordinator fixed numconv's gate (2^20, decision C2) and asked for the parser, an LR-returning hand copy of the prim div block, and the remaining language features.
- Not started in this session: the working context of this agent is nearly used up, and a half-typed network would leave a broken manifest. Hand-off plan for the next session, in order:
  1. Parser ids 400..419 per encodings/vba.md section 6: ps_start (prologue PUSH E, PUSH E, CALL 0, END at BC), ps_tok (block read 2 of the next token, consumer pattern as the lexer), ps_stmt (dispatch on the first token K), ps_expr (shunting-yard, operator stack OSTK with cached top, precedence from token V, unary minus 40 / Not 41 pushed without popping), ps_sym (linear scan of SYMT, then PROCT; implicit Variant slot), ps_patch (jump chain walk), ps_blk (CSTK push/pop for If/For/Do/While/Select/Sub). Bytecode emission one block write of 2 words per instruction.
  2. vi_div (434): retype weights/prim/div.wt block v1..v338 by hand with a new tail returning through vi_bin's result write; \ and Mod as ROUND of operands, quotient trunc, exact remainder correction (cite weights/prim/div.md, idivmod.md).
  3. vi_scmp (433): length, then unit loop by block reads of 8; Option Compare Binary.
  4. Then ^, Like, bitwise And/Or (bit extraction stages), On Error, ByRef, arrays, &H/&O and type suffixes.

## 2026-11-06, parser (ids 400..419), session 3
- Read the brief (with Updates), encodings/vba.md, weights/vba notes and this log. Plan item 1 (parser) done; items 2..4 not started (context budget).
- Design change (VB10): all parser stacks and tables live in registers. Reason: a pop from a memory stack needs a read after the emit write (two memory ops), and a symbol scan in memory is a loop; in registers both are one mul layer. State width 136 (K = 136 in block ops; the harness allows K up to the output length), words 7..63 passed through so VHT, XHT, CHAIN reach vi_start. Every state network reads 3 tokens at TP (VB11), so known tokens (`=` after a target, `.Print`, `As T`) are skipped by TP arithmetic.
- Equality of 2^48-scale keys by triangles relu(d+1) - 2 relu(d) + relu(d-1) on the exact difference (VB12); ANDs of 0/1 flags by relu(a + b - 1); gated values by mul layers.
- Typed Dim emits PUSH Empty + STORE with the type, so vi_store's coercion makes the initial value (Empty -> 0, "" ) (VB13).
- Order of work: ps_read, ps_start, ps_pk, ps_stmt, ps_skip, ps_fin (ran "Option Explicit" through to the interpreter first time), ps_sym, ps_expr, ps_xid, ps_xend, ps_sid, ps_dim, ps_for, ps_next, ps_else, ps_end, ps_pend, ps_endif, ps_patch, ps_dimc.
- Bugs: ps_xid header said 17 rows for 18 typed (caught by the loader). ps_xend referenced layer 25 where the numbering had 24 (one concat fewer than planned): fixed by an identity spacer layer. ps_expr never set SN, so an identifier inside an expression returned to the statement network: added an SN = 418 row by hand (Edit tool). Debug script substitution table had wrong ids for 415..419 (script only).
- Another agent's weights/func/text/tx_sl.wt failed to load for a while (in progress); my scratch debug runner substitutes unloadable files; the tests use the real manifest and passed.
- Results: 6 end-to-end tests from VBA source (precedence, Dim types with ',' lists, For/Next with Step and Step -1, nested For and If, If/Else/End If, unary minus, Not, Function value via its own name, Sub calls by Call and bare name before definition, MsgBox with &, Integer overflow ERR 6, bare Debug.Print, trailing ';'). 55 tests pass in tests/output/vba/test_vba.py.

## 2026-11-06, hand-off plan (next session)
1. vi_div (434): unchanged plan (retype weights/prim/div.wt block, LR tail into vi_bin's result write; \ and Mod). The parser already emits 19, 20, 21 (they trap with ERR 5 today, e.g. `4 / 2 ^ 2`).
2. vi_scmp (433) unchanged.
3. Parser extensions, each a separate network routed by next: parameters and arguments (ps_sym marks parameters at Sub header; call marker on OSTK with argument count; ps_xend ',' at depth of a call), ElseIf / single-line If (ps_xend CTX 4 with K1 != EOS), Do/Loop/While/Wend (block kind 3, 4 already in the encoding), Exit For/Sub (chains in block word c), print zones for ','. Then the item-4 language features (^ at run time, Like, Is, bitwise And/Or, On Error, ByRef, arrays, &H/&O, type suffixes).
4. Test hint: the lexer test helper and run_src are in tests/output/vba/vbabb.py; /tmp scratch runner is not kept.
