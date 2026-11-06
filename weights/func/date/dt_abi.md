# dt_abi (id 351) and dt_abi1 (id 352): function ABI entry for all date and time fids

Hand-written (log/func-date-agent.md; decision FD-6 in log/WORKLOG.md). Implements encodings/functions.md sections 2 and 6 for fids 112 113 116 117 118 147 150 213 270 307 315 335 413 467 474 502 503 515 516. FUNC_TABLE[fid] should be 351 for each (request to the owner of weights/func/core/ft_init.wt).

| Net, PC | Does | Next |
|---|---|---|
| 351 PC 0 | block read mem[SP - 4 .. SP - 1] (value 64 * 2^20 + 4) | 352 |
| 352 (input 69) | slots s1 s2 s3 = arguments 1..3 from the block words and B by n (N0); missing (8, 0) beyond n; N1 = 0 | 351 PC 1 |
| 351 PC 1 | store A into slot N1 (if N1 >= 1); first slot still tagged 9 (cell reference): unpack K into AS AR1 AC1 (FLOOR of K 2^-14 and K 2^-34), T1 = 0, N1 = slot, LR = 351, LP = 1 | CELL_GET 16 |
| 351 PC 1 | no reference left: dispatch ROM over T2 (19 IS_K pairs): A B C = s1 s2 s3 (B kept when n = 0), T0 / N1 / PC = the core's selector, LR = 257, LP = 0 | the core (344..350) |
| 351 PC 1 | argument count outside [min, max] for the fid, n > 3, or an unknown T2 | 257 with #VALUE! |

The cores return straight to FN_RET (their LR/LP, or T9/T10 for the chained ones, is 257/0), so a function costs 3 adapter steps plus 2 per referenced argument plus the core's steps (YEAR 4 in all, DATEDIF 9).

**Preserve set.** Words 10, 11, 22..27 and 38..63 pass through 351 and 352 unchanged; T3..T8, N1, T0, T1, AS..AC1, A, B, C, LR, LP are in the free set. The cores were changed (decision FD-6) so that they also keep the preserve set: function selectors moved from N0 to N1, and dt_pair parks n1 in P0 instead of AR2 (word 22, GEN). Checked on every call by tests/output/func_date/abibb.py.

**Limits.** Range arguments (tag 5) and unions (tag 10) reach the cores and give #VALUE! (no implicit intersection yet); text arguments give #VALUE! (no DATEVALUE coercion yet); arrays are not lifted. At most 3 arguments (enough for every implemented function).

**Parameters.** dt_abi 3320, dt_abi1 188 dense parameters; 102 and 27 layers. **Tests.** tests/output/func_date/test_dt_abi.py.
