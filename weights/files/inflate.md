# Weight block note: inflate (ids 466 to 488, with brd 464 and bz 465)

Hand-written. Not generated. Log: log/files-agent.md session 2. Tests: tests/output/files/test_inflate.py (7 tests), test_deflate.py and test_zip.py (round trips and ZIP parts).

**Computes.** RFC 1951 DEFLATE decoding of a raw stream: stored, fixed Huffman and dynamic Huffman blocks, BFINAL chaining, length and distance codes with extra bits, LZ77 copies with distances up to 32768 (the whole output is the window, so the 32 KB window rule holds without a ring buffer).

**Calling convention.** next = 466 (ifx), PC 0. P0 = compressed bytes (one per word), N0 = their count, P1 = output address (one byte per word), N1 = bit area, a multiple of 8, with room for 8 N0 + 16 words. LR, LP. Returns to (LR, LP) with A.TAG 1, A.PAY = bytes produced, STATUS 0 (ok), 2 (block type 3) or 3 (no Huffman code matched). Clobbers words 13 to 39 except 8, 9, 10, 11 (LR, LP, RSP, MODE preserved); L0..L23 untouched.

## FILE_SCRATCH sub-layout (decision F3 of this session, log/WORKLOG.md)

| Address | Words | Contents |
|---|---|---|
| 0x3BE000 | 4096 | deflate hash heads HEAD[h] (weights/files/deflate.md) |
| 0x3BF000 (LL) | 320 | code lengths: literal/length then distance (HLIT + HDIST) |
| 0x3BF140 (CLL) | 19 | code length code lengths |
| 0x3BF200 (TA) | 320 | literal/length table: cnt[0..15], offs[16..31], sym[32..319] |
| 0x3BF400 (TD) | 64 | distance table, same layout |
| 0x3BF480 (TC) | 64 | code length table, same layout |
| 0x3BF600 (LTAB) | 58 | (base, extra bits) for length symbols 257..285 |
| 0x3BF640 (DTAB) | 60 | (base, extra bits) for distance codes 0..29 |
| 0x3BFF00 | 256 | CRC_TAB (weights/files/crc.md) |

The rest of FILE_SCRATCH (0x3B0000 to 0x3BDFFF) is free for callers (CSV and XML token streams, inflate output and bit areas in the tests).

## Registers during inflate

w15 OUT0, w16 BFINAL, w17 TB (table being decoded), w18 HK (handler id after a symbol), w19 HM (0 literal/length, 1 distance), w20 KB and w21 KP (builder continuation), w22 LB (lengths), w23 NS (symbol count), w24 LEN, w25 DIST (P0 during expansion), w26 OUT, w27 HLIT (N0 = end during expansion), w28 BP (bit pointer), w29 S (loop index; expansion write pointer), w30 TL, w31 HDIST, w32 HCLEN then TOT, w33 PREV, w34 extra bits or RN, w35 base or RV, w36..39 brd and bz arguments.

## Networks

| Id | Name | Role | Params |
|---|---|---|---|
| 466 | ifx | entry (end pointer, OUT0, BFINAL 0, write pointer), then the byte read of the expansion loop | 280 |
| 467 | ifb | expansion: block write the 8 bits of a byte, least significant first; at the end go to ibe | 93 |
| 468 | itab | one block write of LTAB and DTAB (124 hand-typed table words from RFC 1951 3.2.5) | 264 |
| 469 | ihd2 | header bits consumer: BFINAL, dispatch on BTYPE; stored: BP = 8 ceil(BP / 8) by the magic-constant FLOOR | 355 |
| 470 | ibe | end of a block: return if BFINAL, else read the next 3 header bits | 127 |
| 471 | ist1 | stored LEN (NLEN is not checked) | 51 |
| 472 | stw | stored byte: 8 bits to a byte, write, next 8 bits through brd | 101 |
| 473 | ifl | fixed code lengths 8, 9, 7, 8 and 30 distance lengths 5 by step sums, one write per step | 89 |
| 474 | iset | builder starts (TA, TD, TC) and decode starts (TA with ilit, TC with iy5) | 423 |
| 475 | ibc | builder pass 1: cnt[L[s]] += 1 (3 steps per symbol) | 331 |
| 476 | ibo | offs[l] = cnt[1] + .. + cnt[l-1] in one block write (triangular 16 x 16 dense) | 290 |
| 477 | ibs | builder pass 2: sym[offs[l]++] = s (4 steps per coded symbol, 1 per unused) | 625 |
| 478 | hb | forwards cnt[1..15] with the state (K = 79) and block reads 15 bits | 16 |
| 479 | hdec | one-pass canonical decode (below) and the symbol read | 1,497 |
| 480 | ilit | literal write / end of block / length or distance symbol to its (base, extra) pair | 270 |
| 481 | xb | (base, extra) consumer, block reads 13 bits | 16 |
| 482 | xe | base + masked extra bits; length: decode a distance next; distance: start the copy | 296 |
| 483 | icp | copy loop, 2 steps per byte | 188 |
| 484 | iy1 | HLIT, HDIST, HCLEN; zero CLL by a 19-word block write | 71 |
| 485 | iy3 | 3-bit code length code lengths in the permuted order (ord(i) as a step sum) | 146 |
| 486 | iy5 | code length symbol 0..15 written, 16..18 read their extra bits | 256 |
| 487 | iy6 | repeat count and value for 16, 17, 18 | 182 |
| 488 | iy7 | repeat write loop | 168 |

Total 6,135 (plus brd 40 and bz 91). Counted by hand from the layer shapes (rows x cols + rows).

**hdec derivation (puff, RFC 1951 3.2.2).** For l = 1..15 with counts c_l and bits b_1..b_15 (b_1 the bit at BP, the first code bit): code_l = sum_{j<=l} 2^(l-j) b_j, first_l = sum_{j<l} 2^(l-j) c_j (first_1 = 0, first_{l+1} = 2 (first_l + c_l)), index_l = sum_{j<l} c_j. All three are linear, so d_l = first_l + c_l - code_l is one 15 x 30 dense (row l: weights 2^(l-j) on c_j and -2^(l-j) on b_j for j <= l), s_l = step(d_l - 0.5) = [code_l < first_l + c_l]. For a valid code no level before the code length can match with code_l < first_l (canonical property), so the first l with s_l = 1 is the code length: f_l = step(s_l - sum_{j<l} s_j - 0.5) (triangular dense). Symbol position = sum f_l e_l with e_l = index_l + code_l - first_l (second 15 x 30 dense: weights 1 - 2^(l-j) on c_j for j < l, 2^(l-j) on b_j), formed by one mul and a sum row; length = sum l f_l, found = sum f_l. All integers below 2^16, exact (R4).

**Steps.** Expansion 2 per input byte. Stored: 2 per byte. Literal: 4 (brd, hb, hdec, ilit). Match: 4 + xb + xe + 3 (distance decode) + ilit + xb + xe, then 2 per copied byte. Table builds: fixed about 2,500 (318 length writes, 318 x 3 counts, coded symbols x 4); dynamic about 3 x (HLIT + HDIST) + 4 per coded symbol plus the code length decode. Measured: "a" fixed 2,573 steps; 408-byte sheet XML from a dynamic stream about 3,800 steps (about 9 per output byte including the table build).

**Limits.** No check of NLEN, of over-subscribed or incomplete codes, of distances reaching before the output start or of a missing end of block (decoding then runs on whatever words follow the bit area; the caller should leave 16 zero words after it). Output size is bounded only by the caller's buffer. **Multi-role weights.** Registers w24..w35 change meaning between the expansion, builder, dynamic header and decode phases; the phases never overlap in time (each network's note lists which meaning it uses), which is the non-interference argument; covered by the dynamic-header tests that pass through all of them.
