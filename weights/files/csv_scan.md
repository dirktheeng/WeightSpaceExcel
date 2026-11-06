# Weight block note: csv_scan (id 448)

Hand-written. Not generated. Log: log/files-agent.md 2026-11-06; decision F1 in log/WORKLOG.md. Tests: tests/output/files/test_csv_scan.py (10 pass).

**What it computes.** A CSV scanner that reads the bytes of the file transfer region (harness/FORMAT.md: 0x201000 = byte count, then one byte per word, as io 2 leaves it) and writes a token stream starting at P1: a byte value 0..255 for each character of a field, -1 field end (comma), -2 row end, -3 end of data. Quoting follows RFC 4180 plus Excel's lenient reading. A later network packs each field into a heap string and hands it to the entry parser (weights/kernel/commit.md contract); this network does none of that.

**Calling convention** (encodings/control.md section 4). Call with next = 448, PC = 0, LR, LP, P1 = token buffer address (proposed: EVAL_SCRATCH 0x0B0000, free while a file loads). Returns to (LR, LP) with STATUS = 0, P1 = word after the -3 token. Clobbers P0 (byte pointer), N0 (end address), T0 (state). Everything else passes through (no locals used, so no spill). The caller's input word 0 at entry should be below 2^40 (it feeds a gated term in R8).

**Phases.**

| PC | Step | Next PC |
|---|---|---|
| 0 | read byte count at 0x201000 | 1 |
| 1 | N0 = count + 0x201001, P0 = 0x201001, T0 = 0, read 0x201001 | 2 |
| 2 | byte b (input word 0) at P0: if P0 >= N0 write -3 at P1 and return; else classify, set T0, P0 += 1, and either write a token at P1 (P1 += 1) or read the next byte | 3 if written, 2 if read, LP on return |
| 3 | read byte at P0 | 2 |

**State T0.** 0 field start, 1 unquoted field, 2 inside quotes, 3 quote seen inside quotes, 4 just after CR (outside quotes).

| State | `"` | `,` | LF | CR | other |
|---|---|---|---|---|---|
| 0 | -> 2 | FE, 0 | RE, 0 | RE, 4 | byte, 1 |
| 1 | byte, 1 | FE, 0 | RE, 0 | RE, 4 | byte, 1 |
| 2 | -> 3 | byte, 2 | byte, 2 | byte, 2 | byte, 2 |
| 3 | byte (a doubled quote), 2 | FE, 0 | RE, 0 | RE, 4 | byte, 1 |
| 4 | -> 2 | FE, 0 | nothing, 0 (CRLF) | RE, 4 | byte, 1 |

So a lone CR, a lone LF and CRLF each end a row; quotes not at the start of a field are literal (`ab"c` is `ab"c`); text after a closing quote is appended (`"ab"cd` is `abcd`); `""` is an empty field. At end of data the scanner writes -3 whatever the state, so the consumer closes the last row unless the previous token was -2 (an unterminated quoted field keeps what it has read, as Excel does).

**Derivation, layer by layer.**
- v1..v7: PASS, compact u = [b, PC, T0, P0, P1, N0].
- v8, v9: ONEHOT by IS_K pairs (primitives.md) for PC 0..3, T0 0..4 and b in {34 `"`, 44 `,`, 10 LF, 13 CR}; plus eof = step(P0 - N0 + 0.5), i.e. P0 >= N0 (integers, R4).
- v10: indicators as differences of the pairs; row 13 copies eof.
- v11, v12: the transition table as AND units step(sum - k - 0.5). Every unit also has + p2 - 1 - eof, so it fires only in phase 2 and never at end of data. "other" = 1 - Q - C - LF - CR is folded in (g4 bias -0.5 = 1 - 0.5 - 1). Units: g1 FE; g2 RE via CR; g3 RE via LF not after CR; g3b LF -> state 0; g4 other outside quotes; g5 quote in state 1 or 3 (emit 34); g6 non-quote inside quotes; g7 quote in state 1; g8 quote in states 0, 3, 4 (-> 2); g9 quote inside quotes (-> 3); eof2 = eof and p2. p0..p3 copied (step of a 0/1 value is itself).
  emit FE = g1, emit RE = g2 + g3, emit byte = g4 + g5 + g6 (at most one unit fires: the rows partition (state, class)); next state = g4 + g7 + 2 (g6 + g8) + 3 g9 + 4 g2.
- v16, v17: MUX_INT terms relu(a - M (1 - g)) with M = 2^16 for LR and LP, 2^23 for addresses and the T0 reset, 256 for the byte, 2^40 for count + 0x201001 (the caller's word 0 at entry is unknown). R3 = P0 + 1 when p2 and no write (read the next byte), R4 = P1 when writing.
- v19 (D): output rows. next = 448 - 448 eof2 + R0; mem_op = 1 + write (write = emit + eof2); addr = 0x201000 p0 + 0x201001 p1 + R2 + R3 + R4; value = R5 - FE - 2 RE - 3 eof2; PC = p0 + 2 (p1 + p2 + p3) + emit - 2 eof2 + R1; P0 = R6 + p2 + 0x201001 p1; P1 = P1 + write; N0 = R7 + R8; T0 = R9 + next state; STATUS = 0. All rows integer (R4), exact.
- v20..v34: PASS assembly of the 64 words.

**Parameters.** 1,488 dense (v8 189, v10 392, v11 225, v16 240, v19 442). **Steps.** 2 at entry, 1 per byte that writes nothing (opening and closing quotes, the LF of CRLF), 2 per byte that writes a token, 1 for the end token: about 2 n + 3 for n bytes.

**Limits.** Bytes are passed through unchanged: UTF-8 (and a UTF-8 byte order mark) is not decoded yet, so non-ASCII text must be decoded by the field packer (planned). A CRLF inside quotes is kept as the two bytes 13, 10; Excel's exact treatment of the CR there is unverified (open question Q-F1). Comma only (no locale list separator, no `sep=` line). Region size 2^20 bytes. **Multi-role weights.** None: each unit has one role; the phase and eof gating makes all phase-2 units zero in the other phases.
