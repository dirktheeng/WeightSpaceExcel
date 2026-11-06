# Weight block note: ZIP reader (489 to 493, 495, 497) and ZIP writer (494, 496, 507 to 511)

Hand-written. Not generated. Log: log/files-agent.md session 2. Tests: tests/output/files/test_zip.py (7 tests).

## Reader

**Computes.** Finds a named part in a ZIP archive (APPNOTE 4.3: end of central directory, central directory headers, local header), decompresses it (method 8 through inflate, method 0 by copy) and checks its CRC-32.

**Calling convention.** next = 489 (zr0), PC 0. P0 = archive bytes (one per word, for example the file transfer region 0x201001), N0 = archive length, P1 = name bytes, N1 = name length, A.PAY = output address, B.PAY = bit scratch for inflate (multiple of 8), LR, LP, RSP. Returns to (LR, LP) with A.PAY = part length and STATUS 0 ok, 1 not found, 2 not a ZIP / bad header signature, 3 CRC mismatch, 4 unsupported method, 5 decompression failed. RSP balanced. Clobbers words 13 to 39. Needs CRC_TAB (crcg run once).

| Id | Name | Role | Params |
|---|---|---|---|
| 489 | zr0 | PC 0 read the 22 bytes before the end; PC 1 pop [LINK, CRC, out] after inflate or zcp; PC 2 compare the CRC from crc with the directory value and return | 566 |
| 490 | zr1 | EOCD signature 0x06054B50; entry count and directory offset; scans back one byte per step over an archive comment | 296 |
| 491 | zr3 | central directory header: method, CRC, sizes, name length, local header offset, next header; name length test | 1,007 |
| 492 | zr4 | name compare, 2 steps per byte; mismatch moves to the next header | 644 |
| 493 | zr6 | local header (signature 0x04034B50), data start = offset + 30 + name + extra; pushes the link, CRC and output address (block write of 3 at RSP) and calls inflate or zcp with LR = 489, LP 1 | 574 |
| 495 | zr8 | pops, unpacks the link (FLOOR as in csv_ret), calls crc with LR = 489, LP 2, or returns STATUS 5 | 247 |
| 497 | zcp | generic copy of N0 words from P0 to P1 with A.PAY = count (also used by deflate and the writer) | 459 |

Little-endian fields are single dense rows with weights 1, 256, 65536, 16777216 over the header bytes of a block read (exact integers). Signature and equality tests are IS_K pairs. Reader total 3,793.

## Writer

**Computes.** A ZIP archive of n parts, each deflated with fixed Huffman codes (method 8), with local headers, central directory and EOCD. Version needed 2.0, flags 0, time 0, date 0x0021 (1980-01-01), no extra fields or comments.

**Calling convention.** next = 507 (zwa), PC 0. P0 = entry table: n records of 8 words [name address, name length, data address, data length, 0, 0, 0, 0] (words 4..6 receive CRC, compressed size, local header offset), N0 = n (1..65535), P1 = output (one byte per word), N1 = bit scratch, LR, LP, RSP. Returns to (LR, LP) with A.PAY = archive length, STATUS 0, RSP balanced, L0..L7 restored (spilled with the link as one 9-word block). Clobbers words 13 to 39. Needs CRC_TAB.

| Id | Name | Role | Params |
|---|---|---|---|
| 507 | zwa | PC 0 spill and set L0 record, L1 left, L2 write position, L3 base, L4 count, L5 first record, L6 bits, L7 directory start; PC 1 EOCD (22 bytes) then restore through brd | 1,624 |
| 508 | zwb | dispatcher: next record for the local pass or the directory pass, or EOCD | 349 |
| 509 | zwc | record consumer: call crc (PC 0) or deflate to L2 + 30 + name length (PC 1) | 210 |
| 510 | zwd | return point of crc, deflate, zcp: stores CRC and compressed size in the record, advances L2, L0, L1 | 354 |
| 494 | zwl | 30-byte local header and the name copy | 866 |
| 496 | zwm | 46-byte central directory header and the name copy | 1,314 |
| 511 | zwe | restore L0..L7, return | 48 |

Header bytes come from chained MOD 256 blocks (several lanes per dense layer), and payloads are assembled by slices and concats of single bytes plus one dense row of constants, which avoids typing a payload matrix. Writer total 4,765.

**Steps.** Reader: 2 per comment byte scanned, 1 per directory header passed, 2 per name byte compared, then inflate (inflate.md) and crc (2 per output byte). Writer per part: crc (2 per byte), deflate (deflate.md), about 10 for headers, 2 per name byte twice; measured 2,005 steps for two parts of 8 and 270 bytes.

**Limits.** No ZIP64, no encryption, no data descriptors (bit 3), no multi-disk; the EOCD scan reads back over at most the archive (one step per byte); directory and local name lengths are assumed equal. Archive and part sizes must fit the caller's buffers. **Multi-role weights.** None; zr0 serves three call sites by PC (time-separated phases).
