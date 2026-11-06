# Weight block notes: weights/ui/hc0, hc1, hc2, hc3, hcz (ids 133..137, heap string to buffer)

Hand-written. Log: log/ui-agent.md. Text heap layout: encodings/memory-map.md section 9.
| Id | Step | next |
|---|---|---|
| 133 hc0 | read length at handle T0 | 134 |
| 134 hc1 | T1 = n; read packed word at h + 2; T0 = h + 3; T3 = 0 | 135, or 137 if n = 0 |
| 135 hc2 | u = x0 if j = 0 else T2; write u mod 2^16 at P0; P0++, n--, T2 = floor(u/2^16), j++ | 137 if done, 136 if j was 2, else 135 |
| 136 hc3 | read next packed word, T0++, j = 0 | 135 |
| 137 hcz | write 0 at P0, return to (LR, LP) | LR |
**Derivation.** floor(u/2^16) = ROUND(u 2^-16 - (1/2 - 2^-17)) is exact because u 2^-16 has at most 16 fractional bits. The latch uses MUX_INT with M = 2^50, since u < 2^48 keeps every sum below 2^53.
**Parameters.** about 230 in total. **Steps.** n + ceil(n/3) + 2 (n units). **Tests.** test_heap_copy.
