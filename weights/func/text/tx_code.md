# tx_code (id 313): CODE / UNICODE core

Hand-written, not generated. Log: log/func-text-agent.md; WORKLOG Stage 3 Text entry. Conventions: README.md.

**Computes** the first UTF-16 unit of A: (1, mem[h + 2] mod 2^16); "" gives #VALUE! (4, 3); errors pass.

| PC | Step | Next |
|---|---|---|
| 0 | error: return; else read [h] | PC 1 |
| 1 | x0 = length; 0: A = #VALUE!, return; else read [h + 2] | PC 2 |
| 2 | A = (1, x0 mod 2^16) | (LR, LP) |

**Blocks**: thresholds q1, q2 (PC), TAG 3.5 / 4.5, z = step(0.5 - x0). Gates g0 = PC 0 and not error, g1 = PC 1 and length > 0, ez = PC 1 and length 0. MOD2K(x0, 16) by ROUND(x0 2^-16) and the FLOOR correction, c0 = x0 - 65536 FLOOR (exact, R4). c0 is gated by a mul with q2 so a garbage x0 in other phases cannot leak (V1 holds: c0 is finite for any finite x0). next = LR (1 - g) + 313 g, addr = PAY + 2 g1, PC = LP (1 - g) + g0 + 2 g1, A.TAG' = TAG + 2 ez - q2, A.PAY' = PAY (1 - ez - q2) + 3 ez + q2 c0.

**Limits**: UNICODE semantics (the unit itself). Excel's CODE returns the Windows-1252 code for the first character (CODE("€") = 128); the reverse of tx_char's table is not applied yet. A leading surrogate pair gives the high surrogate, where UNICODE gives the full code point. Both are open items for this core.
