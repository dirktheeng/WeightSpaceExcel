# Encoding: ADDRESS (cells, ranges, sheets, and memory addresses)

Status: design, stage 1. Decision records: log/WORKLOG.md "2026-11-06 Stage 1: shared encodings design", decisions D4 (hashed cell store), D6 (register and packed forms), D7 (token reference operand). Related: encodings/value.md, encodings/memory-map.md, encodings/primitives.md.

## 1. Fields and ranges

All indices are 0-based integers inside networks. Excel's displayed A1 row 1 is ROW 0, column A is COL 0.

| Field | Range | Bits | Notes |
|---|---|---|---|
| SHEET | 0 to 65535 | 16 | index into the sheet table (encodings/memory-map.md); sheet order in the tab bar is a separate list, so moving a tab does not renumber |
| ROW | 0 to 1048575 | 20 | Excel limit 1,048,576 rows |
| COL | 0 to 16383 | 14 | Excel limit 16,384 columns (XFD) |
| NS | 0 to 3 | 2 | key namespace: 0 cell, 1 row properties, 2 column properties, 3 cell auxiliary record (comment, note, hyperlink, validation) |

## 2. Register form (unpacked)

In state words a cell address is three words (SHEET, ROW, COL). A range is five or six words (SHEET, R1, C1, R2, C2, and SHEET2 for 3D references, equal to SHEET otherwise), normalised so R1 <= R2 and C1 <= C2. Register assignment is in encodings/control.md.

Unpacked is the canonical register form because every address computation (hashing, offsetting, range iteration, rendering positions) needs the separate fields, and splitting a packed word costs a FLOOR block per field while packing costs one dense row.

## 3. Packed key (storage and comparison form)

    K = ((NS * 2^16 + SHEET) * 2^20 + ROW) * 2^14 + COL
      = NS * 2^50 + SHEET * 2^34 + ROW * 2^14 + COL

K < 2^52, so it is an exact integer double (encodings/value.md V2). Packing is one dense row with weights 2^50, 2^34, 2^14, 1 (all integer, exact in any order). The cell store keeps K + 1 in its key word so that 0 means an empty slot.

Unpacking (only where a network receives a packed key, for example when reading a dependency edge) uses FLOOR on K * 2^-14 (exact scaling by a power of two) to get COL = K - 2^14 * floor(K * 2^-14), then repeats on the quotient for ROW and SHEET. Each FLOOR is 4 to 6 layers inside one forward pass, no extra steps.

Row properties use NS 1 with COL 0; column properties NS 2 with ROW 0; per-cell auxiliary records (comments, hyperlinks, validation) NS 3 with the cell's own ROW and COL. Sheet-level settings live in the sheet table, not here. They share the cell hash table, so per-row heights or per-column widths cost memory only when set.

## 4. Hash to memory address

The cell store is an open-addressing hash table of 2^16 slots, 8 words per slot, at CELL_BASE (encodings/memory-map.md). From the register form:

    t    = 40503 * ROW + 65599 * COL + 1000003 * SHEET + 7919 * NS     (exact integer, t < 2^53)
    slot = t - 65536 * floor(t * 2^-16)                                 (t mod 2^16)
    addr = CELL_BASE + 8 * slot + field

Every step uses only integer weights, one FLOOR, and one dense row, so the address is an exact integer. All networks that touch the store use the same HASH block (encodings/primitives.md), so the slot sequence is identical for writers and readers.

**Why these multipliers.** 40503 is odd, so for a fixed column the map from row to slot is a bijection on any run of 65536 rows: a column of consecutive values never collides with itself. 65599 mod 65536 = 63, so neighbouring columns of one row sit 63 slots apart and do not cluster with the row sequence. SHEET and NS multipliers are large odd constants so separate sheets do not overlay each other's patterns.

**Probing.** Linear probing: on a key mismatch, slot' = slot + 1 - 65536 * step(slot + 1 - 65535.5) (wraps at the end, exact). A lookup is one read per probe: the step that computes the address reads the key word, and the next step (key arrives in input word 0) compares it with K + 1 (EQ primitive): equal means found, 0 means absent, otherwise probe. Deleted cells leave a tombstone key of -1 so probe chains stay intact; the cell writer reuses tombstones. Table occupancy is kept below about 70 percent (about 45,000 cells, open question: capacity).

**Pipelined record load.** Because one memory operation happens per step, loading a found cell's value takes 3 steps (key, TAG, PAY). The lookup network issues the TAG read of the same slot in the step after the key read, speculatively, while it checks the key; on a mismatch the TAG it receives is discarded. A hit therefore costs 3 steps and each extra probe costs 1.

## 5. Ranges and iteration

A range in registers is (SHEET, R1, C1, R2, C2[, SHEET2]). Iteration is a network loop with counters (ROW, COL) in registers, one hash lookup per cell. For sparse large ranges (SUM(A:A)) iterating over 2^20 rows is too slow, so range scans will instead walk a per-sheet list of occupied cells (the occupancy list, encodings/memory-map.md) and test containment with four compares. Which strategy to use is chosen per call by comparing range area with the sheet's cell count (open question: exact crossover).

Whole-column and whole-row references (A:A, 1:1) are ranges with R1 = 0, R2 = 1048575 or C1 = 0, C2 = 16383; no special encoding.

## 6. Reference operand in the token stream

Compiled formulas store references relative to the formula's own cell (like Excel's internal R1C1), so a copied formula shares the compiled tokens. A cell reference operand is one word:

    OPND = FLAGS * 2^36 + RF * 2^15 + CF

- FLAGS (2 bits): bit 0 row absolute ($), bit 1 column absolute ($). Encoded as FLAGS = rowabs + 2 * colabs.
- RF (21 bits): if the row is absolute, RF = ROW; if relative, RF = (ROW - home ROW) + 2^20, which lies in [1, 2^21 - 1].
- CF (15 bits): same for columns with bias 2^14.

OPND < 2^38, exact. Resolution to an absolute row: ROW = rowabs * RF + (1 - rowabs) * (homeROW + RF - 2^20). The gate is a bounded-integer select (relu big-M form is safe here because all quantities are below 2^22, encodings/primitives.md MUX_INT). Then range check: ROW outside [0, 1048575] or COL outside [0, 16383] gives #REF!.

A cross-sheet reference is preceded by a SHEET prefix token whose operand is the sheet index (or a sheet pair for 3D). Range references are two operand tokens (corner 1, corner 2) under one range opcode. Token word layout: encodings/memory-map.md section 6.

## 7. Memory addresses in general

A memory address is an integer word in [0, 0x3FFFFF] (harness MEM_SIZE 2^22). Networks build it with dense rows from base constants (biases), record indices times strides (integer weights) and field offsets, which is exact by V2. Two rules every network follows:

- **A1 (never negative).** numpy indexing accepts negative addresses and silently wraps to the end of memory. Every computed address must be non-negative; a network whose address could underflow (stack pop on an empty stack) checks the pointer first and branches to the trap network (encodings/control.md) instead of issuing the access.
- **A2 (address field when idle).** When mem_op is 0 and io is not 7, the address field is set to 0 so traces stay readable. It has no effect on the harness.

## 8. Multi-role words

- **The key word of a cell slot** holds 0 (empty), -1 (tombstone) or K + 1 (occupied). The ranges are disjoint (K + 1 >= 1), so one EQ against K + 1 and one EQ against 0 decide the probe outcome with no interference.
- **OPND** packs three fields in disjoint bit ranges with exact integer arithmetic; unpacking by FLOOR recovers each field exactly as long as OPND < 2^51 (it is below 2^38).
- **NS in K** lets row properties, column properties and auxiliary cell records share the cell table; they never collide with cells because NS differs and is part of both the key compared and the hash.
