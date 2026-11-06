# tx_exact (id 315): EXACT core

Hand-written, not generated. Log: log/func-text-agent.md; WORKLOG Stage 3 Text entry. Conventions: README.md.

**Computes** (3, 1) if A and B hold identical unit sequences, else (3, 0). Error in A returned, else error in B. Packed words are compared whole (3 units per comparison); unused positions of a last word are 0 by the heap convention (memory-map.md section 9), so equal strings have equal words. Clobbers P0, P1, N1, T1.

| PC | Step | Next |
|---|---|---|
| 0 | errors: return; else read [hA]; P0 = hA + 2, P1 = hB + 2 | PC 1 |
| 1 | T1 = len A; read [hB] | PC 2 |
| 2 | check: x0 != T1: FALSE; N1 = x0; N1 <= 0: TRUE; else read [P0] | PC 3 |
| 3 | T1 = x0; read [P1]; P0, P1 += 1 | PC 4 |
| 4 | check: x0 != T1: FALSE; N1 -= 3; N1 <= 0: TRUE; else read [P0] | PC 3 |

**Blocks**: d = step(x0 - T1) + step(T1 - x0) (exact for integers below 2^53). The remaining count N1new = N1 + p2 (x0 - N1) - 3 p4 uses one mul; le = step(0.5 - N1new). Outcomes F = chk AND d, T = chk AND NOT d AND le, R = chk AND NOT d AND NOT le, with chk = p2 + p4. rA, sB select which error is returned (sB = PC 0, B error, A not error). T1 is loaded through a mul gate (x0 - T1 times p1 + p3).

**Limits**: arguments must be text (wrapper coerces numbers: EXACT(1, "1") is TRUE in Excel).
