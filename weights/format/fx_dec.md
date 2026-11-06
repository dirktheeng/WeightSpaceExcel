# Weight block note: fx_dec (id 192), decimal decomposition

Hand-written. Not generated. Log: log/format-agent.md "numeric core"; decision F1.

**Computes.** From x = A.PAY: s = [x < 0] (AS), e = floor(log10 |x|) + sc (AR1, sc = T2 scale, added only when x != 0) and m = round(|x| 10^(14 - e)) in [1e14, 1e15) (AC1): Excel's 15 significant digits. x = 0 gives (0, 0, 0). One step; next = T10, PC unchanged. Params 606, 52 layers.

**Derivation.** Coarse stage: candidates c_g = a_g 10^(320 - 16 g), g = 1..39 (one R1 row each; a_g = |x| [|x| < 1] for g <= 19 and |x| for g >= 20, so no candidate overflows: V1). Gate g is u_g comp_g with u_g = [c_g >= 1] = step(c_g - nextdown(1)), the constant 0.9999999999999999 parsing to 1 - 2^-53, and comp_g = [c_(g+1) < 1] = step(1 - c_(g+1)); these are exact complements of each other for consecutive g, and the c_g decrease with g, so exactly one gate is 1 when |x| >= 1e-304. a1 = sum gate c_g (one nonzero term, exact), B = 16 g - 320. Fine stage: cand_j = a1 10^(14 - j), j = 0..16 (17 so a1 up to 1e16 (1 + 2^-51) is covered), gates [cand_j > L][cand_(j+1) <= L] with L = 99999999999999.5 and the second test written as step(L' - cand) with L' = 99999999999999.515625 = nextup(L) (doubles in [2^46, 2^47) are 2^-6 apart), so again exact complements. m0 = ROUND(selected cand) (magic constant C = 1.5 * 2^52), carry kappa = [m0 = 1e15] gives m = m0 - 9e14 kappa and e + 1. Every equality case of a power of ten falls into one bin and the carry repairs a bin just below.

**Precision.** Two products with correctly rounded constants (10^k inexact for |k| > 22): about 1 ulp, enough for 15 digits except values within about 1e-16 relative of a 15-digit midpoint (open question, as in encodings/value.md section 4).

**Limits.** |x| < 1e-304 gives m = 0 (shown as 0). Multi-role weights: none. Tests: test_fx_dec (15 cases), test_fx_dec_scale.
