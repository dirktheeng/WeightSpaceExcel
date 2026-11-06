# Encoding: IO (input event words, how tests drive the engine, where results are observed)

Status: design, stage 1. Decision record: log/WORKLOG.md "2026-11-06 Stage 1: input event format and black-box test protocol (Q-G4)", decision D19. Related: harness/FORMAT.md (input events region, io 6), encodings/address.md (cell hashing), encodings/memory-map.md (zero page, cell store, text heap), encodings/value.md (TAG and PAY), encodings/glyph.md (UTF-16 code units), encodings/control.md (network ids, MODE).

## 1. Event words

The harness copies raw event words into the input events region on io 6: word 0x200000 = count, then up to 4095 event words, in order. The harness never looks inside them. One event is exactly one word, an exact integer below 2^52 (encodings/value.md V2):

    W = KIND * 2^48 + MODS * 2^40 + P

| Field | Bits | Range | Meaning |
|---|---|---|---|
| KIND | 48 to 51 | 1 to 15 | event kind (table below); 0 is never sent |
| MODS | 40 to 47 | 0 to 255 | modifier and lock state at the time of the event: 1 Shift, 2 Ctrl, 4 Alt, 8 Meta (Windows key), 16 Caps Lock on, 32 Num Lock on, 64 AltGr (64 is sent with Ctrl and Alt clear) |
| P | 0 to 39 | | payload, layout depends on KIND |

| KIND | Event | Payload P |
|---|---|---|
| 1 | KEY_DOWN | UNIT + 2^16 * VK |
| 2 | KEY_UP | UNIT + 2^16 * VK (UNIT is 0) |
| 3 | MOUSE_MOVE | X + 2^16 * Y + 2^32 * BUTTONS |
| 4 | MOUSE_DOWN | X + 2^16 * Y + 2^32 * BUTTON |
| 5 | MOUSE_UP | X + 2^16 * Y + 2^32 * BUTTON |
| 6 | WHEEL | X + 2^16 * Y + 2^32 * (NOTCHES + 128) |
| 7 | MOUSE_DOUBLE | X + 2^16 * Y + 2^32 * BUTTON (sent instead of the second MOUSE_DOWN of a double click) |
| 8 to 15 | reserved | |

**Keys.** VK is the Windows virtual key code (0 to 255): 0x08 Backspace, 0x09 Tab, 0x0D Enter, 0x1B Escape, 0x20 Space, 0x21 Page Up, 0x22 Page Down, 0x23 End, 0x24 Home, 0x25 to 0x28 Left, Up, Right, Down, 0x2E Delete, 0x30 to 0x39 digits, 0x41 to 0x5A letters, 0x70 to 0x7B F1 to F12, 0xE7 VK_PACKET (a code unit with no physical key). UNIT is the UTF-16 code unit the key press produces after the keyboard layout has applied Shift, Caps Lock and AltGr (the WM_CHAR value), or 0 if the press produces no character (arrows, function keys, any press with Ctrl or Alt held, except AltGr). A character outside the BMP is sent as two KEY_DOWN events with VK 0xE7, high surrogate first, each followed by its KEY_UP. Text that cannot be typed on the en-US layout (for example "é") is sent the same way, one VK 0xE7 event per code unit.

**Mouse.** X and Y are framebuffer pixel coordinates (0 to 1279, 0 to 799, encodings/glyph.md D17), origin top left. BUTTON is 1 left, 2 right, 4 middle; BUTTONS on MOUSE_MOVE is the set of held buttons (sum). NOTCHES is the signed wheel movement in detents, positive away from the user, clamped to -127 to 127.

**Unpacking.** A network unpacks with FLOOR on W * 2^-48 (KIND), then on the remainder * 2^-40 (MODS), then on P * 2^-16 and P * 2^-32; all scalings are exact powers of two and every field fits its bits, so the fields never overlap.

**Why UNIT travels with VK.** Excel itself receives both the key (WM_KEYDOWN) and the produced character (WM_CHAR). Supplying the character in the event moves keyboard layout knowledge out of the networks; the key-to-character network planned in encodings/glyph.md is then needed only for shortcut matching by VK, which uses VK and MODS directly. Typed text decoding is one field extraction.

## 2. How a test feeds input

Tests drive the engine only through the harness API:

1. Read the network manifest weights/MANIFEST.txt: lines `ID PATH` (id, then path relative to the repository root), any order, append only, `#` comments and blank lines ignored, duplicate ids fail. The list is built by id up to 512 entries, and unlisted ids get the TRAP path (id 1, or the entry ending in /trap.wt), per encodings/control.md section 5. The test only passes these paths to `Harness(networks=...)`; it never opens the listed files.
2. Encode the whole input script as event words (section 1) and pass it as `Harness(..., events=[...])`. The networks pull the words with io 6 whenever they choose to.
3. Call `run(0, zeros(65))` (BOOT, encodings/control.md section 5) with a `max_steps` safety bound.

**Typing a key** is KEY_DOWN followed by KEY_UP of the same VK. **Typing text** is one key per UTF-16 unit: letters use VK of the upper case letter with Shift in MODS when the unit is upper case (Caps Lock is never used by tests); digits and en-US punctuation use their en-US VK and Shift state; anything else uses VK 0xE7.

**Go to a cell** (Excel's Go To, Ctrl+G): KEY Ctrl+G (VK 0x47, MODS 2, UNIT 0), then the A1 address typed as text (for example `B12`), then Enter. The active cell becomes that cell.

**Enter a cell**: Go To the cell, type the raw cell text, press Enter. Entering an empty string means clearing: Go To the cell, then press Delete (VK 0x2E). Tests always use Go To before each entry, so they do not depend on where Enter moves the selection.

**Edits** (a case's `edits` list) are applied after all initial cells, each edit in order, with the same entry sequence. All events of a case are queued before the run starts.

**End of input.** When the main loop requests io 6 and receives count 0 while MODE is ready (1) and no recalculation is pending, it routes to HALT_OK (id 3). For stages 1 and 2 an empty queue therefore means "idle, halt". An interactive launcher later will need a waiting idle loop; that will be a new decision record and a different MODE, not a change to this word format.

## 3. Where results are observed

Output tests observe results by reading raw memory words after the run halts (`Harness.mem`), never weights and never anything in WEIGHT_STAGING (0x3C0000 to 0x3EFFFF), which can hold networks. Decoding raw memory is black-box observation of the documented layout:

- **Cell lookup.** For cell (SHEET 0, ROW, COL, NS 0): K = SHEET * 2^34 + ROW * 2^14 + COL; slot from the hash in encodings/address.md section 4; probe linearly (wrap at 2^16) until KEY = K + 1 (found) or KEY = 0 (absent, the cell is blank); tombstones (-1) are skipped.
- **Value.** TAG at slot word 1, PAY at slot word 2, decoded by encodings/value.md: 0 blank, 1 number (PAY), 2 text (string at handle PAY: length at word PAY, packed units from word PAY + 2, three units per word, c0 lowest), 3 boolean (PAY 0 or 1), 4 error (PAY = ERROR.TYPE code).
- **Circular reference.** CIRC_FLAG (zero page 0x12) is nonzero after a recalculation that met a cycle and holds K + 1 of the first cycle cell found. A test expecting `circular` checks that CIRC_FLAG is nonzero and that it names one of the listed cells; a test without `circular` checks CIRC_FLAG = 0.
- **Rejected entries.** REJECT_COUNT (zero page 0x14, taken from the stage 1 reserved range of encodings/memory-map.md section 3) counts entries the engine refused since boot. The engine increments it when Enter is pressed on text it cannot accept, discards the edit and leaves the cell unchanged. A test expecting `rejected` checks REJECT_COUNT = number of listed cells and the expected cell values; otherwise REJECT_COUNT = 0.
- **Fault.** FAULT (zero page 0x00) must be 0 after every run.

## 4. Multi-role words

Each event word holds KIND, MODS and payload in disjoint bit ranges with exact integer arithmetic. REJECT_COUNT has one role (a counter) and one writer (the cell entry network).
