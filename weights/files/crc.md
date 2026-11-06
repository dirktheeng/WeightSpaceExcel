# Weight block note: crc (id 461) and crcg (id 463)

Hand-written. Not generated (crcg writes a data table, not weights). Log: log/files-agent.md session 2. Tests: tests/output/files/test_crc.py (4 tests). Uses x32 (462, weights/files/x32.md).

## crc (461): CRC-32 of a byte run

**Computes.** The CRC-32 of ISO 3309 / ITU-T V.42 used by ZIP and zlib (reflected polynomial 0xEDB88320, initial register 0xFFFFFFFF, final complement) of the bytes at P0 .. N0 - 1, one byte per word.

**Calling convention.** next = 461, PC 0, A.PAY = CRC so far (0 to start; passing an earlier result continues it over the next chunk), P0 = start, N0 = end (exclusive), LR, LP. Returns A.PAY = CRC, STATUS 0, LR and LP restored. Clobbers P0, T1..T4 (T3, T4 hold the caller's link while x32 is used as a leaf). Needs CRC_TAB.

**Phases.** PC 0: T1 = 2^32 - 1 - A.PAY (complement), T3 = LR, T4 = LP, read P0. PC 1, P0 < N0: idx = (T1 mod 256) XOR byte (MOD2K block with k = 8 and an 8-level XOR chain of the x32 kind), T1 = floor(T1 / 256), T2 = 0, read CRC_TAB + idx, P0 += 1, call x32 with LR 461, LP 1; x32 makes T1 = T[idx] XOR T1 and reads the next byte. PC 1, P0 >= N0: A.PAY = 2^32 - 1 - T1, return to (T3, T4). This is the table form crc = T[(crc XOR b) and 255] XOR (crc >> 8).

**Gating.** Outputs are selected by mul products of gates [p0, go, done] with values (exact for any finite value, so caller garbage in T1, T3, T4 at entry cannot leak). The byte is clamped to [0, 255] by two relus first.

**Parameters.** 929 dense. **Steps.** 2 per byte + 2.

## crcg (463): CRC_TAB generator

**Computes.** CRC_TAB = 0x3BFF00 .. 0x3BFFFF (FILE_SCRATCH, sub-layout in weights/files/inflate.md): T[0] = 0, T[i] = T[H] XOR T[i - H] with H the highest power of two not above i. This holds because the table is linear over GF(2) in i. The eight basis values T[1], T[2], T[4], ..., T[128] were worked out by hand (log/files-agent.md session 2, one round per bit of the reflected algorithm): 0x77073096, 0xEE0E612C, 0x076DC419, 0x0EDB8832, 0x1DB71064, 0x3B6E20C8, 0x76DC4190, 0xEDB88320. They enter as telescoped differences D_k = T[2^k] - T[2^(k-1)] with s_k = [i >= 2^k], so B(i) = T[H] = sum s_k D_k and H = s_0 + sum_{k>=1} 2^(k-1) s_k, one dense row each.

**Calling convention.** next = 463, PC 0, LR, LP. Returns to (LR, LP). Clobbers T1..T5, P0. Run once before crc, the ZIP reader or the ZIP writer (they do not call it themselves).

**Phases.** PC 0: write T[0], i = 1. PC 1: read T[i - H], T1 = B(i), call x32 (LR 463, LP 2), or return when i = 256. PC 2: write T[i] = T1, i += 1. **Parameters.** 694 dense. **Steps.** 767 in all.

**Limits (both).** Bytes must be integers 0..255. **Multi-role weights.** None.
