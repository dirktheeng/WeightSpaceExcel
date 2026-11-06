# Encoding: MEMORY MAP (network-defined layout)

Status: design, stage 1. Decision records: log/WORKLOG.md "2026-11-06 Stage 1: shared encodings design", decisions D4 (hashed cell store), D8 (memory map), D9 (packed text). Related: encodings/address.md (cell hashing), encodings/value.md (records holding values), encodings/control.md (zero page use, return stack), encodings/glyph.md (framebuffer).

All addresses are word addresses. Total memory is 0x400000 words (harness MEM_SIZE). Every layout below is a convention kept by networks; the harness knows only its own designated regions.

## 1. Harness regions (never used for network data)

| Region | Range | Use |
|---|---|---|
| framebuffer | 0x100000 to 0x1FFFFF | pixels (encodings/glyph.md) |
| input events | 0x200000 to 0x200FFF | word 0 count, then raw event words |
| file transfer | 0x201000 to 0x300FFF | word 0 byte count, then one byte per word |
| clock | 0x301000 | seconds since epoch, written on io 4 |
| entropy | 0x301001 to 0x301040 | 64 random bytes, written on io 5 |

The harness overwrites these on I/O requests, so networks treat them as volatile: read what they need into their own regions before issuing the next request of the same kind. 0x301041 to 0x301FFF is left unused as a guard so no table straddles the entropy block.

**Block operations (harness v2, decision H2).** mem_op 3 writes a run of N consecutive words starting at addr and mem_op 4 reads such a run into the next input (harness/FORMAT.md, encodings/control.md section 1). The harness checks only that the run lies inside 0 to 0x3FFFFF; it does not know the regions below, so a run that crosses a region boundary is the writing network's error, exactly as for a single write. Intended uses: framebuffer scanlines (a 1280-pixel row of the 1280 x 800 framebuffer is one block write at 0x100000 + 1280 y), register spills to RET_STACK, copying strings and token streams, and writing memory-form networks into WEIGHT_STAGING. Runs are limited to 2^20 - 1 words by the field encoding and in practice by the payload height of the writing network.

## 2. Network regions

Free memory is 0x000000 to 0x0FFFFF (1,048,576 words) and 0x302000 to 0x3FFFFF (1,040,384 words). About 2.09 million words in all, which is the binding resource for workbook size (open question Q-M1).

| Name | Range | Words | Contents |
|---|---|---|---|
| ZERO_PAGE | 0x000000 to 0x0000FF | 256 | global variables (section 3) |
| RET_STACK | 0x000100 to 0x000FFF | 3840 | packed return links (encodings/control.md) |
| OPER_STACK | 0x001000 to 0x001FFF | 4096 | evaluator operand stack, 2 words per value (TAG, PAY) |
| PARSE_STACK | 0x002000 to 0x002FFF | 4096 | parser operator stack (1 word per entry: opcode or paren marker with argument count) and lexer scratch |
| WORK_STACK | 0x003000 to 0x003FFF | 4096 | recalculation depth-first stack (slot indices), also reused by sort and search passes |
| SHEET_TABLE | 0x004000 to 0x004FFF | 4096 | 256 sheet records of 16 words (section 5) |
| NAME_TABLE | 0x005000 to 0x006FFF | 8192 | defined names: 1024 records of 8 words [name handle, scope sheet + 1 or 0, formula record pointer, flags, hidden, comment handle, 2 spare] |
| FUNC_TABLE | 0x007000 to 0x007FFF | 4096 | function dispatch: 0x7000 + fid = network id implementing fid; 0x7400 + j, 0x7800 + j, 0x7C00 + j = name directory entry j (K1, K2, fid + 1024 flags); layout in encodings/functions.md section 3 (decision F3) |
| FORMAT_STORE | 0x008000 to 0x00FFFF | 32768 | 2048 style records of 16 words (section 7) |
| CELL_STORE | 0x010000 to 0x08FFFF | 524288 | hash table, 2^16 slots of 8 words (section 4) |
| FORMULA_STORE | 0x090000 to 0x0AFFFF | 131072 | formula records and RPN token streams (section 6) |
| EVAL_SCRATCH | 0x0B0000 to 0x0BFFFF | 65536 | reference, array and lambda records made during evaluation; reset by bump pointer after each top-level evaluation, except spilled arrays which are copied into cells |
| DEP_POOL | 0x0C0000 to 0x0DFFFF | 131072 | dependency edge nodes (section 8) |
| CALC_CHAIN | 0x0E0000 to 0x0EFFFF | 65536 | cached topological order of formula cells (slot indices) |
| UI_STATE | 0x0F0000 to 0x0FFFFF | 65536 | selection lists, edit buffer, dirty rectangle list, ribbon and dialog state (stage 2 onward) |
| GUARD | 0x301041 to 0x301FFF | 4031 | unused |
| TEXT_HEAP | 0x302000 to 0x37FFFF | 516096 | strings (section 9) |
| VBA_STATE | 0x380000 to 0x3AFFFF | 196608 | VBA modules, bytecode, frames, objects (section 10) |
| FILE_SCRATCH | 0x3B0000 to 0x3BFFFF | 65536 | file import and export work space: CSV token stream, inflate output window, XML token stream (stage 8, decision F2 in log/WORKLOG.md; weights/files) |
| WEIGHT_STAGING | 0x3C0000 to 0x3EFFFF | 196608 | memory-form networks written by generators (section 11) |
| UNDO_LOG | 0x3F0000 to 0x3FFFFF | 65536 | circular undo and redo log (stage 7) |

Charts, pivot caches and conditional formatting rules get space in later stages by splitting EVAL_SCRATCH, UI_STATE or VBA_STATE with new decision records; nothing is assigned to them yet.

**Why fixed regions instead of one general allocator.** Every address must come from a network output, and a general allocator (free lists of mixed sizes) is a large network that every subsystem would call. Fixed regions with one bump pointer or one free list each let each subsystem compute its own addresses with a bias plus a scaled index, which is one dense row. The cost is internal fragmentation (a full region cannot borrow from an empty one); it is accepted for now and revisited if tests run out of a region.

**Why power-of-two record strides.** Strides of 2, 4, 8 and 16 words keep address arithmetic integer and let record indices be recovered from addresses with exact power-of-two scaling and FLOOR.

## 3. Zero page

| Addr | Name | Meaning |
|---|---|---|
| 0x00 | FAULT | 0 normal; otherwise a fault code written by the trap network before halting |
| 0x01 | HEAP_TOP | next free word in TEXT_HEAP |
| 0x02 | FORMULA_TOP | next free word in FORMULA_STORE |
| 0x03 | DEP_FREE | head of the DEP_POOL free list (0 = use DEP_TOP) |
| 0x04 | DEP_TOP | next never-used word in DEP_POOL |
| 0x05 | NET_NEXT | next network id the allocator hands out (encodings/control.md section 5) |
| 0x06 | CUR_SHEET | active sheet index |
| 0x07 | CALC_MODE | 0 automatic, 1 automatic except tables, 2 manual |
| 0x08 | CALC_GEN | recalculation generation counter (section 4, CALC word) |
| 0x09 | ITER_ON | iterative calculation enabled (0 or 1) |
| 0x0A | ITER_MAX | maximum iterations (default 100) |
| 0x0B | ITER_DELTA | maximum change (default 0.001) |
| 0x0C | CELL_COUNT | occupied slots in CELL_STORE |
| 0x0D | SCRATCH_TOP | bump pointer in EVAL_SCRATCH |
| 0x0E | STYLE_COUNT | style records in use |
| 0x0F | SHEET_COUNT | sheets in use |
| 0x10 | NAME_COUNT | names in use |
| 0x11 | STAGING_TOP | next free word in WEIGHT_STAGING |
| 0x12 | CIRC_FLAG | set when the last recalculation met a cycle; holds packed key + 1 of the first cycle cell |
| 0x13 | DATE_1904 | 0 for the 1900 date system, 1 for 1904 |
| 0x14 | REJECT_COUNT | entries refused by the cell entry network since boot (encodings/io.md section 3, D19) |
| 0x15 | FL_COUNT | formula list length (evaluator, weights/eval/README.md) |
| 0x16 | TZ_OFFSET | local time zone offset in seconds east of UTC, added by NOW and TODAY to the clock (0 = UTC until something sets it; reserved for the date agent, 2026-11-06) |
| 0x17 to 0x3F | reserved for stage 1 to 2 globals | |
| 0x40 to 0x7F | UI globals (stage 2) | |
| 0x80 to 0xFF | spill area for the active subsystem's local registers (encodings/control.md section 3) | |

## 4. Cell store

Hash table of 2^16 slots at 0x010000, slot s at 0x010000 + 8 s. Hashing and probing: encodings/address.md section 4.

| Word | Name | Contents |
|---|---|---|
| 0 | KEY | 0 empty, -1 tombstone, else packed key K + 1 |
| 1 | TAG | value tag (encodings/value.md) |
| 2 | PAY | value payload |
| 3 | FORMULA | address of the formula record, 0 for a constant cell |
| 4 | STYLE | style id, 0 = Normal style |
| 5 | DEPS | address of the first dependency node of this cell's dependents list, 0 none |
| 6 | CALC | CALC_GEN * 4 + state, state 0 clean, 1 dirty, 2 visiting, 3 done |
| 7 | NEXTOCC | slot + 1 of the next occupied slot of the same sheet (occupancy list), 0 end |

Value at the slot is the last calculated value; a constant cell has FORMULA 0 and its value is the constant.

**CALC word, two roles.** The state (0 to 3) and the generation share one word. A state is only valid if the generation part equals the current CALC_GEN; starting a new recalculation increments CALC_GEN, which invalidates every state at once without a pass over the table. The roles do not interfere because the state occupies values 0 to 3 of CALC mod 4 and the generation the quotient; both are recovered exactly with one FLOOR on CALC * 0.25 (exact power-of-two scaling). Cycle detection: meeting a cell in state 2 (visiting) during the depth-first walk is a cycle.

**Occupancy list, two roles of NEXTOCC.** NEXTOCC links occupied slots per sheet (head in the sheet record) for sparse range scans and file save. It is written only when a slot changes from empty to occupied or back, and read only by scanners, so it never conflicts with value or formula updates.

## 5. Sheet record (16 words, SHEET_TABLE + 16 * SHEET)

0 name handle, 1 cell count, 2 occupancy head (slot + 1), 3 range dependency list head, 4 tab color, 5 visibility (0 visible, 1 hidden, 2 very hidden), 6 frozen rows, 7 frozen cols, 8 default row height, 9 default column width, 10 top visible row, 11 left visible column, 12 zoom percent, 13 selection record pointer (UI_STATE), 14 tab order position, 15 flags (protection, gridlines shown, right to left).

The table holds 256 sheets although SHEET has 16 bits; a larger table can be placed later without changing the key encoding.

## 6. Formula store and token stream

Formula record (8 words, bump allocated from FORMULA_STORE): 0 text handle (formula text as typed, R1C1-independent display form rebuilt by the formula bar), 1 token stream address, 2 token count, 3 flags (bit values 1 volatile, 2 legacy array formula, 4 dynamic array result, 8 contains INDIRECT or OFFSET, so dependencies are dynamic), 4 reference count (shared formulas), 5 home key for shared formulas (the cell the relative offsets are measured against is always the evaluating cell, so this is used only for display), 6 and 7 spare.

Token stream: tokens of 2 words, [OPC, OPND], in reverse Polish order.

| OPC | Meaning | OPND |
|---|---|---|
| 0 | end of stream | 0 |
| 1 | number literal | the double |
| 2 | text literal | string handle |
| 3 | boolean literal | 0 or 1 |
| 4 | error literal | error code |
| 5 | cell reference | reference operand (encodings/address.md section 6) |
| 6 | range reference, first corner | reference operand; the next token is OPC 7 |
| 7 | range second corner | reference operand |
| 8 | sheet prefix for the next reference | SHEET, or SHEET + 2^16 * SHEET2 for 3D |
| 9 | defined name | name table index |
| 10 | array constant | address of an array record in FORMULA_STORE |
| 11 | missing argument | 0 |
| 16 to 47 | operators | 16 unary minus, 17 unary plus, 18 percent, 19 ^, 20 *, 21 /, 22 +, 23 -, 24 &, 25 =, 26 <>, 27 <, 28 <=, 29 >, 30 >=, 31 range (:), 32 union (,), 33 intersection (space), 34 implicit intersection (@), 35 spill reference (#); others reserved |
| 64 + fid | function call | argument count |

The function id fid is the row index of the function in FUNC_TABLE, which maps it to the network id that implements it. Evaluation dispatch is therefore one read of FUNC_TABLE and one routing step (`next` = the value read), not a comparison chain.

**Why 2-word tokens.** One word per token would need opcode and operand packed, and numeric literals use all 53 bits of a double. A fixed 2-word token keeps stride arithmetic trivial and lets the evaluator read OPC, then OPND, with a uniform pipeline.

## 7. Style record (16 words, FORMAT_STORE + 16 * style id)

0 number format code (string handle, 0 for General), 1 font name handle, 2 font size in points times 4, 3 font flags (1 bold, 2 italic, 4 underline single, 8 underline double, 16 strike, 32 superscript, 64 subscript), 4 font color (0xRRGGBB), 5 fill color, 6 pattern type, 7 pattern color, 8 to 11 borders left, right, top, bottom (style code * 2^24 + color), 12 horizontal align * 16 + vertical align, 13 indent * 256 + rotation, 14 flags (wrap, shrink, merged, locked, hidden), 15 conditional format list pointer. Style 0 is Normal (Aptos Narrow 11, black, no fill). Distinct styles are interned: the cell writer searches for an identical record before allocating one (a network loop; open question on cost).

The packed words (8 to 14) keep each subfield in disjoint integer ranges and are unpacked with FLOOR; no field exceeds its range so the roles do not overlap.

## 8. Dependency pool

Two node kinds, both allocated from DEP_POOL:

- **Cell edge** (2 words): [dependent packed key K, next node address]. The list head is the precedent cell's DEPS word. Written when a formula referencing that cell is entered; removed when the formula changes.
- **Range edge** (4 words): [corner 1 key K, corner 2 key K, dependent K, next node address]. The list head is the sheet record's word 3. A change to any cell scans this list with four compares per node. Range references that cover more than 16 cells use range edges; smaller ranges are expanded into cell edges (open question: threshold).

Freed nodes go on the DEP_FREE list using their "next" word; 2- and 4-word nodes are kept on separate free lists in a later revision if fragmentation shows up (open question).

## 9. Text heap

String record at handle h: word h = length in UTF-16 code units, word h + 1 = reference count, then ceil(length / 3) words of packed code units: `word = c0 + c1 * 2^16 + c2 * 2^32` with c0 the earliest character; unused positions in the last word are 0. Packed words are below 2^48, exact. Character encoding: encodings/glyph.md.

TEXT_EMPTY = 0x302000 is a permanent string of length 0. It needs no initialisation because zeroed memory already reads as length 0, reference count 0. HEAP_TOP starts at 0x302002.

**Why 3 code units per word.** A read moves one word per step, so packing triples the characters per step for lexing, comparison and rendering, and triples heap capacity (about 1.5 million characters). Unpacking costs two FLOOR blocks inside the forward pass (no extra steps). Packing 6 characters of 8 bits would not cover UTF-16, which Excel uses for text.

Allocation is a bump pointer; strings are immutable once written. Reclaiming dead strings (reference count 0) is a later compaction pass (open question Q-M2).

## 10. VBA state (first plan)

0x380000 to 0x38FFFF module source and token streams; 0x390000 to 0x39FFFF bytecode; 0x3A0000 to 0x3A7FFF call frames and locals (variables use the value layout with VBA tags 16 to 63); 0x3A8000 to 0x3AFFFF object table (moved from 0x3B0000 by decision F2, which gave 0x3B0000 to 0x3BFFFF to FILE_SCRATCH) (handles for Application, Workbook, Worksheet, Range objects, collections, class instances). Defined in stage 9.

## 11. Weight staging

Generators write memory-form networks (harness/FORMAT.md) here, then request io 7 with addr = start and io_arg = target id. The harness copies the network on load, so staging space is reused right after the load step; STAGING_TOP is reset by the generator when it finishes a batch. The largest planned single network (several 64 x 65 dense layers) is under 30,000 words, so 196,608 words hold a batch of several.

## 12. Non-interference summary

- Regions are disjoint address ranges, and each is written only by its owning subsystem through its own pointer in the zero page, so no word has two owners.
- WORK_STACK is shared by recalculation, sort and search; these never run nested (recalculation does not call sort; sort runs only from a command or a function such as SORT, which uses OPER_STACK and EVAL_SCRATCH, not WORK_STACK). The owner holds WORK_STACK until it returns to the main loop. Crosstalk test: a SORT function result feeding a recalculation chain (stage 10).
- Multi-role words inside records (CALC, NEXTOCC, packed style words) are covered in their sections above.

## 13. Parser output as built (weights/parse, 2026-11-06, decisions P1 to P5 and P6 to P10 in log/WORKLOG.md)

The compiled token stream follows section 6 exactly, with these stated choices and deviations:
- Formula record word 2 (token count) counts tokens **excluding** the end token (OPC 0); the end token is always written. FORMULA_TOP is advanced past the end token.
- Words 3 to 7 of the record are not written (flags 0 by fresh memory; volatile and INDIRECT flags not set yet).
- Range references are OPC 6 then OPC 7 (corner order as typed, not normalised; the evaluator normalises, decision P9: it resolves both corners to absolute rows and columns anyway, where min and max are one compare each, while the parser would have to unpack OPND1 and swap the flags with the fields).
- Whole columns and rows use the same pair (address.md section 5): A:A is corner 1 = row absolute 0, corner 2 = row absolute 1048575 (FLAGS bit 0 set, the column part as typed); 3:3 is corner 1 = column absolute 0, corner 2 = column absolute 16383 (FLAGS bit 1 set, the row part as typed). The evaluator cannot tell A:A from A$1:A$1048576; the formula text keeps the typed form for display.
- A bare name that is not a reference, boolean or function is compiled as **error literal #NAME? (OPC 4, 5)**, not OPC 9, because no defined names exist yet. To be replaced by OPC 9 when the name table exists.
- A function call is OPC 64 + fid with fid = the checklist FN number (CHECKLIST.csv), operand = argument count. Unknown function names compile to fid 0 (OPC 64), which FUNC_TABLE should map to a #NAME? network.
- Missing arguments are OPC 11, including a leading one (IF(,1,2)) and a middle one (IF(1,,2)). F() with nothing inside has argument count 0 and no OPC 11.
- Unary minus 16, unary plus 17, percent 18 (postfix, emitted directly); ^ is left associative; unary binds tighter than ^ (=-2^2 is 2 u- 2 ^).
- Text literals are new heap strings (reference count word left 0); "" uses TEXT_EMPTY.
- Union is opcode 32 (comma at operand level inside a plain parenthesis, (A1,C1)) and intersection 33 (one or more spaces between an operand and a following letter, '$', apostrophe or '('). Both are operator tokens with operand 0. Precedence: intersection above every other operator (so =-A1 B1 is A1 B1 33 16); union pops only at a comma, ')' or the end, so inside its parentheses it binds loosest (decision P7; with reference operands the two readings give the same result).
- Sheet prefix: OPC 8 with operand SHEET (the sheet table index) immediately before the reference token (OPC 5, or the OPC 6 / 7 pair) it applies to. The name is matched against the sheet records' name strings (section 5 word 0, SHEET_COUNT at 0x0F) with ASCII case folding; quoted names may contain spaces and '' for a quote. A name that matches no sheet rejects the entry (decision P10). 3D prefixes (SHEET + 2^16 SHEET2) are not produced yet.
- Number literals: |decimal exponent| <= 22 in numconv, beyond in numbig (correctly rounded in every case tried, argued not proven). A value above the largest double is rejected in a formula (text as an entry); a value below 2^-1022 becomes 0 (decision P8).
- Not yet produced: OPC 9, 10, 31 (':' between general references), 34, 35.
- PARSE_STACK is split: 0x2000 to 0x27EF operator stack (1 word = kind + 4096 argc), 0x27F0 to 0x27FF the sheet key buffer (a folded sheet name packed 3 units per word, at most 31 units), 0x2800 to 0x2FFF the unpacked character buffer (one UTF-16 unit per word, at most 2047 per entry).
- Parser network ids: 64 to 79 and 120 to 123 (lrow, shpack, shlook, numbig); 124 to 127 are reserved for the parser. The evaluator uses 80 upward.

## 14. UI_STATE layout as built (weights/ui, 2026-11-06, decisions U6 to U10 in log/WORKLOG.md)

| Address | Size | Contents |
|---|---|---|
| 0x0F0100 | 64+ | BUF: text being drawn, one UTF-16 unit per word, 0-terminated |
| 0x0F1000 | 1120 | display cache: (TAG, PAY) last drawn per visible cell, cell (r, c) at 0x0F1000 + 40 r + 2 c (r 0..27, c 0..19) |
| 0x0F2000 | 17920 | DISPLAY_TABLE: text drawn per visible cell, 32 words per cell at 0x0F2000 + 640 r + 32 c: units (one per word, at most 31), then 0. Blank cells hold 0 in word 0. Written on every cell redraw; until the format engine exists it is the General text the UI produced. |
| 0x0F8000 | 2560 | fill pattern ROM row (rewritten by every pattern fill) |

UI zero page globals: 0x40 UI_AROW, 0x41 UI_ACOL (active cell last outlined), 0x42 UI_HLDONE (headers highlighted at least once), 0x43 UI_SCANKEY ((HEAP_TOP - 0x302002) + 2^20 CELL_COUNT at the last cell scan), 0x44 UI_EDLEN (edit length scratch for the echo).
