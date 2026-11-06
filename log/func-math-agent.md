# Func math agent log (weights/func/math, ids 264..295)

## 2026-11-06, Stage 3: reading and plan
- Read docs/AGENT_BRIEF.md, GOAL.md, docs/RULES.md, docs/DOCUMENTATION.md, docs/HARNESS.md, harness/FORMAT.md, encodings/value.md, control.md, primitives.md, memory-map.md section 13, weights/prim/CONVENTIONS.md and floor_round.wt, weights/eval/README.md, pow.md, ev_pow2.wt header, log/eval-agent.md.
- encodings/functions.md (ABI) does not exist yet. Per the brief I start with computational cores as subroutine networks with explicit register I/O, using the control.md call convention (call with LR, LP; return next = LR, PC = LP, result in A, STATUS).
- Interim register contract for my networks (to be wrapped to the ABI later): argument 1 in A (words 13, 14), argument 2 in B (15, 16), function selector in T0 (word 29) for family networks. Result in A, STATUS = 0. Every other word passes through.
- Plan: family networks rather than one per function, to save ids and parameters (rule 4): fm_unary (id 264) for the one-argument piecewise-linear and constant functions ABS, SIGN, INT, TRUNC (1 arg), PI, EVEN, ODD, DEGREES, RADIANS, all in one forward pass with a 9-way selector MUX.
- Reuse check: ev_pow2 (id 99) contains EXP and LN, but it returns to ev_disp with fixed next = 96 and TP += 2, so it is not callable as a subroutine. Needed change (eval agent's file): a variant or a link-return phase so EXP/LN/SQRT/POWER can call it. Reported, not edited.

## 2026-11-06, fm_unary (id 264)
- Wrote weights/func/math/fm_unary.wt by hand: coercion front end, |x|, signs, big and DEGREES-overflow guards, four parallel FLOOR blocks retyped from prim/floor_round, sign corrections by mul, 9 candidates, 9-way selector MUX, error/#VALUE!/#NUM! assembly, link return. Derivations in weights/func/math/fm_unary.md. 967 parameters, 1 step.
- Tests: tests/output/func_math/test_func_math.py (expected values stated by hand from Excel's documentation: INT rounds down, TRUNC toward zero, EVEN/ODD away from zero with ODD(0) = 1, DEGREES(PI()) = 180, RADIANS(270) = 4.71238898038469). The harness raises when max_steps is reached without halt, and this network returns to LR, so the test takes the single forward pass from the harness's loaded network (still black box).
- Run 1: 52 of 52 pass on the first run.
- Next (not done this session): ROUND/ROUNDUP/ROUNDDOWN/MROUND/CEILING/FLOOR variants (need 10^d ROM and Excel's decimal-aware rounding, e.g. ROUND(2.675, 2) = 2.68), MOD/QUOTIENT (DIV primitive), SQRT/EXP/LN/LOG/POWER (needs a link-returning ev_pow2 or a retyped NORM2 core), trig with argument reduction, GCD/LCM/FACT/COMBIN, aggregate functions (need the ABI's argument and range iteration), RAND/RANDBETWEEN.
