# dv_ent (id 354) and dv_rest (id 357): entry and exit of the date/time text parser

Hand-written (log/func-date-agent.md session 2; decision FD-7 in log/WORKLOG.md). The parser chain is dv_ent -> dv_loop (355) -> dv_fin (356, with calls of dt_time 346 and dt_date 345) -> dv_rest. It serves DATEVALUE (fid 114), TIMEVALUE (fid 468) and the text-to-date coercion of date arguments (dt_coer 358), and is meant for the evaluator's text coercion too (see README.md, "Evaluator change for coe21").

**Interface (leaf subroutine).** Caller sets next = 354, PC = 0, A = the argument, T0 = mode (0 DATEVALUE, 1 TIMEVALUE, 2 coercion), LR, LP. Returns to (LR, LP) with A = (1, value) or an error, STATUS = 0. **Every other word comes back unchanged** (RSP balanced): dv_ent block-writes words 8..39 at RSP (32 words, RSP += 32), the chain uses words 12..39 as its private state, and dv_rest (block consumer, input 97) restores words 8..11 and 15..39 from the spilled block and returns to the spilled link. Uses 32 words of RET_STACK during the call.

**dv_ent (one step).** Output 96 words, mem_op 3 (decision T4). Word 15 = mode, word 16 = a = A.PAY gated by [A is text] (so a non-text argument never reads outside memory), words 17..35 = 0, word 36 = ecode0 = A.PAY for an error argument, 3 for any other non-text, 0 for text. next = 355 PC 1.

**dv_rest (one step).** next = spilled LR, PC = spilled LP, words 8..11 and 15..39 spilled, STATUS 0, A and words 40..63 current.

**Parameters.** dv_ent 160 (21 layers), dv_rest 27 (12 layers). **Steps.** Whole chain: 1 + 2 + (L + 1) + 3 + 1 (dt_time) + 1 (dt_date) + 1 = L + 10 for a string of L characters ("1/2/2000": 18).

**Multi-role weights.** Words 12..39 hold parser state only between dv_ent and dv_rest, while the caller's values sit in RET_STACK; no word holds two meanings at one time. **Tests.** tests/output/func_date/test_dv.py (83 cases, including the preserve check on every call), test_dv_abi.py.
