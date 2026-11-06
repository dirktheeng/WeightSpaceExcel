# Weight block notes: emitter (ids 194, 200..209)

Hand-written. Not generated. Log: log/format-agent.md "numeric core" and "compiler"; decisions F1, F3.

Each displayed unit takes 2 steps: fx_fetch reads the token at TP and routes to 200 + NC (the code of that token, which the previous executor took from bits 20 up of its own token), then the executor writes one unit at BP (or nothing) and returns to fx_fetch, or stays (PC = 1, token kept in CUR) when it has more units to write. Executors that can stay pick the token from input word 0 or CUR by a [PC, 1 - PC] mul. Digits are peeled from M: q0 = ROUND(M 1e-14) corrected by the sign of r = M - 1e14 q0 (exact), d = q0 - neg, M' = 10 (r + 1e14 neg); after the last kept digit M is 0, so later digits are zeros (Excel shows zeros beyond 15 significant digits).

| Id | File | Token | Behaviour | Params |
|---|---|---|---|---|
| 194 | fx_fetch | | read TP, TP + 1, next = 200 + NC | 27 |
| 200 | fx_end | 0 END | to fx_fin (212) | 16 |
| 201 | fx_lit | 1 LIT | writes arg | 42 |
| 202 | fx_int | 2 INT | j = N0 - 1 - jl. R > j + 1: extra leading digit (stay); R = j + 1: own digit; R <= j: '0', ' ' for '?', nothing for '#'. After a unit at position p (R - 1 or j) a ',' follows when TH, p > 0 and p mod 3 = 0 (p mod 3 by p - 3 ROUND(p/3)); SUB = 1 holds the pending comma for one step | 717 |
| 203 | fx_point | 3 POINT | flushes integer digits left (R > 0, stay), then '.'; arg 1 (General) writes '.' only when M != 0 | 253 |
| 205 | fx_frac | 5 FRAC | digit if type '0' or M != 0; ' ' for '?' at a trailing zero; nothing for '#' | 221 |
| 206 | fx_exp | 6 EXP | 'E'/'e', then '-' (X < 0) or '+' (unless 'E-'); sets XR = digits of abs(X) | 180 |
| 207 | fx_expd | 7 EXPD | as fx_int over the digits of abs(X) (d2, d1, d0 by two floors), j = T3 - 1 - jl, no commas | 558 |
| 209 | fx_fill | 9 FILL | writes the marker 65536 + c, N1 = 2 | 46 |

Products of a 0/1 gate and a small integer use MUX_INT (relu(v - B (1 - g)), B = 2^17 or 2^20); products with M use mul layers. Multi-role words: SUB (T5) is a pending comma in fx_int and the sign step in fx_exp; the two are never live together because SUB is 0 whenever an executor finishes. N1 is the scientific flag before emission (read by fx_rnd) and the fill flag after it. Tests: test_emit (11), test_emit_sci (8, one xfail: engineering exponent), and every full-engine test.
