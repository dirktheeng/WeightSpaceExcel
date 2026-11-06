# Weight block notes: fm_pw0 (id 268), fm_pw1 (id 269)

Hand-written. fm_pw1 v1..v291 are copied from weights/eval/ev_pow2.wt (eval agent; derivations in weights/eval/pow.md and log/eval-agent.md: NORM2, atanh series LN, guarded y = b L, EXP by k = round(y / ln2), Taylor degree 14, exact 2^k scaling with exact overflow test), with five in-place edits listed below. Not generated. Log: log/func-math-agent.md (2026-11-06).

**Family.** T0: 0 EXP, 1 LN, 2 LOG10 (and one-argument LOG), 3 POWER, 4 SQRT, 5 SQRTPI. x = A, b = B (POWER). Two steps, 268 then 269, which returns to (LR, LP) with A = result.

**fm_pw0 (268), 55 values.** Coercion and first error (A, then B for POWER). Floors of b and b/2 (gated by |b| < 2^51) give b non-integer and b odd. Domain rows (AND gates): LN, LOG10 x <= 0; SQRT, SQRTPI x < 0; SQRTPI x > 5e307 (x pi would overflow); POWER 0^0 and negative base with non-integer b give #NUM!, 0^negative #DIV/0!, 0^positive and SQRT(0) give 0. go = ok and no domain case. a' = go acand + (1 - go) with acand = 1 (EXP), x (LN, LOG10, SQRT), |x| (POWER), pi (1 - huge) x (SQRTPI); b' = go bcand with bcand = x (EXP), b (POWER), 1/2 (SQRT forms), 0 (logs). mode = EXP and ok. neg = POWER, x < 0, b odd.

**fm_pw1 (269), 343 values.** Edits to the ev_pow2 copy: v1 = [a', mode]; v2 has a zero column for mode; v135 = concat of [m, e] and v1; v137 Lo = 2 P s + e ln2_lo + mode; v138 Hi over 5 columns. When mode = 1, a' = 1, so e = 0 and s = 0 and L = 0 + mode = 1 exactly, so y = b' = x and the EXP half computes EXP(x) with no extra rounding; otherwise L = LN(a') as before and mode adds an exact 0.
Tail: V = gR R + gL L + gL10 (L log10(e)) (one nonzero term). Snap: if |V| < 2^51 and |V - ROUND(V)| < 2^-51 |V| and the selector is not LN, V = ROUND(V) (so POWER(2, 10) = 1024, POWER(9, 0.5) = 3, LOG10(1000) = 3, SQRT(16) = 4 exactly; Excel's library functions give these exactly). neg negates. Errors: fm_pw0's first, then the zero result, then EXP overflow (#NUM!); underflow gives 0.

**Parameters.** Not tallied yet (fm_pw1 = ev_pow2's layers plus the edited columns plus the tail). Steps: 2.

**Limits.** POWER and SQRT form y = b ln a as one double, so for |y| large the result has relative error up to about |y| 2^-53 (pow.md: 1e308^0.5 off by 7e-15). EXP and LN are within an ulp or two. LOG with a base other than 10 is not built (needs two LN passes and a division). The snap can round a true non-integer result lying within 2^-51 relative of an integer (displayed identically to 15 digits).

**Multi-role weights.** mode in v137 (row Lo): it adds 1 only when a' = 1 forces 2 P s = 0 and e = 0, so its role (forcing L = 1) and the LN role are exclusive by fm_pw0's construction. **Tests.** test_powfam (52 cases), all pass.
