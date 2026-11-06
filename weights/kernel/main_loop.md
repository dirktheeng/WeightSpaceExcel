# Weight block notes: main loop (ids 4, 5, 6, 8) and its register use

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decisions K1, K3, K4. Event format: encodings/io.md section 1. Files: main_poll.wt, main_count.wt, main_first.wt, ev_next.wt; the decoder is ev_decode.wt (note ev_decode.md), the Enter commit chain is commit.md.

**Main loop locals (callee-saved, so the cell store and parser never touch them).**

| Word | Name | Meaning |
|---|---|---|
| 40 | L0 i | index of the event being processed |
| 41 | L1 n | events in the current batch |
| 42 | L2 ROW | active cell row (0-based) |
| 43 | L3 COL | active cell column |
| 44 | L4 len | code units typed into the edit buffer |
| 45 | L5 gm | 1 while typing a Go To address (after Ctrl+G) |
| 46 | L6 acc | packed word being filled (c0 + c1 2^16 + c2 2^32) |
| 47 | L7 pos | next unit position in acc (0, 1, 2) |
| 48 | L8 waddr | heap address where acc is stored |
| 49 | L9 HS | header address of the string being typed (= HEAP_TOP when typing starts) |
| 50 | L10 gcol | Go To column accumulator (bijective base 26, A = 1) |
| 51 | L11 grow | Go To row accumulator (decimal, 1-based) |

Active sheet is always 0 (CUR_SHEET not read yet). The active cell is kept in registers only; renderers will need a mirror in the UI zero page (open item K-Q4).

**Phase table (one network per step, PC unused and kept 0).**

| Id | Step | next |
|---|---|---|
| 4 main_poll | io 6: harness copies up to 4095 queued events to 0x200000 | 5 |
| 5 main_count | read count word 0x200000 | 6 |
| 6 main_first | n = x0. n = 0: halt route; else L0 = 0, L1 = n, read 0x200001 | 3 (HALT_OK) or 7 |
| 7 ev_decode | act on event x0 (ev_decode.md) | 8, 9 or 16 |
| 8 ev_next | L0 += 1; if L0 < n read 0x200001 + L0 | 7, or 4 when the batch is done |

**Derivations.** main_first: c = step(n - 0.5); next = 3 + 4 c, mem_op = c, addr = 0x200001 c (one integer weight each). ev_next: c = step(n - i - 1.5) = [i + 1 < n]; addr = relu(i + 0x200002 - M (1 - c)), M = 2^24 (MUX_INT; i < 4096), so the idle address is 0 (rule A2); next = 4 + 3 c.

**Idle rule.** An empty batch (count 0) means "idle, halt" (encodings/io.md section 2). MODE stays 1 (BOOT sets it); no recalculation is pending in this stage, so the halt condition is just count = 0.

**Parameters.** main_poll 14, main_count 14, main_first 32, ev_next 52. Steps: 2 per event (decode + next), 3 per batch (poll, count, first).

**Limits.** No wait loop for interactive use (io.md: future MODE and decision record). **Multi-role weights.** None in these four.

**Tests.** tests/output/kernel/test_kernel.py main loop group, including test_long_queue_crosses_event_chunks (more than 4095 event words, so at least two batches).
