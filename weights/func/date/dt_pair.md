# dt_pair (id 347): two-date driver

Hand-written (log/func-date-agent.md; decision FD-3). Three phases, one step each.

| PC | Does | Next |
|---|---|---|
| 0 | T9, T10 = LR, LP; T0 = 0; LR = 347, LP = 1 | 344 (dt_ymd on A) |
| 1 | A error: return it. Else AS AR1 AC1 P0 = T1 T2 T3 T8 (y1 m1 d1 n1); P0 rather than AR2 because word 22 is GEN in the ABI preserve set (FD-6), A = B; LP = 2 | 344, or T9 |
| 2 | A error: return it. Else route to the finisher; for N1 = 2 with a text C, read mem[C.PAY + 2] | 348 (N1 < 3), 353 (N1 >= 3), or T9 |

N1 = 0 DAYS(A = end, B = start), 1 DAYS360, 2 DATEDIF, 3 YEARFRAC (A = start, B = end, C = method / unit / basis). All gating is by products of 0/1 gates with the register values (one mul layer of 20 pairs), so no garbage word reaches an output.

**Parameters.** 1357 dense parameters, 55 layers. **Tests.** test_dt_pair.py, test_dt_yf.py.
