# tx_case (id 314): UPPER / LOWER core

Hand-written, not generated. Log: log/func-text-agent.md; WORKLOG Stage 3 Text entry. Conventions: README.md.

**Computes** a new string with letters mapped: N0 = 0 UPPER (a..z, U+00E0..U+00FE except U+00F7 lose 32), N0 = 1 LOWER (A..Z, U+00C0..U+00DE except U+00D7 gain 32). Other units are copied. Clobbers P0, P1, N1, T1.

| PC | Step | Next |
|---|---|---|
| 0 | error: return; else read [h]; P0 = h + 2, P1 = HT + 2, T1 = HT | PC 1 |
| 1 | write [T1] = length; N1 = length | PC 2 |
| 2 | N1 <= 0: A = (2, T1), HT = P1, return; else read [P0] | PC 3 |
| 3 | write [P1] = mapped x0; P0, P1 += 1; N1 -= 3 | PC 2 |

**Blocks**: UNPACK3(x0) gives c0, c1, c2. Per unit a 12-step thermometer at 96.5, 122.5, 223.5, 246.5, 247.5, 254.5 (upper-able ranges as alternating signs) and 64.5, 90.5, 191.5, 214.5, 215.5, 222.5 (lower-able); dU_k = step(in-range_U - N0 - 0.5), dL_k = step(in-range_L + N0 - 1.5) (range AND mode in one row). w' = x0 + 32 sum_k 2^(16 k) (dL_k - dU_k), an exact integer row (R4). The value field is p1 x0 + p3 w' through a mul so the packed word, large in every phase, never enters a relu mux. MUX_INT relus select addresses (PAY, T1, P0, P1 by phase), A.PAY (T1 at the finish), P0, P1, T1 (set in PC 0), N1 and HT. N1 can go negative after the last word; PC 2 sees nz = 0 and finishes.

**Limits**: case mapping for Latin-1 only; U+00FF, U+00DF and letters beyond U+00FF (Greek, Cyrillic, Latin Extended) are not mapped yet (Excel maps them). The reference count word of the result is left 0.
