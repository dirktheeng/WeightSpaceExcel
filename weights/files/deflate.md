# Weight block note: deflate (ids 498 to 506)

Hand-written. Not generated. Log: log/files-agent.md session 2. Tests: tests/output/files/test_deflate.py (4 tests) and the ZIP writer tests.

**Computes.** RFC 1951 compression of the bytes at P0 .. P0 + N0 - 1 (one per word) into a raw DEFLATE stream at P1 (one byte per word). Mode B.PAY = 0: one stored block (N0 <= 65535). Mode 1: one final fixed Huffman block with greedy LZ77 matching through a hash of the next 3 bytes (no chains, no lazy matching).

**Calling convention.** next = 499 (dfa), PC 0, P0, N0, P1, N1 = bit area (multiple of 8, 9 bits per input byte at most plus 16), B.PAY = mode, LR, LP. Returns to (LR, LP) with A.PAY = compressed byte count, STATUS 0. Clobbers words 13 to 39 (the link is kept in w22, w23); L0..L23 untouched. Uses HEAD (0x3BE000, 4096 words, weights/files/inflate.md layout), zcp (497) in stored mode, bz (465), brd (464).

**Registers.** w15 BB (bit area base), w17..w21 emitter arguments EV, EN, EM, EK, EP, w22 LR, w23 LP, w28 BP, w29 i, w30 b0, w31 h, w32 dist, w33 l (match length), w34 x (compare byte).

| Id | Name | Role | Params |
|---|---|---|---|
| 498 | dzb | bit emitter: EN (0..13) bits of EV at BP, MSB first (EM 1, Huffman codes) or LSB first (EM 0, extra bits and header fields); one 13-bit top-down decomposition of W = EV 2^(13 - EN) (MSB) or EV (LSB), payload word j = EM t(12 - j) + (1 - EM) t(j) by a mul mux | 555 |
| 499 | dfa | entry; stored header [1, LEN lo, LEN hi, NLEN lo, NLEN hi] (MOD 256) and copy; fixed: zero HEAD, header bits 1, 1, 0 | 974 |
| 500 | df2 | loop head: read 3 bytes at i, or emit end of block (7 zero bits) | 69 |
| 501 | df3 | h = (b0 + 32 b1 + 1024 b2) mod 4096, read HEAD[h] | 46 |
| 502 | df4 | HEAD[h] = i + 1; candidate valid if HEAD was set, i + 3 <= N0 and dist <= 32768; else literal | 205 |
| 503 | df5 | match length, 2 steps per byte, up to 258 and the input end; length < 3 gives a literal | 741 |
| 504 | df6 | length code (257 + c: 7 bits c + 1 if c <= 22, else 8 bits c + 169), length extra, distance code (5 bits), distance extra; c and the bases from step sums over the RFC 1951 3.2.5 bases | 909 |
| 505 | dpk | pad to a byte, A.PAY = (BP - BB) / 8, start packing | 94 |
| 506 | dpw | pack 8 bits into a byte, 2 steps per output byte | 204 |

Total 3,797, counted by hand from the layer shapes.

**Fixed codes (RFC 1951 3.2.6).** Literal b < 144: 48 + b in 8 bits; b >= 144: 256 + b in 9 bits (400 + b - 144); lengths 257..279: sym - 256 in 7 bits; 280..285: sym - 88 in 8 bits; distances: the 5-bit code. With c = sym - 257, the 8-bit case is exactly t_23 = [l >= 115], so EN = 7 + t_23 and EV = c + 1 + 168 t_23.

**Steps.** Literal 4 (df2, df3, df4, dzb); match of length l: 4 + 2 l (compare) + 8 (four emits); packing 2 per output byte; stored 2 per byte + 1; fixed setup 66 (HEAD zeroing) + 2. Measured: "abcabcabc" 119 steps, 460 bytes of repeated XML 1,128 steps.

**Limits.** One block, so the fixed mode output is not split; stored mode supports at most 65535 bytes; hash positions skipped inside a match are not inserted (worse ratio, same correctness); bytes must be 0..255. **Multi-role weights.** None beyond the register reuse documented above (time-separated).
