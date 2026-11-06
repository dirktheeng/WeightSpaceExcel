# dt_coer (id 358): text-to-date coercion of date function arguments

Hand-written (log/func-date-agent.md session 2; decision FD-8). Sits between dt_abi's dispatch and the core: dt_abi now dispatches to 358 PC 0 with the core id in T9 and the core PC in T10.

| PC | Does | Next |
|---|---|---|
| 0 | first text argument among A (not for DATEVALUE, TIMEVALUE), B (only if n >= 1), C (not for DATEDIF): park A in AS AR1 and T0 in AC1; A = the text, T0 = 2; LR 358, LP = slot | 354 |
| 1, 2, 3 | slot LP = A (the coerced value or #VALUE!), A and T0 back from AS AR1 AC1; then as PC 0 | 354 or core |
| any, no text left | next = T9, PC = T10, LR 257, LP 0 | the core |

**Costs.** One step per date function call, plus (1 + parser) per text argument. **Preserve set.** Words 10, 11, 22..28, 30..63 pass; writes 0..9, 12..21, 29.

**Parameters.** 749 dense parameters, 53 layers. **Tests.** test_dv_abi.py, and every test_dt_abi.py case now runs through it.
