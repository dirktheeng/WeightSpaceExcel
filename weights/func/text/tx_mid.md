# tx_mid (id 316): MID core (LEFT and RIGHT through wrappers)

Hand-written, not generated. Log: log/func-text-agent.md; WORKLOG Stage 3 Text entry, decision T3. Conventions: README.md.

**Computes** MID(A, B, C): units start - 1 .. start + count - 2 of A (0-based), fewer if A is shorter, "" if start is past the end. Start and count are truncated after clamping to [-2^23, 2^23]; start < 1 or count < 0 gives #VALUE!. Errors: A, else B, else C. LEFT(s, n) = MID(s, 1, n); RIGHT(s, n) = MID(s, max(1, LEN(s) - n + 1), n), computed by the wrapper. Clobbers P0, P1, N1, T1 to T4.

| PC | Step | Next |
|---|---|---|
| 0 | errors / bad start or count: return; else read [hA] | PC 1 |
| 1 | x0 = L; n, i0, o (below); write [HT] = n; P0 = hA + 2 + i0, P1 = HT + 2, OH = HT, N1 = n, T3 = o | PC 2 |
| 2 | N1 <= 0: A = (2, OH), HT = P1, return; else read [P0], P0 += 1, F = 1 | PC 3 |
| 3 | if F: T1 = x0; F = 0; read [P0], P0 += 1 | PC 4 |
| 4 | write [P1] = out word; T1 = x0; P1 += 1; N1 -= 3 | PC 3 if N1 >= 4, else PC 2 |

**Arithmetic** (PC 1): s0 = start - 1; d1 = relu(L - s0) = units available (0 if past the end, L if s0 < 0 is impossible after validation); n = d1 - relu(d1 - count) = min(d1, count); min(s0, L) = L - d1; i0 = ROUND(min(s0, L) / 3 - 1/3) is FLOOR of the third because the fractional parts 0, 1/3, 2/3 become -1/3, 0, 1/3, all far from the half-way points, and the R5 rounding error of the row is about 1e-16 times 2^23; o = min(s0, L) - 3 i0 in {0, 1, 2}.

**Realignment** (PC 4): prev word T1 has units u0 u1 u2, cur word x0 has v0 v1 v2. o = 0: (u0, u1, u2); o = 1: (u1, u2, v0); o = 2: (u2, v0, v1). Each output unit is a sum of three MUX_INT terms relu(unit - 2^17 (deficit)), the deficit counting how many of (offset indicator, keep indicator) are 0; keep for unit 1 is N1 >= 2 and for unit 2 is N1 >= 3, so the last word is masked even when the source word continues past the substring (or past the end of the string, where memory may hold other data). Units are below 2^16 < 2^17, so a term is the unit or 0. out = w0 + 2^16 w1 + 2^32 w2, exact.

**Clamp and FLOOR**: clamp(a) = relu(2K - relu(K - a)) - K; FLOOR by ROUND with C - K folded into the bias (same real sum as clamp + C, so the same rounding). Fractions below about 2^-29 are lost at the clamp's scale (a start of 3 - 2^-40 truncates to 3, Excel gives 2).

**Limits**: B and C must already be numbers. Open question: whether Excel truncates a negative fractional count (MID("abc", 2, -0.5)) to 0 before the sign test; this core floors it to -1 and gives #VALUE!. Not tested either way.
