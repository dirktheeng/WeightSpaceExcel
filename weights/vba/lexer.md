# Weight block notes: VBA lexer (ids 384..399)

Hand-written. Not generated. Tokens and keyword table: encodings/vba.md section 4. Log: log/vba-agent.md; decisions VB1, VB5.

**Protocol.** Every state network is a block consumer of the current char c (input 65) and outputs 66 words: either it consumes c and block-reads char I + 1 for the next state, or it emits a token by block write and goes to vl_read (385), which re-reads char I for the state in RS (55). Source is NUL-terminated (VB5): c = 0 is the end.

| Id | File | Computes |
|---|---|---|
| 399 | vl_start | registers, first read |
| 385 | vl_read | block read char I -> RS |
| 384 | vl_idle | 38 thresholds, 29 classes; every output row linear in classes (one-hot), plus MUX_INT rows for state seeds (first digit, first letter value, string start) and for the address (TP or next char) |
| 386 | vl_word | KEY = 64 (KEY mod 2^42) + v, mod by FLOOR(KEY 2^-42) (exact scaling) |
| 387 | vl_kw | KL = KEY + 2^48 KLEN; 55 IS_K pairs on KL against hand-summed constants (table below); token from 4 aggregate rows (K, V, isRem, isKeyword); identifier after Sub/Function -> vl_preg |
| 388 | vl_preg | PROCT[NPROC].key = V |
| 389 | vl_num | number states (section 4); calls numconv (parse agent, id 75) |
| 391 | vl_nend | Integer / Long / Double kind; emit |
| 390, 395, 396 | vl_str, vl_strq, vl_semit | string units to a VSTR record, "" escape, header, token |
| 394 | vl_op2 | <> <= >= |
| 392, 397 | vl_date, vl_dser | m/d/y fields; serial by the civil-day formula (encodings/vba.md 4.1) |
| 393 | vl_cmt | skip to LF |
| 398 | vl_done | VGLOB NPROC, NTOK, VHT; halt or chain to the parser (CHAIN word 38) |

**Keyword constants KL = KEY + 2^48 len** (KEY from encodings/vba.md; 2^48 len added by hand: len 2 562949953421312, 3 844424930131968, 4 1125899906842624, 5 1407374883553280, 6 1688849860263936, 7 1970324836974592, 8 2251799813685248). Bias pairs are 0.5 - KL and -0.5 - KL, exactly representable (spacing at most 0.5 below 2^52). Order of the 55 pairs: Sub Function End Dim As If Then Else ElseIf Select Case For To Step Next Each In Do Loop While Until Wend Exit Call Debug Print MsgBox Integer Long Double String Boolean Variant Single Date Byte Private Public ByVal ByRef Option Explicit Const Mod And Or Xor Eqv Imp Like Is Not True False Rem.
**Costs.** About 3 steps per short token, 1 per extra identifier char, 2 per string char, number end + 2 (numconv). 182 steps for a 3-line Sub. vl_kw about 1,100 parameters, vl_idle about 3,300.
**Limits.** Identifiers over 8 characters collide when length and last 8 characters agree; length < 32. No &H/&O literals, no type-suffix characters on identifiers, no ".5" literals, no date times or 2-digit years, exponents beyond 22 need numconv's numbig path, which routes back by relu(RID - 128) and so fails for ids above 127 (request to the parse agent below). Unknown characters are skipped silently.
**Multi-role words.** 51 is KEY (word) or DST (string); 53 KLEN or S0; 56..61 are numconv's inputs or the date fields; 48 is NST (number) or OP2 (< >). Roles are exclusive by lexer state, and vl_idle seeds every one at a token start. **Tests.** test_lex_* in tests/output/vba/test_vba.py.
