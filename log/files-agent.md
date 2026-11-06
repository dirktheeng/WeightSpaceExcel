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
