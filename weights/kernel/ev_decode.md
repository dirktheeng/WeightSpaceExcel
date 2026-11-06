# Weight block notes: weights/kernel/ev_decode.wt (id 7, event decoder and dispatcher)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decision K3. Event format: encodings/io.md section 1. Registers: weights/kernel/main_loop.md.

**Computes.** One step per event word W in input word 0.

1. **Field extraction (v4 to v13).** Three FLOORs in parallel: f16 = floor(W 2^-16), f24 = floor(W 2^-24), f48 = floor(W 2^-48), each R1 (exact power-of-two scale, weights 2^-16, 2^-24, 2^-48 typed as exact decimals) then ROUND by C = 1.5 2^52 and the step correction (weights/poc/round_floor.md). Then VK = f16 - 256 f24 (since f24 = KIND 2^24 + MODS 2^16 exactly, VK < 256), UNIT = W - 65536 f16, KIND = f48. All integer rows, exact; W < 2^52 keeps every scaled value below 2^51.
2. **Thresholds (v15, v16).** 19 GE_K units: s0, s1 on KIND (1, 2); s2, s3 on VK (71, 72 = G); s4, s5 (13, 14 = Enter); s6, s7 (46, 47 = Delete); s8 UNIT >= 1; s9 UNIT >= 32 (printable); s10, s11 digits 48..57; s12, s13 upper case 65..90; s14, s15 lower case 97..122; s16 len >= 1; s17, s18 pos >= 1, >= 2. Equality indicators are differences of neighbours (kd = s0 - s1 etc).
3. **Outcomes (v18, v19).** Each is one step unit over a sum of indicators, threshold (number of conditions) - 0.5:

| Outcome | Condition | Action | next |
|---|---|---|---|
| O1 | KEY_DOWN, VK 71, UNIT 0 (Ctrl+G; io.md sends UNIT 0 when Ctrl is held) | gm = 1, gcol = grow = 0 | 8 |
| O2 | KEY_DOWN, VK 13, gm | ROW = grow - 1, COL = gcol - 1, gm = 0 | 8 |
| O3 | KEY_DOWN, VK 13, not gm, len > 0 | commit (commit.md) | 9 |
| O4 | KEY_DOWN, VK 13, not gm, len 0 | ROW += 1 | 8 |
| O5 | KEY_DOWN, VK 46, not gm | CELL_SET blank at the active cell, LR = 8 | 16 |
| O6L | KEY_DOWN, UNIT letter, gm | gcol = 26 gcol + UNIT - 64 (- 32 if lower case) | 8 |
| O6D | KEY_DOWN, UNIT digit, gm | grow = 10 grow + UNIT - 48 | 8 |
| O7 | KEY_DOWN, UNIT >= 32, not gm | append UNIT to the edit buffer (write acc') | 8 |
| O7p2 | O7 and pos = 2 | also start the next packed word | (with O7) |
| none | KEY_UP, mouse, other keys, control units | nothing | 8 |

4. **Selects (v21, v22).** relu MUX_INT with M = 2^24 (all selected integers below 2^24): r0 addr = waddr on O7; r1..r3 = UNIT gated by pos one-hot; r4/r5 new or kept gcol (reset on O1); r6/r7 grow; r8..r11 ROW, COL from Go To on O2; r12 = O1 AND gm.
5. **Packing (v24, v25).** d = r1 + 2^16 r2 + 2^32 r3 = UNIT 2^(16 pos) (integer row); acc' = acc + d. A mul layer forms O7 d and O7p2 acc' (acc' can reach 2^48, beyond big-M range).
6. **Output rows (v27).** next = 8 + O3 + 8 O5; mem_op = 2 O7; addr = r0; value = acc + d (value is ignored by the harness unless mem_op = 2); LR = 8, LP = 0, A = (0, 0), AS = 0, AR1 = L2, AC1 = L3, P1 = 0, T1 = 1 are set unconditionally: they are the CELL_SET call arguments for O5 and are caller-saved scratch for every other outcome, so setting them always costs nothing and harms nothing. Locals: L2 = r8 + r9 + O4; L3 = r10 + r11; L4 = len + O7; L5 = gm + O1 - O2 - (O1 AND gm); L6 = acc + O7 d - O7p2 acc'; L7 = pos + O7 - 3 O7p2; L8 = waddr + O7p2; L10 = r4 + r5; L11 = r6 + r7.

**Parameters.** 3585 (mostly zeros of the gathered dense layers). Layers: 50 values, 9 dense. Steps: 1.

**Limits.** Backspace, Escape, arrows, Tab and editing keys are ignored (no in-place edit, no cancel). Typing does not set MODE 2. Go To accepts only A1 addresses without $ or sheet names; a Go To with no digits gives ROW 0 (relu clamps -1). More than 4 Go To letters can exceed the M range (beyond XFD anyway). Any KEY_DOWN with a unit >= 32 is text, including VK_PACKET units and surrogates, which are stored as UTF-16 code units as typed.

**Multi-role weights.** (a) The value word holds acc' on every step, but is meaningful only when mem_op = 2 (O7); no other outcome writes. (b) Words 8, 13, 14, 19 to 21, 26, 30 are the CELL_SET arguments on O5 and dead scratch otherwise (caller-saved temporaries by encodings/control.md section 2). Crosstalk: test_delete_clears_cell and test_enter_moves_down_and_typing_continues mix O5 with O7 and O3 in one run.
