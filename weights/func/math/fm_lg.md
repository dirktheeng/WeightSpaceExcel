# Weight block note: fm_lg (id 273)

Hand-written. Not generated. Log: log/func-math-agent.md (2026-11-06).

**Computes.** LOG(x, base) = LN(x) / LN(base), base missing (tag 8) = 10. Three phases: PC 0 coercion, first error (A, B), x <= 0 or base <= 0 -> #NUM!, base = 1 -> #DIV/0!, else LN(base) via 268 (T0 = 1) returning to PC 1; PC 1 stores LN(base) in word 17 and computes LN(x) the same way, returning to PC 2; PC 2 sends LN(x) / word 17 to fm_dv1 (gQ = 1) with the link (word 25, LR 2^16 + LP) unpacked by FLOOR into LR, LP, so fm_dv1 returns to the original caller. x is kept in word 28.

**Limits.** Two roundings in the logs and one in the division: LOG(8, 2) = 3 exactly here; other exact cases may be one ulp off (inside 15 digits). **Parameters.** Not tallied yet. Steps: 9. **Multi-role weights.** Words 14, 17, 25, 28 hold phase-dependent values selected by phase gates p0, p1, p2 (exclusive). **Tests.** test_log (16 cases), all pass.
