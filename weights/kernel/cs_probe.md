# Weight block notes: weights/kernel/cs_probe.wt (id 17, linear probe)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decision K2.

**Computes.** Input word 0 = key word k just read at slot P0. T0 = K + 1, T1 = mode. Indicators (all exact integer tests, IS_K form): f = [k == T0], e = [k == 0], w = [P0 + 8 >= 0x90000] (wrap), o = 1 - f - e (another key or a tombstone). AND gates by step: fm = f T1, em = e T1, ow = o w; f0 = f - fm, e0 = e - em.

| Outcome | Step does | next |
|---|---|---|
| f0 found, get | read TAG at P0 + 1 | 18 cs_ltag |
| fm found, set | write A.TAG at P0 + 1 | 23 cs_wpay |
| em empty, set | write KEY = T0 at P0 | 20 cs_cntr |
| e0 empty, get | STATUS 1, A = (0, 0), PC = LP | LR |
| o other key | P0 = P0 + 8 - 2^19 ow, read key at new P0 | 17 (self) |

**Field rows (linear in indicators).** next = 17 + f + 5 fm - 17 e + 20 em + rN; mem_op = 1 + fm + 2 em - e; addr = rA - 7 f - 8 e + 8 - 524288 ow; value = fm TAG + em T0; STATUS = e - em; P0' = P0 + 8 - 8 f - 8 e - 524288 ow. Each was checked against all five outcomes by hand (log/kernel-agent.md).

**Selects.** rA = relu(P0 - M e0), rN = relu(LR - M (1 - e0)), rP = relu(LP - M (1 - e0)) with M = 2^23 (MUX_INT, D14; P0 < 2^20, LR, LP < 2^16). The value word and the A clear use a mul layer (MUX for doubles): T0 is up to 2^50 and PAY is any double, beyond the big-M range.

**Parameters.** 482. Steps: 1 per probe.

**Limits.** Tombstones (-1) are skipped but not reused for inserts (nothing deletes yet). No probe count limit: a completely full table would loop forever (fault 4 not yet raised; open item K-Q2). Occupancy list (NEXTOCC, sheet occupancy head) is not maintained yet (K-Q3).

**Multi-role weights.** The value word carries A.TAG on fm and the key on em; the two products are gated by exclusive indicators, so at most one is nonzero (exclusive gating). Crosstalk: test_overwrite_keeps_count and test_set_then_get_roundtrip exercise both.
