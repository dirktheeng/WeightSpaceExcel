# tx_char (id 317): CHAR / UNICHAR core

Hand-written, not generated. Log: log/func-text-agent.md; WORKLOG Stage 3 Text entry, decision T4. Conventions: README.md.

**Computes** a 1 or 2 unit string from a code. One step. Uses harness v2 block write: output length 67, words 64..66 are the payload [length, refcount 1, packed word]. mem_op is always 3 with K = 64 so the successor always takes 65 inputs; N = 3 only when the code is valid (value = 2^26 + 3 ok), N = 0 writes nothing.

**Blocks**: f = FLOOR(clamp(A.PAY)) as in tx_mid. A 39-row step bank on f: g1 (f >= 1), g256, s55 (f >= 55296), s57 (f >= 57344), two (f >= 65536), big (f >= 1114112), and t128 .. t160. Windows-1252: delta = sum_k t_k (d_k - d_(k-1)) with d_k = codepoint(k) - k for k = 128..159 (d = 0 outside); the row telescopes so a code k in 128..159 gets exactly d_k. Codepoints used: 80 20AC, 81 0081, 82 201A, 83 0192, 84 201E, 85 2026, 86 2020, 87 2021, 88 02C6, 89 2030, 8A 0160, 8B 2039, 8C 0152, 8D 008D, 8E 017D, 8F 008F, 90 0090, 91 2018, 92 2019, 93 201C, 94 201D, 95 2022, 96 2013, 97 2014, 98 02DC, 99 2122, 9A 0161, 9B 203A, 9C 0153, 9D 009D, 9E 017E, 9F 0178 (the five undefined positions map to themselves, as Excel does). delta is applied only in CHAR mode (mul by 1 - N0).
Surrogate pair: q = FLOOR(f / 1024 - 64) (exact scaling), hi = 55296 + q, lo = 56320 + (f - 65536 - 1024 q); word2 = hi + 2^16 lo = 65536 f - 67108863 q - 603924480 (expanded by hand; checked on U+1F600 = D83D DE00).
Validity: CHAR bad = f < 1 or f > 255 (#VALUE!); UNICHAR bad = f < 1 or f > 1114111 (#VALUE!), surrogate code point = #N/A. Word select by MUX_INT with M = 2^49 (words below 2^48).

**Limits**: argument must already be a number.
