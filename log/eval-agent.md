# Eval agent log (weights/eval, ids 80..117)

## 2026-11-06, Stage 1: reading and design
- Read GOAL.md, docs/*, harness/FORMAT.md, harness.py, encodings/*, weights/kernel/*.md, weights/prim/*.md, log/WORKLOG.md, tests/output/stage1/cases.yaml, later memory-map.md section 13 (parser deviations) and weights/parse/README.md.
- Constraints that drove the design: one memory op per step, state width 64, kernel locals L0..L11 live during the hook, CELL_SET clobbers A, P0, T0, T1, STATUS, ids 80..127 available (parser has 64..79).
- Decisions (recorded as E1..E6 in log/WORKLOG.md): precedent lists hung on formula record word 6 instead of dependents lists; precedents are cell slots (blank precedents are created as blank cells so edges never need a hash in recalc); full recalc of a formula list at CALC_CHAIN on every commit, ordered by an iterative DFS on WORK_STACK; cycles by a Tarjan low link (cells whose low link reaches an ancestor evaluate to 0); single-step networks with small PC phase sets; lazy dereference of cell references (TAG 9 = cell reference, PAY = K) so intersection and functions can see references later.

## 2026-11-06, recalc networks (ids 80..94)
- Wrote hk_commit, hk_delete, rc_chain, rc_scan, rc_ref, rc_got, rc_next, rc_fin, rc_edge, rc_class, rc_enter, rc_loop, rc_back, rc_done by hand.
- Test driver tests/output/eval/evalbb.py: BOOT, then each cell committed through CELL_SET (id 16) with LR = 80, token streams written into memory as test data.
- Run 1: =1+2 -> 3 in 62 steps on the first attempt. Refs, chains (dependents above precedents), edits, self cycle (A1 = A1 + 1 -> 0, CIRC_FLAG = K + 1 of A1), two-cell cycle with a dependent (C1 = A1 + 1 -> 1), cycle broken by edit (A1 = B1 = 3, C1 = 4, CIRC_FLAG 0): all as expected.

## 2026-11-06, evaluator networks
- ev_start, ev_disp, ev_push, ev_push2, ev_pop, ev_dref, ev_t2n (stub), ev_end, ev_func (stub), ev_arith (SAFE_ADD and SAFE_MUL retyped from weights/prim), ev_div (copy of weights/prim/div.wt, layers 1..338 unchanged, new tail).
- Runs: 7/2 = 3.5, 1/0 #DIV/0!, 1/3*3 = 1, 1E308*10 #NUM!, error precedence (#N/A + #DIV/0! -> #N/A; 1/0 + #N/A -> #DIV/0!), "a"+1 #VALUE! (stub coercion), TRUE+1 = 2, 12% = 0.12, 200%% = 0.02, blank/5 = 0, 5/blank #DIV/0!: all as expected.
- ev_cmp, ev_scmp_a, ev_scmp_b: 32 comparison cases incl. type ordering, case-insensitive text, blank adoption, 0.1+0.2=0.3 TRUE (tolerance): all as expected after fixing my own test data (an apostrophe-prefixed test string bug, not a weight bug).
- ev_totext, ev_fmt0, ev_fmt_emit, ev_cat: first version of ev_totext had two wrong rows (LR gate and a swapped sign in the string word value); found by re-deriving before running, fixed. Runs: abcd, 12, 1.5, TRUE, TRUEFALSE, 0.333333333333333, 0.3, 1E+20, -5, 0.12, blanks -> "", errors propagate, 123456789012, 0.000001, 123, 0, -0.5, 1E+15, 1E-10 all as Excel; 2.5E-12 wrong (outside the 1e-10..1e21 bank, documented).
- ev_pow0, ev_pow1 (square and multiply): 2^10, 2^-2, 0^0 #NUM!, 0^-1 #DIV/0!, (-2)^3, (-8)^(1/3) #NUM!, 10^309 #NUM!, left associativity, -2^-2: all as expected. 2^0.5 gives #NUM! (no EXP/LN yet; documented limit).
- Coordinator note: harness is being extended by another agent; I do not touch harness/.

## 2026-11-06, integration run and fixes
- Patched copies of c_set.wt (LR 80) and ev_decode.wt (LR 81) in /tmp only (never in the repo) to run tests/output/stage1/cases.yaml through the real parser. Run 1: every formula gave 0. Trace showed rc_loop routing to rc_done PC 0, i.e. CYC set: word 24 holds parser garbage and rc_class cleared CYC with relu(CYC - q5), weight 1. Fixed rc_class z7 to weight -2^23 on q5. Run 2: 249 of 273 non-SUM cases pass. Failures: 17 text coercion (ev_t2n stub), ari05 2^0.5, rng09..11 (parser), ref12 (parser), cir05/06/09 (test_stage1 checks `circ in []`; engine gives the right 0).
- tests/output/eval/test_eval.py: 91 passed. Compliance suite: only failure is tests/output/ui/ui_util.py (another agent).
- Next: ev_t2n through a number lexer (spill B, C, T2, HT, GEN, CYC to RET_STACK, call parser 78, restore); EXP/LN for ^; intersection network 108 once the parser emits op 33; FUNC_TABLE dispatch in ev_func.
