# String building (ids 324 to 329): tx_cp, tx_cpf, tx_f1, tx_cc, tx_rp, tx_rl

Hand-written, not generated. Log: log/func-text-agent.md session 2; WORKLOG decision T6.

## tx_cp (324): unit copier with a filter
One source unit per step appended to the output being built; the output word ACC is rewritten at WA on every emitting step (as ev_fmt_emit does), so there is no separate flush. Registers in the file header. UNPACK of the current source word: rest = FLOOR(srcw 2^-16), u = srcw - 2^16 rest (srcw = x0 in the load phase, SW otherwise, chosen by a mul gate). Filters: 0 copy; 1 CLEAN (drops units 0..31); 2 TRIM (state st: 0 nothing emitted, 1 last emitted non-space, 2 one space pending; a pending space is emitted on its own step before the next non-space, which is not consumed in that step); 3 PROPER (st = previous unit was a letter; letters = A..Z, a..z, U+00C0..U+00D6, U+00D8..U+00F6, U+00F8..U+00FF; upper-casing a..z and U+00E0..U+00FE except U+00F7, lower-casing A..Z and U+00C0..U+00DE except U+00D7). All conditions are AND rows of 0/1 bits (sum minus k - 0.5). The emitted unit is placed at POS by three relus with M = 2^17, 2^33, 2^49 (exact integers). Skip count SK (N0) consumes units without emitting. Cost: 4 steps per 3 units (one read, three unit steps), plus one step per pending TRIM space. Params 1812.
## tx_cpf (325)
One block write of [LEN, 1] at OH, A = (2, OH), HT past the last word, -> tx_fin. Params 83.
## tx_f1 (326): CLEAN / TRIM / PROPER
Reads the length, one copier piece over the whole string. Params 189.
## tx_cc (327): CONCAT, CONCATENATE (N0 0), TEXTJOIN (N0 1)
Walks the converted arguments on the operand stack (idx from 1, or 3 for TEXTJOIN), reading tag, pay and length (3 steps per argument), returns the first error, and appends a delimiter piece before every argument after the first emitted one (TEXTJOIN); ignore_empty skips empty arguments. Params 3263. Limit: CONCAT and TEXTJOIN over ranges are not supported yet (range arguments give #VALUE!).
## tx_rp (328): REPT
count = TRUNC, #VALUE! for count < 0 or L count > 32767 (Excel's limit), then count copier pieces. Params 928.
## tx_rl (329): REPLACE
Three pieces: old[0 : min(s - 1, L)], new, old with skip min(s - 1 + k, L). #VALUE! for s < 1 or k < 0. Params 1618.
