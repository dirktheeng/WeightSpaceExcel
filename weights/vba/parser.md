# Weight block notes: VBA parser (ids 400..419)

Hand-written. Not generated. Token and bytecode formats: encodings/vba.md sections 4 and 7; parser state: section 6. Log: log/vba-agent.md "parser"; decisions VB10 to VB13 in log/WORKLOG.md.

**Protocol.** The parser state is 136 words (K = 136 in every block op): words 7..63 are passed through (VHT 43, XHT 23, CHAIN 38 survive to the interpreter), parser registers are words 64..135. Every state network takes 143 inputs: the state plus 3 tokens (K0 V0 K1 V1 K2 V2 at input 137..142) block-read at TP. A network that only consumes tokens reads the next 3 tokens itself; a network that emits bytecode block-writes it at BCP (payload at output 136 up) and goes to ps_read, which re-reads at TP and continues at NX. Lookahead (K1, K2) lets Dim, `x =`, `Debug.Print` and `For v =` skip known tokens by TP + 2 n without extra steps.

| Id | File | Computes |
|---|---|---|
| 400 | ps_start | registers (TP = TOK, BCP = BC + 8, PC = -1); block read PROCT (8 records) |
| 401 | ps_pk | procedure keys PK0..7 into registers; writes the prologue PUSH E, PUSH E, CALL 0, END |
| 402 | ps_read | block read 3 tokens at TP -> NX |
| 403 | ps_stmt | statement start: 14 classes on K0 (triangles relu(K - t)), unknown -> ps_skip |
| 404 | ps_fin | BCLEN to VGLOB + 6; CHAIN 1 -> vi_start (420), else halt |
| 405 | ps_skip | skip to the end of the statement |
| 406 | ps_sym | identifier lookup: [V = PK_j], [V = S_i] AND [i < NSYM] by triangles on exact differences (< 2^53); insert a new local at NSYM; outputs CURF, SIX, SI, PF, PI; -> SN |
| 407 | ps_dim | As type -> vt (collapsed triangle sum on K2), INFO += 4096 vt, emit PUSH Empty + STORE (typed store gives the initial value) |
| 408 | ps_sid | statement identifier: Sub call (PUSH E, PUSH E, CALL, POP) or assignment target |
| 409 | ps_expr | shunting-yard step (below) |
| 410 | ps_for | loop variable -> TGT, TGS; CTX 5 |
| 411 | ps_next | increment, JMP top, patch the loop JZ, pop |
| 412 | ps_else | JMP 0, patch the JZ, block a = JMP |
| 413 | ps_end | End Sub/Function (RET), End If, else skip |
| 414 | ps_xend | expression end by CTX (assign, print, MsgBox, If, For start/limit/step) |
| 415 | ps_pend | PROCT[PC] = [entry, 15 slots, 0 params] |
| 416 | ps_endif | patch the pending JZ/JMP to BCP, pop |
| 417 | ps_patch | write PV at PA |
| 418 | ps_xid | identifier operand: LOAD slot, or CALL of a procedure without arguments |
| 419 | ps_dimc | ',' -> next Dim item |

**Registers (words).** 64 TP, 65 BCP, 66 NX, 67 PC, 68 NSYM, 69 CTX (1 assign, 2 print, 3 MsgBox, 4 If, 5..7 For), 70 AO (operand expected), 71 TGT (STORE arg), 72 CURF, 73 SIX, 74 SI, 75 PF, 76 PI, 77 SN (ps_sym continuation), 78 EMP (0 operand seen, 1 fresh, 2 after ';'), 79 ENT, 80 CD (block depth), 81..88 PK0..7, 89..96 S0..7 (local keys), 97..104 INFO0..7 (slot + 4096 vt), 105..110 OP0..5, 111..116 PR0..5 (operator stack, 0 top), 117..128 block stack, 3 entries of [kind, a, b, c], entry 0 top (If [1, pending jump, 0, 0]; For [2, top, info, slot]), 129 TGS, 130 PA, 131 PV.

**ps_expr.** Classes: identifier, literal (3..8), '(', ')', ignore ('.', Print), operator (16..41) with sub-classes +, -, Not, terminator (rest). Gates: hp = [PR0 > 0], ge = [PR0 >= V]; cb = operator AND NOT AO (binary), um = '-' AND AO, bpop = cb AND ge. Stack update R_i' = s R_i + u R_(i-1) + o R_(i+1) with s, u, o gates replicated and multiplied in one mul layer of 36 products; the pushed entry is (K + 23 um, V + 4 um), which gives '(' (10, 0), unary minus (40, 13), Not (41, 6) and binary (K, prec) at once. PUSH opcode for literals = 79 + K + [K >= 5] + 2 [K >= 6] - 2 [K >= 7] + 3 [K >= 8] (82, 83, 85, 88, 87, 91 for K = 3..8).

**ps_xend.** Flags are one-hot triangles on CTX, K and EMP; gates are relu ANDs (relu(a + b - 1)). Payload of up to 16 words; the For limit end (no Step) writes STORE h, PUSH 1, STORE h + 1, LOAD i, LOAD h, LOAD h + 1, FORCHK, JZ 0 in one block write. Hidden For slots h = 9 + 2 CD, h + 1.

**ps_dim vt coefficients.** vt = sum over t = 90..100 of c_t relu(K2 - t) with c = 2, -1, 1, 1, 0, -14, 16, -3, 8, -27, 17 (c_t = vt(t + 1) - 2 vt(t) + vt(t - 1)); checked by hand at K2 = 95 (11), 97 (5), 99 (17), 120 (0).

**Costs.** About 2 steps per token in expressions (1 to consume, 2 per emitted instruction), 3 steps per identifier operand. The 4-line test program parses in about 30 steps. Parameters (dense weights and biases, zeros included): ps_sym 4,241, ps_xend 2,761, ps_expr 2,035, ps_dim 1,016, ps_stmt 920, the rest under 520 each; 13,038 in all.

**Limits.** At most 8 procedures, 8 locals per procedure (a 9th local is silently given slot 0), operator stack depth 6, block nesting 3; every frame has 15 slots. No parameters or arguments (calls are `F()` or `F` only); no ElseIf, single-line If, Do, While, Select, Exit, GoTo, With, Const, arrays; ',' in Debug.Print acts as ';' (no print zones); MsgBox only as a statement; unbalanced parentheses and syntax errors are not reported (PSTATUS stays 0). Program entry is procedure 0 (the first in the module).

**Multi-role weights.** ps_expr's TP' and address rows serve every class (exclusive one-hot); ps_xend's payload rows sum per-class contributions, of which one is nonzero. **Tests.** test_src_* in tests/output/vba/test_vba.py.
