# weights/prim/hash.wt: HASH (cell store address)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 2". Spec: encodings/address.md section 4.

**Computes.** SHEET = AS, ROW = AR1, COL = AC1, NS = T0, FIELD = T1 (inputs). T0 = slot = t mod 2^16 with t = 40503 ROW + 65599 COL + 1000003 SHEET + 7919 NS; T1 = CELL_BASE + 8 slot + FIELD, CELL_BASE = 0x010000 = 65536 (encodings/memory-map.md).

**v4 (dense 1x5).** t; integer weights and fields, t < 1.1e11, exact (R4). **v5..v8.** MOD2K's FLOOR of t 2^-16 (mod2k.md). **v12 (dense 2x9).** slot = t - 65536 (r - g); addr = 65536 + 8 t - 524288 (r - g) + FIELD. All integers below 2^40, exact.

**Limits.** Field ranges of encodings/address.md section 1. Probing (slot + 1 with wrap) is the caller's. Cost: 1 step unit, 39 parameters, 12 layers.
**Multi-role weights.** None (T0 and T1 are inputs and then outputs; the input values are consumed before the outputs are formed in the same pass, and both belong to the callee during a call per encodings/control.md).
**Tests.** test_hash (7 cases incl. the last cell XFD1048576, slot 8586, worked by hand: 40503 * 1048575 = -40503 mod 2^16 = 25033, 63 * 16383 mod 2^16 = 49089, sum mod 2^16 = 8586): pass.
