# Files agent progress log (stage 8 groundwork: CSV, ZIP, DEFLATE, XML)

Owner of weights/files/ and network ids 448 to 511.

## 2026-11-06 16:04, reading
- Read AGENT_BRIEF, RULES, DOCUMENTATION, harness/FORMAT.md (file transfer region 0x201000: word 0 byte count, then one byte per word; io 2 file in, io 3 file out), control.md (64-word state, registers, calling convention), memory-map.md, primitives.md, kernel/commit.md (entry parser contract: A = (2, text handle), address register = cell, P1 = 0, return A, P1, STATUS).
- encodings/functions.md does not exist yet, so per the brief I start with subroutine networks using the control.md calling convention with explicit registers.

## 2026-11-06 16:05, plan
- The full stage 8 list (CSV in and out with cell commit, ZIP, CRC-32, DEFLATE inflate and deflate, XML tokenizer) is far more than one session of hand-typed weights. I start with the part every later piece depends on and that is pure RFC 4180 logic: a CSV byte scanner (id 448) that turns the file transfer bytes into a token stream (byte units, field end, row end, end of data). A second network (later) packs each field into a heap string and calls the entry parser through the kernel commit contract.
- Why a token stream first: it isolates the quoting state machine (the part Excel parity depends on) from cell commit, which depends on parse and kernel networks owned by others; it can be tested in isolation with hand-made byte fixtures.

## 2026-11-06 16:20, csv_scan (id 448)
- Wrote weights/files/csv_scan.wt by hand: 4 phases (read count, init, process byte, read next byte), 5 states (field start, unquoted, in quotes, quote seen, after CR). Transition table as 11 AND units gated by phase 2 and not-eof; outputs by big-M relu muxes. Note: weights/files/csv_scan.md.
- First run: 4 of 10 tests passed. Traced "a CRLF b" by forward pass: correct. Cause of the other failures: the test enters with garbage T0 = 77 and the init phase reset used M = 8 (T0 - 8 p1), which only clears T0 <= 8. Changed the p1 weight of R9 to -2^23. Two test expectations were my own counting errors (",\"\",\n" has two separators, not three; "1,2\n" makes 5 tokens), corrected by restating them by hand.
- Now 10 of 10 pass: simple CRLF rows, LF only, no final newline, quoted comma, doubled quote, quoted CRLF, empty and empty-quoted fields, literal quote in unquoted field, text after closing quote, lone CR, blank line, empty file, stale bytes after the data, register pass-through and return, step count (2 n + 3 style).
- Not done this session: field packer and commit (needs the ABI in encodings/functions.md, absent), CSV export, CRC-32, ZIP, DEFLATE, XML tokenizer.
## 2026-11-06 16:11, FILE_SCRATCH
- Coordinator: token buffer may not be EVAL_SCRATCH. No unassigned space exists; took 0x3B0000..0x3BFFFF from the unused VBA_STATE top (decision F2), edited memory-map.md rows and section 10.
- Next: field packer and commit. Design: csv_pack 449 (token loop, UTF-8 decode, unit packing, separators), hk_file 450 (copy of hk_commit with RET 451 so the recalc returns to me), csv_back 451 (reread HEAP_TOP, back to 449 PC 1), csv_commit 452 (string header, HEAP_TOP, parser call, CELL_SET call; a rejected field is stored as text). State in L0..L11 (preserved by parser, CELL_SET and the recalc chain); the caller's link goes on RET_STACK and the END token returns through RET (id 2).

## 2026-11-06 17:10, field packer and commit (ids 449 to 454)
- Wrote csv_imp 453 (entry: one block write spills LINK + L0..L11, RSP += 13), csv_back 451 (read HEAP_TOP, to 449 PC 1), csv_pack 449 (token loop with UTF-8 decoder, BOM drop, unit packing 3 per word, separators), csv_commit 452 (len, refcount, HEAP_TOP, parser call, CELL_SET call; rejected entries stored as text), hk_file 450 (hk_commit block retyped with RET 451 so the recalculation returns to me), csv_ret 454 (block consumer: restores L0..L11 and returns through the unpacked LINK).
- Note on hk_file: I first copied hk_commit.wt with sed; that is a string-replacement helper emitting weight rows (RULES rule 2 as the brief words it), so I deleted that output and retyped the file by hand.
- First run: every cell blank. Trace of "7\n": the byte was read but no unit appended; L6 (pos) was 498 = the caller's 506 - 8, so the p1 reset of pos used M = 8, too small for a caller's local. Same mistake as csv_scan's T0 reset. Changed the R12 p1 weight to -2^23.
- Then 6 of 6 pass: text, numbers, TRUE, blank field, space in text, locals and RSP restored with STATUS 0, a formula =B1*2 imported before B1 recalculates to 42 (dependencies recorded through hk_file), quoted comma, 7-unit string spanning 3 packed words, target offset C3, UTF-8 2- and 3-byte sequences, BOM dropped, 4-byte sequence -> U+FFFD (documented limit), rejected "=1+" stored as text.

## 2026-11-06 18:00, CSV export (ids 455 to 459)
- Wrote xp_imp, xp_scan (used range by a full slot pass, since the occupancy list is not maintained yet, kernel K-Q3), xp_cell (row and column loop with CELL_GET and dispatch), xp_str (quoting scan plus UTF-8 emission, 8 phases), xp_err (error texts as hand-computed packed words).
- Run 1: ValueError, xp_str emitted 63 words: pass-through slice 0 9 33 stopped one word short; fixed to 0 9 34. Run 2: infinite loop, the same cell exported again and again with writes at address 0: xp_cell put L5..L7 at words 46..48 instead of 45..47. Fixed the three assembly slices.
- Now 5 of 5 pass: grid of text, number, boolean; blanks inside the used range; quoting with doubled quotes and a comma; formula values (#DIV/0!, 6); UTF-8 2- and 3-byte units and a 10-unit string; empty sheet writes an empty file; return restores L0..L11 and RSP.
## 2026-11-06 16:34, XML tokenizer design (id 460)
- Byte state machine like csv_scan, 11 states (text, after <, tag name, in tag, attribute name, after =, value in double or single quotes, end tag name, after / in tag, skip <? ... > and <! ... >), 27 AND units. Tokens: byte, -1000 - b start tag whose name starts with b, -2000 - b attribute whose name starts with b, -3 value start, -4 tag end >, -5 empty tag end />, -6 end tag open, -9 end. First name character is folded into the marker so every input byte costs one token write at most.
- 2026-11-06 18:40: xml_tok written; 4 of 4 tests passed on the first run (attributes in both quote styles, nested elements with text, declaration skipped, empty tag with spaces around =, comment skipped, white space before > in an end tag, empty input).

## 2026-11-06 18:45, stopping point
- Done and tested: csv_scan 448, the import chain 449..454, the export chain 455..459, xml_tok 460. 26 tests in tests/output/files pass.
- Not done: CRC-32, ZIP reading, DEFLATE inflate, DEFLATE compression. Design notes for the next session: CRC-32 as a bitwise network (8 rounds of shift and conditional XOR with 0xEDB88320, the CRC held as 32 bit words in a FILE_SCRATCH block read and written each byte, or 4 bytes of a byte-table stamped by a generator network, rule 3); inflate as a bit reader (one byte per read, bit buffer in a register) plus Huffman decoding by canonical code tables built in FILE_SCRATCH (count per length, first code per length, symbols in order), one symbol per few steps; stored blocks first, then fixed, then dynamic. These are large hand-written networks and did not fit in this session.
