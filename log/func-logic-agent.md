# func-logic-agent progress log

Owner: weights/func/logic/, network ids 296 to 311, tests/output/func_logic/.

## 2026-11-06
- Read AGENT_BRIEF, RULES, HARNESS, FORMAT, encodings (value, control, primitives), prim CONVENTIONS, eval README. encodings/functions.md (ABI) does not exist yet, so per the brief I start with the computational cores as subroutine networks with explicit register inputs and outputs, and will wrap them once the ABI appears.
- Plan: three one-step leaf subroutines following control.md section 4 (args in A, B, C; result in A; selector in T0; return next = LR, PC = LP; STATUS = 0):
  - lg_info (296): every unary Information function plus NOT, NA, TRUE, FALSE, selected by T0.
  - lg_fold (297): AND / OR / XOR as an accumulator over arguments (init, add direct argument, add referenced value, finalize).
  - lg_cond (298): branch decision core for lazy IF, IFS, IFERROR, IFNA, SWITCH (returns which branch to evaluate in STATUS).
- lg_info (296) written: one forward pass, tag thermometer + selector thermometer, parity chain (q = |x|/2, r = ROUND(q), u = r - q; odd = [u > 0] or [u = -0.5]), conjunction steps, 20 gated candidates selected by one mul. tests/output/func_logic/test_info.py: 85 cases pass on the first run.
- lg_fold (297) written: accumulator fold (C = first error, two counters). test_fold.py 16 cases x 3 functions pass.
- encodings/functions.md appeared (ABI agent). Key facts: eager evaluation (F4), so "lazy IF" is selection among evaluated arguments; references arrive undereferenced as tag 9 (PAY = packed key); arguments on the operand stack at SP - 2 (n - i), last one in B; return next = 257 PC 0 result in A; preserve set includes N0 = n and words 40..63.
- lg_un (299): ABI entry for one-argument functions; maps T2 = 64 + fid to the lg_info selector by a 19-step thermometer with hand-computed jumps; tag 9 goes through CELL_GET (key unpacked by two FLOORs); ISFORMULA reads slot word 3. test_un.py 48 pass.
- Decision: moved lg_fold counters from N0/N1 to T3/T4 because N0 = n is in the ABI preserve set and N1 is the streamer's argument index. (Only slice indices changed; edit made as a plain text replacement of the slice lines, no weight rows touched.) Tests re-run: pass.
- lg_arg (300): argument streamer. Entry writes B to [SP, SP+1] so all n arguments are uniform in memory, then one block read (N = 2) per argument into a 67-input consumer. A dereferenced value is written back over its slot and refetched with T5 = 1.
- lg_cfold (301): AND/OR/XOR consumer, routes to lg_fold with LR = 300 LP = 1 (fold returns straight to the fetch) or, at the end, LR = 257 (fold returns straight to FN_RET). test_abi_fold.py 15 pass. Cost: 3 steps per argument + 5; a reference adds 5 to 7.
- lg_csel (302): IF/IFERROR/IFNA/IFS/SWITCH consumer, 4 step-layers of conjunctions, one step per argument looked at. test_abi_sel.py 45 cases: all expected values right on the first run (one test-side typo in a stated key fixed). Total 209 pass.
- lg_sheet (303): SHEET / SHEETS. test_sheet.py 8 pass.
- Notes written: weights/func/logic/README.md and one .md per network. Parameter counts summed by hand from the dense headers: 296 1302, 297 1533, 299 1158, 300 350, 301 294, 302 3199, 303 424; total 8260.
- WORKLOG entry appended (LG1 to LG4, Q-LG1 to Q-LG3). MANIFEST lines appended for 296, 297, 299, 300, 301, 302, 303.
- Full suite: tests/output/func_logic 217 pass. Whole tests/output: 18 failures in eval, stage1 and ui tests (fault 5 routes, ranges, UI outline), none touching ids 296..311; removing my manifest lines does not remove them, so they come from concurrent work elsewhere.
- Not done: CELL, INFO (need text arguments and text results; deferred), ISOMITTED (stage 10), BYCOL/BYROW/LAMBDA/LET/MAKEARRAY/MAP/REDUCE/SCAN (stage 10), STOCKHISTORY. FUNC_TABLE entries must be written by FT_INIT (ABI agent).
