# weights/prim/div.wt: DIV(a, b), correctly rounded division

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "div". Decisions D15, P-D4, P-D5 (answers most of Q-P1).

**Computes.** a = A.PAY, b = B.PAY, finite doubles. T0 = fl(a / b), the IEEE round-to-nearest-even quotient, or 0 when the quotient overflows or b = 0. T1 = overflow flag (#NUM!), T2 = divide-by-zero flag (#DIV/0!; when T2 = 1, T1 is meaningless). One forward pass, 338 block layers.

## Structure and derivation

1. **v4, v5: |a|, |b| as pairs.** relu of [a, -a, b, -b, 0, 0] gives [a+, a-, b+, b-, ea = 0, eb = 0]; |a| = a+ + a- with one term 0.
2. **NORM, v6..v152 (21 stages of 7 layers, a and b in parallel rows).** Down stages k = 512 .. 1: D1 rows 2^k - x (R3, sign exact), x, 2^-k x (exact power-of-two scaling); step gives u = [x < 2^k] (keep); D2 forms gates [u, 1 - u] and e + k (1 - u); mul 0 4 4 8 selects x or x 2^-k exactly. After them x < 2. Up stages k = 512, 512, 256 .. 1: D1 rows 2 - 2^k x (the test x < 2^(1-k) rewritten with a positive literal), x, 2^k x (no overflow since x < 2); g = step gives take; e - k g. Invariant after up stage k: x in [2^(1-k), 2); the doubled 512 stage reaches subnormals (2^-1074). Result m in [1, 2) (or 0 for a = 0, harmless), x = m 2^e exactly. Every literal 2^+-k was checked exact by a debug forward pass (log "constant check").
3. **RECIP, v153..v177.** y0 = 24/17 - (8/17) mb (P-D4), 4 Newton steps as in idivmod.md. y is within a few ulps of 1/mb.
4. **Q0 = fl(ma y), v179.** Within about 3 ulps of the mantissa quotient q = ma / mb, which lies in (0.5, 2).
5. **Residual 1, v180..v196 (Dekker TwoProduct).** Split constant 2^27 + 1 = 134217729 (R1 row), hx = cx - (cx - x), lx = x - hx (R2 rows), p = fl(x mb), the four partial products (each exact: at most 26 x 27 bits), err = (((hh - p) + hl) + lh) + ll, each a single R2 add, exact by Dekker's theorem (no overflow or underflow is possible because x and mb are in (0.25, 4)). ma - p is exact (Sterbenz, p within a factor 2 of ma). R0 = fl((ma - p) - err).
6. **Q1 = fl(Q0 + fl(R0 y)), v197..v200.** The correction is accurate to about 2^-50 relative and |R0 y| is a few ulps, so Q0 + fl(R0 y) is within a tiny fraction of an ulp of q and Q1 is within 0.5 ulp plus that fraction: Q1 is faithful (one of the two doubles bracketing q).
7. **Residual 2, v201..v217.** Same block for Q1. R1 = ma - Q1 mb is exactly representable because Q1 is faithful (Q1 mb is a multiple of 2^-105 and |R1| < ulp(Q1) mb needs at most 53 bits), so R1 is exact.
8. **Exact midpoint check, v218..v226.** q - Q1 = R1 / mb. The correct result is the neighbour of Q1 iff |q - Q1| exceeds half the gap on that side. Gaps: above Q1 the half gap is 2^-53 if Q1 >= 1, 2^-54 if Q1 < 1; below it is 2^-53 if Q1 > 1, 2^-54 if Q1 <= 1. Rows R1 - 2^-53 mb, R1 - 2^-54 mb, -R1 - 2^-53 mb, -R1 - 2^-54 mb: the product by a power of two is exact, so each row's sign is exact. A tie is impossible: q = M for a 54-bit midpoint M would need M mb = ma, but M mb has at least 54 significant bits. AND gates with [Q1 < 1] and [Q1 > 1] choose the right gap, and delta = +-2^-52 or +-2^-53 (at most one term) moves Q1 to its neighbour exactly. Q is the correctly rounded mantissa quotient.
9. **Flags, v227..v244.** E = ea - eb. sa = [a < 0], sb = [b < 0], dz = 1 - [b < 0] - [b > 0]. Overflow: Q 2^E >= 2^1024 iff E + [Q >= 1] + [Q >= 2] >= 1025 (Q in (0.5, 2]); one R4 row and a step. Gate g = step(0.5 - ov - dz); Qs = sgn g Q with sgn = 1 - 2 XOR(sa, sb). Gating first keeps every later product finite even for b = 0 (where NORM and RECIP produce large but finite garbage).
10. **Exponent split, v245..v257.** Ec = max(E, -1077) (below that the result is 0 anyway: Q 2^-1077 <= 2^-1076 rounds to 0). P = min(relu(Ec), 1023), N = min(relu(-Ec), 1021), E2 = Ec - P + N in [-56, 1] (upper clamp to 1 only matters when ov, where Q = 0). Integer relu rows, exact.
11. **Power-of-two cascade, v258..v327 (10 stages k = 512 .. 1).** Bits of P, N and N2 = relu(-E2) are taken greedily (step(P - k + 0.5), P - k bit), and three factors Fp = 2^P, Fn = 2^-N, F2 = (1 + relu(E2)) 2^-N2 are built from 1 by mul gating. Each intermediate is a product of distinct bits of a number at most 1023, so it stays within [2^-1023, 2^1023]: no infinity ever meets a zero gate.
12. **Scaling, v328..v336.** q = ((Qs Fp) Fn) F2. Qs Fp is exact (no overflow once ov is excluded); times Fn is exact (Fn >= 2^-1021 keeps Qs Fn >= 2^-1022, normal); the last product is the only rounding, and only when the result is subnormal.

## Q-P1 status

- **Normal results (|q| >= 2^-1022): correctly rounded.** Steps 5 to 8 make Q exact as argued; scaling by powers of two is exact. The one argued (not exhaustively proved) step is faithfulness of Q1 (item 6); if it ever failed by 2 ulps, the midpoint check would still move Q1 by at most one ulp.
- **Subnormal results: possible double rounding.** Q is rounded to 53 bits, then the final product rounds again to the subnormal grid. If Q lands exactly on a subnormal midpoint while q is not on it, the second rounding can pick the wrong side. Rare; Excel shows such values as 0 or within 1e-308 of it, far inside docs/ACCEPTANCE.md tolerances, but not bit exact. Fix if needed: run the midpoint check at the subnormal grid spacing instead of 2^-53 (needs the exponent before step 8). Open as Q-P1b.
- **Exact quotients** (=6/3, =1/0.5, =-7.5/2.5) are exact, as required.

## Limits and costs

Inputs finite (V1). b = 0 gives dz = 1, q = 0. Overflow gives ov = 1, q = 0. a = 0 gives q = 0 (sign may be -0, equal to 0). Cost: 10470 parameters as written, almost all zeros in the wide copy matrices of the 31 stage blocks (about 1100 nonzero), 338 layers, 0 extra harness steps. The NORM D2 and cascade D2 copy matrices could be replaced by slice and concat with small gate rows to cut the stored parameters by roughly 8 times; not done yet.
**Multi-role weights.** None. Each pair word holds one value; gates are exclusive.
**Tests.** test_div (39 cases: everyday quotients with known IEEE results such as 0.3/0.1 = 2.9999999999999996, 10/3 = 3.3333333333333335; binade edge cases; MAXD, 2^-1074 ties to even; overflow boundaries such as MAXD / (1 - 2^-53)), test_div_by_zero (4): pass.
