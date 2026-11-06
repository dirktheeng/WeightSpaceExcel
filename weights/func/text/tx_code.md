# tx_code (id 313): CODE / UNICODE core

Hand-written, not generated. Log: log/func-text-agent.md (session 1, rewritten in session 2); WORKLOG Stage 3 Text entries. Conventions: README.md.

**Computes** from the first packed word of A: N0 = 0 CODE, the Windows-1252 code of the first unit (units 0..255 unchanged, the 27 code points that Windows-1252 places at 128..159 mapped back, e.g. U+20AC -> 128, U+2122 -> 153; any other unit above 255 -> 63, "?"); N0 = 1 UNICODE, the first code point (a high surrogate followed by a low surrogate combine to 65536 + 1024 (hi - 55296) + (lo - 56320) = 1024 hi + lo - 56613888). "" gives #VALUE!; errors pass.

| PC | Step | Next |
|---|---|---|
| 0 | error: return; else read [h] | PC 1 |
| 1 | x0 = length; 0: A = #VALUE!, return; else read [h + 2] | PC 2 |
| 2 | A = (1, result) | (LR, LP) |

**Blocks**: two FLOOR(x 2^-16) stages give c0, c1. A 48-step bank: c0 > 255, high-surrogate range, 43 thermometer thresholds around the 27 table entries (runs of consecutive code points share thresholds), low-surrogate range on c1. CODE = relu(c0 - 2^17 [c0 > 255]) + 63 [c0 > 255] + sum_k t_k (d_k - d_(k-1)) with d = code - 63 on the table (telescoped, so exactly one table entry or none contributes). UNICODE pair select by MUX_INT with M = 2^27 (the pair formula is below 2^27 for any two units). Mode select by MUX_INT with M = 2^27; the result is gated by a mul with q2.

**Limits**: the Windows-1252 mapping of U+0080..U+009F (which Windows maps to themselves) is assumed; Excel on other code pages differs. A lone surrogate gives its own value.
