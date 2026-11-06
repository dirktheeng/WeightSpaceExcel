# Primitive library agent log (weights/prim/)

Task: implement the primitive blocks of encodings/primitives.md as standalone hand-written test networks in weights/prim/, with notes, black-box output tests in tests/output/prim/, and this log. Rules: docs/RULES.md (every weight typed by hand; forward passes only for debugging).

## 2026-11-06, Stage 1: reading and conventions

- Read GOAL.md, docs/RULES.md, docs/DOCUMENTATION.md, harness/FORMAT.md, harness/harness.py, encodings/primitives.md, value.md, control.md, address.md, log/WORKLOG.md, weights/poc/round_floor.*.
- Convention chosen for every test network (decision P-D1 in log/WORKLOG.md): 64-word state, input 65. Arguments are read from the register map (A.TAG input 14, A.PAY input 15, B.PAY input 17, C.PAY input 19, AS/AR1/AC1 inputs 20 to 22, T0/T1 inputs 30, 31). Results go to T0, T1, ... (words 29 onward). Words 0 to 6 are [0, 0, 0, 0, 0, 0, 1] (halt, no memory op). Every other word is passed through unchanged by slice and concat. The common "tail" is: a 7x1 dense with zero weights and biases 0 0 0 0 0 0 1, slice 0 8 30, the result vector, slice 0 (30 + k) 65, joined by three concats.
- Manifest ids: encodings/control.md section 5 assigns no id range to primitives (0 to 511 are all owned by subsystems; 512 and up are generated ids and must stay sequential). Primitives are blocks that are retyped into networks, not routable networks. Decision P-D2: their standalone test networks get no manifest id and are loaded by path in their own tests; nothing appended to weights/MANIFEST.txt.

## 2026-11-06: batch 1 (IS_K, ONEHOT, compare, MUX, FLOOR/ROUND, MOD2K, DIVMOD_K)

- Wrote by hand: weights/prim/is_k.wt, onehot.wt, compare.wt, mux.wt, floor_round.wt, mod2k.wt, divmod_k.wt.
- Derivations (detailed in each note): compare uses R2 rows a - b and b - a feeding step only, so an overflowing difference never reaches a dense layer. floor_round extends the poc FLOOR with CEIL = -FLOOR(-x) computed in parallel, TRUNC by mul-gated select on step(x), and Excel's ROUND half away from zero via exact tie detection (e = round_even(x) - x is exact; a tie is e = -0.5 or 0.5, detected as NOT step(e + 0.5) and NOT step(0.5 - e)). DIVMOD_K uses q0 = ROUND(fl(0.1 x)) instead of FLOOR (saves the FLOOR compare layer): with |x| < 2^51 the product is within 0.04 of x/10, so q0 is f or f + 1, and the two-sided exact remainder correction fixes it.

## 2026-11-06: constant check (debug forward pass, not committed)

- Large and tiny powers of two that I typed as decimal literals (2^64, 2^-64, 2^-128, 2^-256, 2^-512, 2^512, 2^1023, 2^128, 2^256) were placed as biases of a throwaway 9x1 dense in /tmp/primdbg/consts.wt and the forward output printed in hex: all nine are exactly 0x1.0p+-k. So the literals 2.938735877055719e-39, 8.636168555094445e-78, 7.458340731200207e-155, 1.3407807929942597e154, 8.98846567431158e307 parse to the exact powers.

## 2026-11-06: batch 2 (SAFE_ADD, SAFE_MUL, HASH, DIGITS)

- Wrote safe_add.wt, safe_mul.wt, hash.wt, digits.wt by hand.
- SAFE_MUL deviates from primitives.md (which scales by 2^-600 with a 2^-176 threshold): I scale each factor by 2^-512 (a verified literal) so s = fl(a b 2^-1024) and the overflow test becomes |s| >= 1, an exact compare. Derivation: fl(ab) overflows iff |ab| >= 2^1024 (1 - 2^-54); fl(X) >= 1 iff X >= 1 - 2^-54 (the midpoint rounds to the even value 1). Recorded as decision P-D3.
- SAFE_ADD: overflow iff |h| >= 2^1023 with h = fl(a/2 + b/2); tested as 2 - step(2^1023 - h) - step(2^1023 + h).
- hash.wt first version used a 3-word source (the [S, R, C] slice) for the 7x1 header dense; fixed to use v4 (t, one word) before any run.
- DIGITS: 14 independent chains, each q0 = ROUND(fl(n 10^-k)) plus exact correction; then one 15x15 dense d_k = f_k - 10 f_(k+1).
- Output tests: tests/output/prim/test_prim.py, expectations typed by hand. Run 1: 114 passed (the RuntimeWarnings are the expected overflows inside rows that only a step layer reads).

## 2026-11-06: idivmod (variable integer divisor)

- Wrote weights/prim/idivmod.wt: NORM down stages k = 32, 16, 8, 4, 2, 1 on d with a parallel S pair tracking 2^-e, RECIP by 4 Newton steps, yd = y S, q0 = ROUND(fl(x yd)), exact remainder by a mul layer (integer product < 2^50, exact), two-sided correction.
- Run 1: only powers of two correct (7/2 = 3 r 1, but 100/7 = -213538). Truncated a copy after v34 (debug, /tmp): NORM gave md = 1.75, S = 0.25 for d = 7 (correct), but y0 = -0.47. Cause: the initial guess in encodings/primitives.md, y0 = 48/17 - (32/17) m, is the minimax line for 1/m on [0.5, 1], not [1, 2]; at m = 1.5 it gives 0. Correct line on [1, 2]: y0 = 24/17 - (8/17) m (same 1/17 relative error, scaled by 1/2). Fixed v34 weights to -0.47058823529411764 and bias 1.411764705882353.
- Run 2: 7/2 = 3 r 1, 100/7 = 14 r 2, -7/2 = -4 r 1, (2^49 - 1)/3 = 187649984473770 r 1, 12345678901234/97 = 127275040218 r 88, (-(2^49 - 1))/7 = -80421421917331 r 6, (2^49 - 1)/(2^49 - 1) = 1 r 0. All as derived by hand.

## 2026-11-06: div (correctly rounded division)

- Design worked out on paper first (recorded in weights/prim/div.md and decision P-D5). Reasons for changes from D15: (1) D15's single refinement q0 + r y is not provably correctly rounded; I added a second exact residual and an exact midpoint comparison, which decides between Q1 and its neighbour with only exact operations. (2) Scaling the quotient directly by 2^E with a cascade can create an infinity in an unselected branch (V1 violation, 0 times inf = NaN); I build factors Fp, Fn, F2 from 1 instead, each bounded by 2^+-1023, and split E so only the last multiply rounds.
- Verified three more literals first (debug pass, /tmp): 2^-52, 2^-53, 2^-54 decimals and the split constant 134217729 all exact.
- Part 1 (NORM, v1..v152) written and run alone (the file ended at v152): 6, 3 gave [1.5, 0, 1.5, 0, 2, 1]; MAXD and 5e-324 gave ma = 1.9999999999999998, ea = 1023, mb = 1, eb = -1074; -0.1 gave 1.6, -4; 1e-310 gave 1.1505..., -1030. All as derived. a = 0 gave ea = -1535; I first expected -2047, but the up stages sum to 512 + 512 + 256 + ... + 1 = 1535, so the output is right and my expectation was the slip.
- Part 2 (RECIP to the midpoint check, v153..v226) run on a truncated copy: mantissa quotients 6/3 -> 1, 1/3 -> 0.6666666666666666 (= 1/1.5), 1/10 -> 0.8 (= 1/1.25), (2 - 2^-52)/(1 + 2^-52) -> 1.9999999999999993 (= 2 - 3 2^-52, derived by hand), 1/(2 - 2^-52) -> 0.5000000000000001 (just above the 0.5 midpoint, rounds up). All as derived.
- Part 3 (flags, exponent split, cascade, scaling, tail) run whole: 6/3 = 2, 1/3, -2/3, 1/10, 1/-7 correct; 1e308/1e-10 ov; 5e-324/2 = 0 (tie to even); 1/3e-320 ov; 0/5 = 0; 3/0 dz; MAXD/0.5 ov; 2^-1022/3 = 7.41691286169067e-309 (subnormal). Disclosure: in this one debug print I also printed Python's own a/b next to the outputs as a visual reference. No test uses code-computed values, and later checks were stated by hand only.
- Output tests added (test_idivmod, test_div, test_div_by_zero). Run: 2 failures, both mine in the expected values: (a) I typed 1/(1 + 2^-52) = 0x1.fffffffffffffp-1, but the true value 1 - 2^-52 + 2^-104 - ... rounds to 1 - 2^-52 = 0x1.ffffffffffffep-1, which is what the network gave; (b) 999999999999 / 999999 is exactly 1000001 (999999 * 1000001 = 999999999999), not 1000000 r 999999. Fixed both expectations and added 999999999998 / 999999 = 1000000 r 999998. Run: 172 passed. Compliance tests: 6 passed.

## 2026-11-06: measurement and notes

- Sizes from layer headers (dense ROWS x COLS + ROWS, tail excluded): is_k 7, onehot 75, compare 32, mux 40, floor_round 144, mod2k 23, divmod_k 26, digits 436, safe_add 35, safe_mul 35, hash 39, idivmod 753, div 10470.
- Notes written: weights/prim/*.md plus CONVENTIONS.md. Decision records P-D1 to P-D7 in log/WORKLOG.md.
- Not done: UNPACK3, ROM, DISPATCH, LOOP, CANCEL_SNAP, SQRT and later (not in this task's priority list). Next useful step: slim div.wt (replace the wide copy matrices with slices) and a grid-aware midpoint check for subnormal quotients (Q-P1b).
