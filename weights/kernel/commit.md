# Weight block notes: Enter commit chain (ids 9 to 15), parse_stub (27), rej_rd (28), rej_wr (29)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decisions K3 and K5. Files: c_len.wt, c_rc.wt, c_top.wt, c_parse.wt, c_set.wt, c_done_rd.wt, c_done.wt, parse_stub.wt, rej_rd.wt, rej_wr.wt.

**Edit buffer = the string being built.** Typed units are packed straight into a text heap record (encodings/memory-map.md section 9) at HS = L9: ev_decode writes the packed word acc at L8 = HS + 2 + floor(len / 3) on every keystroke. On Enter the header is completed, so no copy is needed.

| Id | Step | next |
|---|---|---|
| 9 c_len | write len (L4) at HS | 10 |
| 10 c_rc | write reference count 1 at HS + 1 | 11 |
| 11 c_top | HEAP_TOP = L8 + [pos > 0] (first word after the string) | 12 |
| 12 c_parse | call entry parser: A = (2, HS), address = (0, L2, L3), P1 = 0, LR = 13, LP = 0 | parser id (27) |
| 27 parse_stub | return STATUS 0, A and P1 unchanged (text constant) | LR |
| 13 c_set | ok = [STATUS == 0]: call CELL_SET (T1 = 1, address (0, L2, L3), A, P1 from the parser, LR = 14); else 28 | 16 or 28 |
| 28 rej_rd | read REJECT_COUNT (0x14) | 29 |
| 29 rej_wr | write count + 1 | 14 |
| 14 c_done_rd | read HEAP_TOP (the parser may have allocated) | 15 |
| 15 c_done | L9 = top, L8 = top + 2, L4 = L6 = L7 = 0, L2 += 1 (Enter moves down) | 8 |

**Parser contract (for weights/parse).** Called with next = parser id, PC 0, LR = 13, LP = 0, A = (TAG 2, PAY handle of the typed text), address register = target cell (sheet 0), P1 = 0. Return to (LR, LP) with A = value to store (constants parsed: number, boolean, error, or text), P1 = formula record address (0 for constants) and STATUS = 0 accepted, nonzero rejected. Locals L0..L23 must be preserved (callee-saved). The parser may move HEAP_TOP. To install the real parser change the single bias 27 in c_parse.wt (v4, first bias) to its id.

**Derivations.** c_top: g = step(pos - 0.5); value = waddr + g. c_set: ok = 1 - step(S - 0.5) - step(-S - 0.5) (IS_K at 0), next = 28 - 12 ok. Everything else is CONST biases, one-weight copies and PASS.

**Parameters.** c_len 21, c_rc 14, c_top 31, c_parse 68, c_set 63, c_done_rd 14, c_done 39, parse_stub 27, rej_rd 14, rej_wr 14. Steps for one Enter commit of a new cell: 17 (6 chain + 1 stub + 9 CELL_SET + 2 finish); of an existing cell: 14.

**Limits.** Every entry is stored as text until the parser exists (numbers, TRUE, formulas stay text). Rejected entries leave their string in the heap (no reclamation, Q-M2). **Multi-role weights.** None.

**Change 2026-11-06 (parse agent, authorized by the coordinator).** c_parse.wt v4 first bias changed from 27 (parse_stub) to 78 (weights/parse/spill.wt, the real entry parser's entry network). parse_stub stays in the manifest but is no longer called. Log: log/parse-agent.md and log/WORKLOG.md decision P5.
