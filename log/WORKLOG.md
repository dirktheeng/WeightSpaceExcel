# Work log

## 2026-11-06, Stage 0: harness design (DECISION)

**Decided.** One Python file, harness/harness.py (numpy only), about 175 lines. Frozen layer types: dense, relu, step (1 if x > 0), identity, mul (gating product of two slices of one value), slice, concat. Networks are lists of layers; each layer names an earlier value as its source (0 = network input), so branching and gating need no extra machinery. Step protocol output fields 0 to 6: next, mem_op, addr, value, io, io_arg, halt. Next input = [read result] + previous output. Weight files are plain text (harness/FORMAT.md). Generator networks write the same token stream as numbers into memory and request load with io code 7.

**Alternatives considered.** (a) Purely sequential layers with no source index: simpler, but gating and skip paths would need wide identity pass-through blocks, which conflicts with rule 4 (small networks). (b) Named registers: more readable, but a larger harness. (c) JSON or binary weight files: not comfortable to edit by hand. (d) A separate binary memory form for generated networks: would double the loader; reusing one token stream keeps one parser.

**Why.** Source indices give branching at near zero harness cost. One token stream for disk and memory keeps loading mechanical and small. Fixed fields at the front of every output let the harness obey without interpreting anything.

**Affects later.** Every network's output starts with the 7 fields; every network's input length is 1 + the previous network's output length, so network boundaries must agree on output length. Memory map regions are fixed (FORMAT.md); all other layout belongs to networks. Display, file, clock, entropy and event I/O are raw copies only. Number representation for protocol fields: floats rounded to integers; value is used unrounded (rule 8).

## 2026-11-06, Stage 0: harness and tests

- Tried: wrote harness.py. First version of load_memory had a dead generator and compared numeric codes as strings. Fixed by mapping numeric layer codes through MEM_CODES inside the single builder and feeding memory words through itertools.chain. Ad hoc forward pass (not committed): memory form [3, 1,0,1,3, 1,1,1, 0, 0] (input 3, dense 1x3 all ones, bias 0, end) on input [1,2,3] gave 6. Correct.
- Tried: compliance tests. Checks: no code files (by extension or shebang) outside harness/ and tests/; weights/ checked by file name only, never opened for content; harness digest equals harness/FROZEN.sha256; output tests make no file reading calls (AST check); compliance tests never call the weight loaders; harness never imports tests or pytest.
- Run 1: 6 passed, 1 failed. test_compliance_tests_skip_weights matched its own banned strings. Fixed by building the banned names from string pieces. Run 2: same failure, because "loadtxt" also appears legitimately in the FILE_READ_NAMES list. Removed those two from the banned list (the AST check already covers them for output tests). Run 3: 7 passed.

## 2026-11-06, Stage 0: smoke network

- Goal: the stage 0 exit check, a hand-written network that adds two numbers and halts.
- Wrote weights/smoke/add.wt by hand (one dense 7x8 layer) with its note weights/smoke/add.md. Row 3 has ones at input columns 1 and 2; mem_op bias 2 (write); halt bias 1; everything else zero.
- Forward passes via tests/output/test_smoke.py: (2, 3) wrote 5 to address 0 in exactly one step and halted; (-1.25, 0.5) wrote -0.75, address 1 untouched. Both passed.
- Froze the harness: harness/FROZEN.sha256 holds the SHA-256 over harness/ files (relative path plus contents, sorted, excluding FROZEN.sha256 and __pycache__). Full suite: 7 passed.
- Next: Stage 0 remaining deliverables (itemized parity checklist) and a manual harness audit against docs/HARNESS.md.

## 2026-11-06, Stage 1: shared encodings design

- Goal: define the latent encodings and memory map every later weight block will use (encodings/value.md, address.md, memory-map.md, control.md, primitives.md, glyph.md). Design only; no application weights.
- Read the harness closely first, because it fixes several constraints that drive every choice below: (1) next input = [read result] + previous output, so input length must equal 1 + previous output length; (2) exactly one memory operation per step, and a read result only arrives in the next step's input word 0; (3) fields 0 to 6 are rounded, everything else is a raw float64; (4) memory is 0x400000 words with the designated regions taking 0x100000 to 0x301040, leaving about 2.09 million words for networks; (5) on io 7 a network id at or beyond the current count is appended at the end, not placed at the requested id; (6) numpy indexing accepts negative addresses and wraps.
- Proof of concept: wrote weights/poc/round_floor.wt and weights/poc/round_floor.md by hand to validate the ROUND trick (D5) before building FLOOR, MOD and hashing on it. Ad hoc forward passes (not committed): 2.5 gave floor 2 round 2; 3.5 gave 3 and 4; -2.5 gave -3 and -2; -0.0001 gave -1 and 0; 0.49999999999999994 gave 0 and 0; 2^51 - 0.5 gave 2^51 - 1 and 2^51. All as derived, so numpy's dense evaluation does give plain IEEE rounding for one-term-plus-bias rows.
- Next: weights/lib reference blocks (IS_K, ONEHOT, FLOOR, MUX, DIVMOD_K) with notes, then BOOT, TRAP, RET, and the cell lookup network; settle the open questions listed at the end of this entry.

### D1 (DECISION): one state width S = 64 for all application networks
- Decided: every application network outputs 64 words and takes 65.
- Alternatives: per-subsystem widths (smaller networks, but any return to a different caller would break the harness length rule unless every boundary had an adapter network costing a step); S = 32 (too few words once control, three value registers, a range address and pointers are placed); S = 128 (no planned subsystem needs it).
- Why: returns can go to any caller, so one width is the only safe choice; slice and concat make pass-through free in parameters.
- Affects: every network file (input 65), the register map (D10), generator templates (D16).

### D2 (DECISION): values are two words (TAG, PAY) with a scalar tag
- Decided: TAG is a small integer (0 blank, 1 number, 2 text, 3 boolean, 4 error, 5 reference, 6 array, 7 lambda, 8 missing argument, 16 to 63 VBA); PAY is the double, handle, flag, error code or pointer. Error codes follow ERROR.TYPE numbering.
- Alternatives: one-hot tag (9+ words per value; 9 reads to load a type); one word with NaN boxing (rejected: NaN poisons every row of the next dense layer, since 0 * NaN = NaN); type folded into PAY by value ranges (impossible, numbers use the full double range).
- Why: one read per word is the scarcest resource; indicators are cheap to derive in-pass with ONEHOT. Blank = 0 means unwritten memory is already blank.
- Affects: cell records, operand stack, arrays, VBA variants, every operator and function network.

### D3 (DECISION): numeric precision plan
- Decided: PAY holds the exact IEEE double Excel would hold. Entry keeps 15 significant digits by truncation into an exact integer mantissa, converted with one correctly rounded multiply or divide by an exact power of ten when |E| <= 22; two-stage scaling otherwise. Arithmetic uses IEEE-faithful blocks (D13, D15). Excel's final-operation cancellation snap is a separate CANCEL_SNAP block with threshold to be pinned by tests. Display uses exponent search, scaling, ROUND and DIGITS.
- Alternatives: decimal (BCD-like) arithmetic in integer words (would not match Excel, which is binary double); fixed point (range far too small).
- Why: matching Excel bit for bit is only possible with the same binary doubles; the harness gives exactly that.
- Affects: lexer, formatter, all arithmetic, comparison tests.

### D4 (DECISION): cell store is an open-addressing hash table
- Decided: 2^16 slots of 8 words at 0x010000; hash t = 40503 ROW + 65599 COL + 1000003 SHEET + 7919 NS, slot = t mod 2^16 via FLOOR; linear probing; tombstones -1; key word holds packed K + 1.
- Alternatives: dense grid (2^34 cells per sheet, impossible in 4M words); page table of tiles (directory alone needs millions of words for the full grid); sorted list with binary search (about 16 reads per lookup and costly inserts); linked lists per column (a column scan per lookup).
- Why: about 3 steps per hit, memory only for used cells, all arithmetic exact (V2).
- Affects: every cell read and write, range scans (need the occupancy list), capacity (about 45,000 cells at 70 percent load, open question Q-M1).

### D5 (DECISION): ROUND by the 1.5 * 2^52 magic constant
- Decided: round(x) = (x + C) - C in two separate dense layers, C = 6755399441055744; FLOOR, MOD2K, DIVMOD_K and UNPACK build on it.
- Alternatives: step banks (one unit per possible integer value; useless for 20-bit fields); repeated subtraction across steps (one step per unit).
- Why: two layers, exact, validated by weights/poc/round_floor.wt.
- Affects: hashing, key and token unpacking, digit extraction, character unpacking, the return trampoline.

### D6 (DECISION): unpacked register form, packed storage form for addresses
- Decided: registers hold (SHEET, ROW, COL) or a 6-word range; storage and comparison use K = NS 2^50 + SHEET 2^34 + ROW 2^14 + COL.
- Alternatives: packed everywhere (every hash or offset needs an unpack); unpacked in memory (3 reads to compare a key).
- Why: packing is one dense row, unpacking costs FLOOR blocks; each form is used where it is cheap.
- Affects: address registers 19 to 24, dependency nodes, cell keys.

### D7 (DECISION): relative references in compiled tokens
- Decided: reference operand = FLAGS 2^36 + RF 2^15 + CF, relative fields biased by 2^20 and 2^14; tokens are 2 words [OPC, OPND].
- Alternatives: absolute addresses in tokens (copying a formula needs recompilation); 1-word tokens (no room for double literals).
- Why: copied and filled formulas share compiled streams, as in Excel's internal R1C1 form.
- Affects: lexer and parser output, evaluator, insert and delete reference adjustment (stage 7).

### D8 (DECISION): fixed memory regions
- Decided: the region table in encodings/memory-map.md, zero page globals at 0x000000, network data in the two free spans, a guard after the entropy block.
- Alternatives: one general allocator for all records (a large shared network on every path).
- Why: each subsystem computes addresses with one dense row from its own bump pointer or free list.
- Affects: all networks; region growth later needs new decision records.

### D9 (DECISION): text as packed UTF-16, three units per word
- Decided: string record = [length, reference count, packed words]; word = c0 + c1 2^16 + c2 2^32.
- Alternatives: one unit per word (3 times the reads and memory); 6 bytes per word (cannot hold UTF-16).
- Why: triples characters per read; unpacking is in-pass.
- Affects: lexer, string functions, rendering, file encoders and decoders.

### D10 (DECISION): register map
- Decided: words 7 PC, 8 LR, 9 LP, 10 RSP, 11 MODE, 12 STATUS, 13 to 18 value registers A, B, C, 19 to 24 address register, 25 to 28 pointers and counters, 29 to 39 temporaries, 40 to 63 callee-saved locals.
- Alternatives: no fixed map (each network pair negotiates; unmanageable across hundreds of networks).
- Why: a fixed map lets any subroutine be called from anywhere, and gives each word one owner at a time.
- Affects: every network note (clobber sets), crosstalk tests.

### D11 (DECISION): calling convention with link registers and a memory return stack
- Decided: call sets next, PC, LR, LP; nested callers push LINK = LR 2^16 + LP in the call step's free memory slot; return copies LR and LP into next and PC; RET (id 2) pops and returns for stack-based returns.
- Alternatives: stack only (extra read step on every return); registers only (no nesting); one network per subsystem with internal PC only (networks would become huge).
- Why: zero-overhead leaf calls, which dominate.
- Affects: every multi-network subsystem.

### D12 (DECISION): network id plan and allocation
- Decided: a 512-entry hand-written manifest (unused ids filled with TRAP); fixed id ranges per subsystem; generated ids from 512 handed out sequentially by an allocator keeping NET_NEXT equal to the loaded count.
- Alternatives: generated ids requested at arbitrary numbers (the harness would silently append them at a different index).
- Why: the harness append rule requires sequential allocation; fixed ranges make DISPATCH tables stable.
- Affects: weights/MANIFEST.md (to be written), FUNC_TABLE, glyph page dispatch, generators.

### D13 (DECISION): IEEE-faithful dense row rules R1 to R6
- Decided: real arithmetic uses only one-term rows, two unit-weight-term rows, one-term-plus-bias rows and mul layers; multi-term rows only for exact integers.
- Alternatives: trust dense rows with many real terms (summation order and fused multiply add are unspecified in numpy and BLAS, so results could differ from Excel by an ulp unpredictably).
- Why: makes every arithmetic result well defined and equal to Excel's.
- Affects: every arithmetic block and its note.

### D14 (DECISION): select by mul gating for doubles, relu big-M only for bounded integers
- Decided: MUX via mul layer for any value; MUX_INT via relu with M = 2^23 only for integers below 2^22.
- Alternatives: big-M everywhere (rounds or overflows for large doubles); mul everywhere (fine, but a relu form is cheaper inside integer-only networks).
- Why: exactness for doubles, cheaper integer selects.
- Affects: phase dispatch, operator networks, address resolution.

### D15 (DECISION): division by normalisation, Newton reciprocal and exact residual correction
- Decided: NORM by a binary exponent cascade, 4 Newton steps from a linear initial guess, Dekker TwoProduct residual and one correction.
- Alternatives: long division across steps (about 53 steps per divide); reciprocal ROM (enormous); Newton without correction (not correctly rounded; =6/3=2 could fail).
- Why: one forward pass, close to or exactly correctly rounded (open question Q-P1).
- Affects: / operator, MOD, QUOTIENT, every function that divides, decimal conversion.

### D16 (DECISION): generator stamping by rules, not stored matrices
- Decided: generators write one memory-form token per step, computing token values from ROMs of header tokens, parameter copies, and (row, col) rules for patterned matrices; generated networks rely on slice and concat for pass-through to stay small.
- Alternatives: generators holding full copies of template matrices (large generators); no generation (hundreds of near-identical function networks typed by hand).
- Why: keeps both generators and generated networks small and every value traceable.
- Affects: function compiler (stage 3), formula specialiser (stage 1 or later), documentation of generated networks (Q-P2).

### D17 (DECISION): framebuffer 1280 x 800, row-major, packed 0xRRGGBB words
- Decided: as stated; incremental redraw by dirty rectangles.
- Alternatives: full-region 1024 x 1024 (not a usual window shape); planar channels (3 writes per pixel).
- Why: fits the region, one write per pixel.
- Affects: all rendering, UI tests (window size must match, Q-G1).

### D18 (DECISION): glyphs as hand-designed bitmap ROMs per (variant, 128-unit page)
- Decided: one page network per font variant and page, rows as packed bit integers, dispatch by routing, ink-only pixel writes.
- Alternatives: vector outlines rasterised by networks (far larger and slower); one ROM for all of Unicode (enormous ONEHOT front end).
- Why: small per-page networks, cost only for pages used, and rendering steps proportional to ink.
- Affects: stage 2 rendering, text layout (ADV ROM), zoom.

### Open questions recorded by this entry
- Q-M1 capacity: about 2.09M free words; the cell table holds about 45,000 cells. Large workbooks from file tests may not fit.
- Q-M2 text heap reclamation (compaction) design.
- Q-C2 network id reuse for run-time specialised networks.
- Q-P1 is DIV correctly rounded in all cases without a fused multiply add; build a test set of hard quotients from Excel.
- Q-P2 how to document generated networks that exist only in memory.
- Excel's cancellation snap threshold, and whether = compares exactly; needs Excel-sourced cases.
- Range scan strategy crossover (hash per cell versus occupancy list) and the 16-cell range dependency threshold.
- Q-G1 window size; Q-G2 full-frame speed at one pixel per step; Q-G3 unsupported characters; Q-G4 input event word format; Q-G5 scaled glyph quality.

## 2026-11-06, Stage 1: input event format and black-box test protocol (Q-G4)

### D19 (DECISION): one packed word per input event; tests type keystrokes and read the cell store
- Decided: event word W = KIND 2^48 + MODS 2^40 + P (encodings/io.md). KIND 1 key down, 2 key up, 3 mouse move, 4 down, 5 up, 6 wheel, 7 double click. Key payload = UTF-16 unit + 2^16 VK (Windows virtual key code); the unit is the character the layout produced (0 for none), non-BMP and non-layout text goes as VK_PACKET (0xE7) units. Mouse payload = X + 2^16 Y + 2^32 button or wheel notches + 128.
- Test protocol: output tests read weights/MANIFEST.txt (paths only, line = network id), pass the paths and the encoded event script to Harness(networks, events=...), and call run(0, zeros(65)). Cell entry = Ctrl+G, address, Enter, text, Enter; clearing = Ctrl+G, address, Enter, Delete. An empty event queue with MODE ready halts through HALT_OK. Results are read from raw memory: cell store by the address.md hash and probe, TAG and PAY by value.md, text from the heap, CIRC_FLAG (0x12), FAULT (0x00), and a new zero page word REJECT_COUNT (0x14) for refused entries. WEIGHT_STAGING is never read.
- Alternatives: separate words for key, character and modifiers (3 reads per keystroke); key codes only with a layout network (keyboard layout knowledge in weights for no parity gain at this stage); a harness entry point that sets cells directly (would put application logic in the harness and is not frozen API); navigation by arrow keys (tests would depend on Enter's move direction setting).
- Why: one read per event, exact integer fields unpacked by FLOOR with power-of-two scaling, and the test exercises the same path a user does (keyboard, edit mode, commit). Reading documented memory is observation, not weight inspection.
- Affects: the main loop and event dispatch (ids 4 to 15) must halt on an empty queue in MODE 1; the cell entry network owns REJECT_COUNT; the manifest file is weights/MANIFEST.txt (encodings/control.md section 5 says MANIFEST.md; the coordinator chose .txt); encodings/glyph.md's Q-G4 note is now resolved by encodings/io.md. Compliance: output tests may open only static paths under tests/, weights/MANIFEST.txt and checklist/CHECKLIST.csv (AST checked).

## 2026-11-06, Stage 1: control kernel and cell store (kernel agent; details in log/kernel-agent.md)

- Built weights/kernel/: BOOT (0), TRAP (1), RET (2), HALT_OK (3), main loop (4 to 8), Enter commit chain (9 to 15), cell store (16 to 26), parse stub (27), rejection counter (28, 29). 30 networks, 5126 parameters in all (ev_decode 3585, cs_probe 482, boot 298, the rest 14 to 76 each). Every network has a note in weights/kernel/*.md.
- Forward passes found one bug (cell hash used the quotient instead of the remainder; fixed in cs_hash.wt). tests/output/kernel/test_kernel.py: 20 passed. weights/MANIFEST.txt created with ids 0 to 29.

### K1 (DECISION): kernel networks are single-step; routing replaces phases
- Decided: each kernel network performs exactly one harness step; multi-step procedures are chains of networks linked by `next`, and PC stays 0 inside the kernel. Every network's output is a small dense head over a gathered slice of its input, concatenated with PASS slices.
- Alternatives: multi-phase networks with ONEHOT(PC) and vector MUX (encodings/control.md section 3), which cost the sum of all phases' weights in every step and need a MUX over 64 words.
- Why: routing is free and each step's network stays small (median 21 parameters); weights are easier to reason about one step at a time.
- Affects: network id usage (one id per step: 30 ids for the kernel so far, inside the 0 to 63 range), notes have per-network step tables instead of PC tables.

### K2 (DECISION): one cell store path for get and set, selected by T1
- Decided: CELL_GET and CELL_SET both enter at id 16 with T1 = 0 or 1. The probe network writes the first word itself (TAG on a hit, KEY on an empty slot). Set writes KEY (new), TAG, PAY, FORMULA = P1, CALC = 4 CALC_GEN + 1, and bumps CELL_COUNT. NS is fixed at 0 for now. Tombstones are skipped but not reused; the occupancy list is not maintained yet.
- Alternatives: separate get and set networks (duplicate hash weights); set as a caller of get (nested call, a return stack push and pop per write); the speculative TAG read of address.md section 4 (saves one step on hits but complicates the probe; can be added later inside cs_probe without changing the interface).
- Why: no nesting, shared hash, set of a new cell in 9 steps, get hit in 4.
- Affects: callers pass T1; recalculation can rely on CALC dirty marks written by every set; open items K-Q1 (NS argument), K-Q2 (full table fault 4), K-Q3 (NEXTOCC and sheet occupancy head), tombstone reuse.

### K3 (DECISION): event decoding and the edit buffer
- Decided: ev_decode handles a whole event in one step: three parallel FLOORs give VK, UNIT, KIND; Ctrl+G = KEY_DOWN, VK 0x47, UNIT 0 (UNIT is 0 whenever Ctrl is held, encodings/io.md), so MODS is not unpacked; Go To addresses accumulate in registers; typed units are packed directly into the next heap string record (one write per keystroke). Enter commits by writing the header and calling the entry parser, then CELL_SET, then moves the active cell down. Delete writes a blank value (TAG 0) rather than a tombstone.
- Alternatives: a separate edit buffer in UI_STATE copied to the heap on Enter (one extra read and write per three units); decoding MODS bits (two more FLOORs).
- Why: fewest steps per keystroke (2 per event including the next-event read), no copy on commit.
- Affects: the parser receives the text as a finished heap string (TAG 2, handle); strings of rejected entries are not reclaimed (Q-M2); Backspace, Escape and arrows are not handled yet.

### K4 (DECISION): manifest content and the parser hook
- Decided: weights/MANIFEST.txt lists kernel ids 0 to 29 in `ID PATH` form; the parser id is a single bias in weights/kernel/c_parse.wt (currently 27, the stub that accepts text). The parser contract is in weights/kernel/commit.md.
- Alternatives: a dispatch word in the zero page read at commit time (one extra step per commit, and a zero page word to reserve).
- Why: one hand edit when the parser lands, no runtime cost.
- Affects: weights/parse must follow the contract in commit.md (A = text handle in, value and P1 out, STATUS 0 or reject, locals preserved, LR 13 return).

## 2026-11-06, Stage 1: primitive library (weights/prim/)

- Goal: implement the encodings/primitives.md blocks as hand-written, tested reference blocks. Detailed attempt log: log/prim-agent.md.
- Built and tested (tests/output/prim/test_prim.py, 172 cases, all pass): is_k, onehot, compare, mux, floor_round, mod2k, divmod_k, digits, safe_add, safe_mul, hash, idivmod, div. Each has a note beside it; shared conventions in weights/prim/CONVENTIONS.md.

### P-D1 (DECISION): primitive test network convention
- Decided: each primitive is a one-step 64-word network (input 65): arguments from the register map (A, B, C, address register, T0, T1), results in T0 onward, words 0 to 6 = halt only, all other words passed through by slice and concat.
- Alternatives: the 8-word poc layout (not the application width, so blocks would need re-plumbing); a separate library format with no runnable test (cannot be verified by forward passes).
- Why: blocks are tested in the exact layout they will be retyped into.
- Affects: every block note; host networks copy only the middle layers.

### P-D2 (DECISION): primitive test networks take no manifest id
- Decided: weights/prim networks are loaded by path in their own tests and get no entry in weights/MANIFEST.txt.
- Alternatives: give them ids inside a subsystem range (encodings/control.md section 5 has no primitive range, and all of 0 to 511 is owned); ids from 512 (breaks the sequential generated-id rule of D12).
- Why: primitives are retyped blocks, never routed to.
- Affects: weights/MANIFEST.txt unchanged by this work. If a router ever needs them, control.md must assign a range first.

### P-D3 (DECISION): SAFE_MUL scales by 2^-512 and tests |s| >= 1
- Decided: s = fl((a 2^-512)(b 2^-512)); overflow iff |s| >= 1.
- Alternatives: primitives.md's 2^-600 with threshold 2^-176 (equivalent, needs two more literals).
- Why: one literal, already verified exact; the threshold argument is a simple midpoint argument (weights/prim/safe_mul.md).
- Affects: operator networks that retype SAFE_MUL.

### P-D4 (DECISION, correction): RECIP initial guess is 24/17 - (8/17) m
- Decided: on m in [1, 2) the linear start is y0 = 24/17 - (8/17) m.
- Alternatives: the line in encodings/primitives.md, 48/17 - (32/17) m, which is the minimax line for m in [0.5, 1]; on [1, 2) it gives 0 at m = 1.5 and Newton diverges (seen in idivmod run 1, log/prim-agent.md).
- Why: same 1/17 relative error, correct interval.
- Affects: encodings/primitives.md RECIP text should be corrected by its owner; idivmod and div use the corrected line.

### P-D5 (DECISION): DIV by normalised mantissas, two residual refinements, exact midpoint check, and an exponent split with one final rounding (Q-P1)
- Decided: NORM both operands in parallel; Q0 = ma y; Q1 = Q0 + R0 y with R0 from Dekker TwoProduct; exact R1 for the faithful Q1; neighbour selection by exact comparison of R1 with half-gap times mb; then scale by Fp Fn F2 built from bits of P <= 1023, N <= 1021 and E2 in [-56, 1].
- Alternatives: D15 as written (one refinement, q = q0 + r y, not provably correctly rounded without FMA); a direct exponent cascade on the quotient (unselected branches can overflow, then 0 times inf is NaN); scaling by 2^-eb only (Dekker overflows for large a).
- Why: correct rounding for every normal quotient with only IEEE single operations; every intermediate finite.
- Affects: Q-P1 answered for normal results; new open question Q-P1b: subnormal quotients can double round (weights/prim/div.md). Cost 338 layers, 10470 parameters as written (mostly zeros; a slimmer rewrite is possible).

### P-D6 (DECISION): DIVMOD_K and DIGITS take q0 = ROUND, not FLOOR
- Decided: q0 = round(fl(x fl(1/d))), then the two-sided exact remainder correction.
- Alternatives: FLOOR first as in primitives.md (one more compare layer and step unit per divisor).
- Why: the product error is below 0.04, so q0 is f or f + 1 and the existing correction covers it.
- Affects: digits.wt (14 chains), divmod_k.wt, idivmod.wt.

### P-D7 (DECISION): ROUND half away from zero lives in the FLOOR block
- Decided: floor_round.wt also outputs Excel's ROUND(x, 0) (half away from zero) by exact tie detection on e = round_even(x) - x.
- Alternatives: floor(x + 0.5) (wrong for 0.49999999999999994 and for large odd values, because x + 0.5 rounds).
- Why: exact for all |x| < 2^51, shares the layers of FLOOR and CEIL.
- Affects: the ROUND, MROUND and formatting functions.

### Open questions recorded by this entry
- Q-P1b: subnormal quotients may double round in DIV (fixable by a grid-aware midpoint check).
- Q-P3: control.md assigns no network id range to primitives (only matters if a primitive is ever routed to).
- The broad correctness of DIV rests on the hand cases and the argument in div.md; an Excel-sourced set of hard quotients is still wanted (Q-P1).

## 2026-11-06, Stage 1: entry parser and formula compiler (parse agent; details in log/parse-agent.md)

### P1 (DECISION): lexer as one network per state, routed by next
- Decided: the formula lexer is a set of small networks, one per lexer state (idle 66, number 67, word 68, string 70, error literal 71, comparison 72), each consuming one character per step and choosing the next state's network as `next`. Token completion hands registers to the parser decision network (73) and its emit phases (74).
- Alternatives: one lexer network with all states as phases (every step pays for every state's gates; a pair ROM over state x class would be 200+ AND units); a lexer pass writing a token list then a separate parser pass (two passes, more memory).
- Why: dispatch by routing costs no parameters (encodings/primitives.md DISPATCH); each network only carries the character classes its state needs.
- Affects: ids 64..79, step counts (about one step per character plus 1 to 4 per token).

### P2 (DECISION): parser register use and spill of L12..L23
- Decided: the kernel calls the parser with L0..L23 live (weights/kernel/commit.md). The parser enters through spill (78), which saves L12..L23 on RET_STACK (12 steps), and every exit goes through restore (79, 13 steps). Inside, the parser owns T0..T10 (29..39), L12..L23 (52..63), B, C (15..18), AR2, AC2, AS2 (22..24) and N0 (27). Map in weights/parse/README.md.
- Alternatives: fit into caller-saved words only (21 free words, but the lexer and parser need 27); spill all 24 locals (twice the cost).
- Why: 25 steps per entry is cheap relative to typing every network around a scattered register map.
- Affects: all parse networks; any later caller must leave RSP valid.

### P3 (DECISION): unpack the typed text once into a character buffer
- Decided: unpack (65) copies the packed heap text into one unit per word at 0x2800 + i (inside PARSE_STACK's "lexer scratch" half; the operator stack uses 0x2000 to 0x27FF). Limit: 2047 characters per entry.
- Alternatives: every lexer state network unpacks 3 units per word itself (UNPACK3 FLOOR blocks duplicated in six networks).
- Why: UNPACK3 lives in one network; 4 steps per 3 characters.
- Affects: memory-map PARSE_STACK split (0x2000 to 0x27FF operator stack, 0x2800 to 0x2FFF character buffer).

### P4 (DECISION): decimal conversion in one pass with exact residual
- Decided: numconv (75) computes M 10^k with one multiply for k >= 0; for k < 0 it computes q0 = M fl(10^-k), the exact residual M - q0 10^k by Dekker TwoProduct, and q = q0 + r fl(10^-k). |k| <= 22 only; beyond that the token is marked out of range (entry: text; formula: rejected).
- Alternatives: DIV primitive (about 140 layers); plain M fl(10^-k) (gives 0.30000000000000004 for 0.3).
- Why: 10^k is exact for k <= 22, so one residual correction gives the correctly rounded quotient in every case tested.
- Affects: all numeric literals; open question: exponents beyond 22 (1E+308, 1E-200 in stage 1 cases) need a two-stage scale.

### P5 (DECISION): kernel hook
- Decided: weights/kernel/c_parse.wt now calls 78 instead of 27 (coordinator authorization). Documented in weights/kernel/commit.md.
- Result (parse agent): 16 networks in weights/parse (ids 64..79), 18,132 dense parameters, all hand-typed. tests/output/parse/test_parse.py: 91 passed. Stage 1 suite: 28 passed with the evaluator still missing (was 3 with parse_stub). Token deviations recorded in encodings/memory-map.md section 13.
- Rule slip, recorded and undone: a shell loop briefly printed 23 repeated thermometer rows into a /tmp scratch file. It was deleted unused and the layer was typed by hand (log/parse-agent.md).

## 2026-11-06, Stage 1: evaluator and recalculation (eval agent; details in log/eval-agent.md)

- Built weights/eval/: hook entries (80, 81), recalculation (82..94), evaluator (95..107, 109, 116), number to text and & (110..113), power (114, 117). 34 networks, 32437 parameters (ev_div 10541 of them, a copy of weights/prim/div.wt with a new tail). Notes: weights/eval/README.md and the five notes beside it. MANIFEST.txt lines appended.
- tests/output/eval/test_eval.py: 91 passed. With the two kernel biases changed (in a /tmp copy, debug only), the stage 1 suite gives 249 of 273 non-SUM cases passing; the failures are 17 text coercion cases (stub), ari05 (2^0.5), rng09..11 (parser has no intersection yet), ref12 (parser choice), and cir05, cir06, cir09, where CIRC_FLAG = 0 is right but tests/output/test_stage1.py checks `circ in []` for `circular: []`, which can never pass (test bug to fix by the tests owner: treat an empty list as "expect 0").

### E1 (DECISION): precedent lists on the formula record, not dependents lists on cells
- Decided: when a formula is committed its cell references become edge nodes [precedent slot, next] in DEP_POOL, headed at formula record word 6. memory-map.md section 8 (dependents lists headed at the cell DEPS word, range edges) is not used yet.
- Alternatives: dependents lists (need unlinking from every old precedent when a formula changes, plus dirty propagation); walking token streams during recalculation (a hash lookup per reference per recalculation).
- Why: a replaced formula gets a new record, so old edges simply stop being reachable (rec12 needs no removal code); DFS reads slots directly.
- Affects: DEPS word unused; DEP_FREE unused (leak until a compaction pass); range precedents not recorded (stage 3 with SUM).

### E2 (DECISION): every precedent gets a cell slot
- Decided: a reference to an empty cell creates a blank cell (CELL_SET with TAG 0) at record time.
- Why: edges hold slot bases, never keys, so recalculation needs no hashing. Observable cells stay blank (TAG 0).
- Affects: CELL_COUNT counts these cells; file save must skip TAG 0 cells with FORMULA 0.

### E3 (DECISION): full recalculation in dependency order by an iterative DFS, every commit
- Decided: a formula list at CALC_CHAIN (count in zero page 0x15, FL_COUNT, taken from the stage 1 reserved range) holds every formula cell slot; each commit increments CALC_GEN (all cells stale) and visits the list with a DFS on WORK_STACK, evaluating a cell after its precedents. CALC states 2 (visiting) and 3 (done) per memory-map.md section 4.
- Alternatives: dirty marking through dependents (needs E1's alternative); demand-driven recursive evaluation (needs a re-entrant evaluator and stack frames for operand stacks).
- Why: smallest correct design; cost is linear in formula cells per commit.
- Affects: large sheets recalc slowly; a dirty-only pass is a later optimisation on the same DFS.

### E4 (DECISION): cycles by a Tarjan low link; cycle cells are 0
- Decided: frames carry LOW and CYC; a back edge to a visiting cell (its stack index is kept in its PAY word while visiting) lowers LOW and sets CYC; on pop a child whose LOW reaches its parent's depth propagates. CYC cells are written (1, 0) without evaluation; their dependents evaluate normally. CIRC_FLAG = K + 1 of the first back-edge target, reset each recalculation.
- Alternatives: zero everything on the stack at a back edge (zeroes non-cycle ancestors, wrong for cir10 orderings).
- Affects: iterative calculation (ITER_ON) will replace the "0" rule later.

### E5 (DECISION): hook point and return ids
- Decided: two entries, hk_commit (80, returns to 14) and hk_delete (81, returns to 8). Kernel owner must change weights/kernel/c_set.wt LR bias 14 -> 80 and weights/kernel/ev_decode.wt LR bias (biases line, 9th value) 8 -> 81. rc_fin rewrites HEAP_TOP; on the Delete path it also moves L8, L9 past strings the evaluator allocated.

### E6 (DECISION): lazy references on the operand stack (value tag 9)
- Decided: a cell reference token pushes (9, K); operators dereference with CELL_GET (left operand first) when they need values. Tag 9 is from the cell engine range 9..15 of encodings/value.md.
- Why: intersection and reference-taking functions need the reference, not the value; references cost nothing until used.

### E7 (DECISION): General number to text, first version
- Decided: 15 significant digits, fixed notation for exponents -9..14, otherwise d.dddE+xx; exponent from a 31-threshold bank (1e-10 to 1e20); one correctly selected power of ten by an exact one-hot ROM; digits emitted most significant first by DIVMOD_K(10^14). Text conversion builds a new heap string.
- Alternatives: DIGITS block plus trailing-zero count (larger); a 617-threshold bank (too much hand typing).
- Affects: numbers outside [1e-10, 1e21) give wrong text (documented); the cell renderer (stage 2) can reuse ev_fmt0/ev_fmt_emit with a different destination.

## 2026-11-06, Stage 2: minimal UI (ui agent; details in log/ui-agent.md)

### U1 (DECISION): screen layout, metrics and colours (Excel 2016 to 2021 "Colorful" theme, 100 percent zoom)
- Decided: 1280 x 800. Title bar and tab strip y 0..54 #217346; selected Home tab #F3F3F3; ribbon body y 55..146 #F3F3F3; ribbon border y 147 #D4D4D4; formula band y 148..175 white; name box x 3..104 and formula box x 160..1276, y 151..172, borders #C6C6C6, white interiors; "fx" label at x 136. Column header row y 176..195 and row header column x 0..30, fill #EFEFEF with separators #D4D4D4 (the last header pixel row and column are the separators); header text #444444, centred. Grid origin (31, 196). Column width 64 px (8.43 characters) and row height 20 px (15 pt), each including its right or bottom gridline; gridlines #E1E1E1; 20 columns A..T (T partial) and 28 rows visible. Sheet tab bar line y 756 #D4D4D4, bar and status bar y 757..799 #F3F3F3, "Sheet1" tab x 60..129 white with green text and 2 px underline, "Ready" at x 8. Cell text: glyph top at row + 5 (baseline 5 px above the gridline), left text ink from x + 2, right text ink ending at x + 59 or 60, booleans and errors centred, clip at x + 61. Active outline 2 px #217346 straddling the cell boundary (top/left on the neighbour's gridline, clamped to stay off the headers), plus a 5 x 5 fill handle at (x + 61, y + 17).
- Alternatives: the Microsoft 365 2023+ light title bar (newer, but the rest of the default chrome is less settled); D4D4D4 gridlines (older Excel).
- Why: one consistent, well-known era of Excel's look. Exact RGB values from real screenshots remain open question Q-G1 (glyph.md); every value is one ROM entry or bias to retune.
- Affects: weights/ui/scene.wt ROM, fill.wt pattern constants (31, 64, 196, 20), ce5/ce7, olR, fbar biases.

### U2 (DECISION): UI as single-step networks, a scene command ROM, and a displayed-value cache as the dirty scheme
- Decided: ids 128..169 as listed in weights/MANIFEST.txt. Each network does one step kind and routes by `next` (as kernel K1). Leaves return by (LR, LP). Mid-level loops (headers, cells, outline, formula bar) return to (L22, L23), which the scene sets to (152, PC + 1). The frame program is a ROM in scene.wt. Dirty tracking: each frame compares every visible cell's value with a cache of what was drawn (UI_STATE 0x0F1000 + 2 (20 r + c)) and repaints only changed cells. The outline is erased by repainting exactly its own rectangles with the grid pattern, using the previous active cell at UI zero page 0x40, 0x41.
- Alternatives: a dirty list appended by kernel hooks on every commit (needs two more kernel edits and misses recalculated formula cells); phase-dispatch networks with ONEHOT(PC) per subsystem (larger and harder to type).
- Why: no per-commit hooks; recalculation changes are caught for free; about 6 steps per visible cell per frame.
- Affects: UI_STATE use: BUF 0x0F0100..0x0F01FF (text buffer, one unit per word), cache 0x0F1000..0x0F145F; zero page 0x40 UI_AROW, 0x41 UI_ACOL. memory-map.md sections 2 and 3 should record these (owner: coordinator).

### U3 (DECISION): UI register use and the callee-saved exception
- Decided: the UI uses L12..L18 and L22, L23 as its locals without spilling them, and never touches L0..L11 (it reads L2/L3 for the active cell). Leaf arguments: fill N0, N1, T0..T8; glyph P0, T0..T8; aligned text B, C, AR2, AC2, AS2, N0, N1.
- Alternatives: spill L12..L23 on entry as the parser does (24 extra steps per frame).
- Why: the only callers are boot and the main loop, which do not use L12..L23 (main_loop.md), and the parser saves and restores its own. This is an exception to the callee-saved rule (control.md section 4). If the main loop ever uses L12..L23, add a spill network at 153 and 152 PC 0.

### U4 (DECISION): font as visual decimal-digit rows, 12 rows, one size
- Decided: weights/ui/glyph.wt v32 is a 96 x 13 ROM. Each glyph row is a decimal number whose digits are the pixels; ADV times 10^12 is in the last column. Cap height 9, x height 7, descender 3, digit advance 7, blank left bearing column. Pixels are extracted by repeated ROUND(r/10). This is an original design, not taken from any font file.
- Alternatives: binary row integers (they need binary-to-decimal conversion by hand for every row and cannot be read visually); per-pixel 0/1 dense (strided in row-major files).
- Why: the bitmap is legible and editable in the weight file, and digits 0/1 make the divide-by-10 extraction exact.
- Affects: bold, italic and other sizes are later variants (glyph.md D18 planned per-variant pages). Anti-aliasing could use digits 2..4 as coverage levels (still exact, since ROUND(r/10) holds for digits up to 4).

### U5 (DECISION): simplest General number display
- Decided: at most 11 characters including the sign and point; k = max(0, 10 - integer digits - sign) decimals, rounded, trailing zeros stripped (fnum.md).
- Alternatives: full Excel General with width-dependent rounding and scientific notation (stage 3 number format work).
- Affects: |x| >= 1e11 and nonzero |x| < 5e-10 display wrongly (documented in fnum.md); no shortening for narrow columns.

### U6 (HOOK REQUEST, not applied; weights/kernel is not mine to edit)
- weights/kernel/boot.wt: in the `next` row of the PC-step output dense (line 37, "next: main loop (4) at PC 9"), change the weight 4 on the PC-9 one-hot to 152. Boot then draws the first full frame and the scene returns to main_poll (4) itself, with PC 0 and MODE 1 as before.
- weights/kernel/ev_next.wt: in v8 (words 0..7), the next row is `0 0 3 0` with bias 4 (next = 4 + 3 c). Change it to weight -146 on c and bias 153, so next = 153 - 146 c (7 when another event remains, 153 when the batch is done). The incremental frame ends by routing to 4 with MODE 1.
- No active-cell hook is needed: the UI reads L2/L3 and keeps its own copy at 0x40, 0x41.
- Cost after the hooks: every event batch costs about 30k steps on harness v1, and boot about 1.1M steps (about 65 s), until the harness v2 block writes are used.

## 2026-11-06, Stage 1: parser extension (parse agent, session 2; details in log/parse-agent.md)

### P6 (DECISION): parser ids 120 to 123, reserve 124 to 127
- Decided: lrow 120, shpack 121, shlook 122, numbig 123 (weights/MANIFEST.txt); 124 to 127 reserved for the parser.
- Alternatives: ids just above 79 (the evaluator agent already uses 80 to 94 and is growing upward).
- Why: the top of the formula engine block (control.md section 5) cannot collide with the evaluator's sequential ids.
- Affects: encodings/memory-map.md section 13, weights/parse/README.md.

### P7 (DECISION): union and intersection as operator tokens 32 and 33; intersection found by idle
- Decided: idle keeps SPC (word 28) = "a space was skipped while E = 0"; at a letter, '$', apostrophe or '(' with SPC and E = 0 it hands parse the binary operator 33 without consuming the character. A comma whose stack top is a plain '(' is a binary push of 32. Intersection has the highest precedence; union pops only at a comma, ')' or the end.
- Alternatives: detect intersection in parse when an operand arrives with E = 0 (the pop it triggers would land after a sheet prefix token already emitted by shlook, splitting OPC 8 from its reference); give union precedence 8 above unary (needs a T >= 32 threshold and two more indicator columns; only changes results for non-reference operands, which are #VALUE! either way).
- Why: the lexer sees the space before the next operand is lexed, so the operator reaches the parser in source order.
- Affects: idle, parse. A digit after a space is never an intersection (=A:A 3:3 rejects, =1 2 still rejects).

### P8 (DECISION): number literals beyond 10^22 by a double-double loop; overflow rejects, subnormals flush to 0
- Decided: numconv routes |E10| > 22 to numbig, which builds 10^k 2^-512 as a double-double by exact factors (10^22, then 10^rem) with Dekker TwoProduct, then multiplies by M (positive) or forms the residual-corrected quotient (negative), then scales by 2^512 or 2^-512 exactly. Overflow is decided from the 15-digit mantissa and decimal exponent (e = 308 and M15 >= 179769313486232, or e >= 309) and rejects the formula (an entry stays text); values below 2^-1022 (e = -308 and M15 <= 222507385850720, or e <= -309) become 0.
- Alternatives: two-stage scale M 10^22 10^(k-22) (value.md section 4 plan; off by one ulp in places); a ROM of double-double powers (hundreds of hand-computed low parts); keeping subnormals (double rounding in the final scaling).
- Why: exact factors need no hand-computed constants; the only constants are 10^j (exact), fl(10^-j) and 2^(+-512) built by squaring in the pass.
- Affects: numconv, numbig. Excel's own behaviour below 2.2250738585072E-308 is unverified (open question Q-P4).

### P9 (DECISION): range corners stay as typed; the evaluator normalises
- Decided: the parser does not swap corners (=B5:A1 compiles as typed).
- Alternatives: normalise in wordend (needs a FLOOR unpack of OPND1 and a flag-aware swap of two packed fields).
- Why: the evaluator resolves both corners to absolute rows and columns anyway; min and max there cost one compare each.
- Affects: evaluator (weights/eval) must normalise every OPC 6 / 7 pair, including whole columns and rows.

### P10 (DECISION): sheet prefix by a packed, folded key and a linear scan; a missing sheet rejects
- Decided: shpack packs the case-folded name (3 units per word) into 0x27F0..0x27FF; shlook compares lengths, then folded heap words, sheet by sheet, emits [8, SHEET] and resumes lword with KLEN 100 and KEY 0 so only a reference can follow. A name that matches no sheet rejects the entry.
- Alternatives: compare unit by unit against the character buffer (4 steps per 3 characters per sheet, and '' escapes would not line up); compile a missing sheet to #REF! (Excel instead asks for an external workbook, which has no meaning here yet).
- Why: 2 steps per 3 characters per candidate sheet; the escapes are resolved once in shpack.
- Affects: memory-map section 13 (operator stack now ends at 0x27EF), README. Open: Unicode case folding, 3D prefixes, external references.

### Open questions recorded by this entry
- Q-P4: Excel's handling of typed numbers below 2.2250738585072E-308 (0, subnormal, or rejection).
- Q-P5: whether Excel accepts "=1 A1" or "=SUM (A1)"; both now parse as intersections.
- Result: 20 networks, 25,735 dense parameters. tests/output/parse: 179 passed (91 old unchanged, 88 new in test_parse_ext.py).

## 2026-11-06, Harness v2: block memory operations and faster engine (harness v2 agent; details in log/harness-v2-agent.md)

### H2 (DECISION): change the frozen harness, approved by the project owner
- Decided: (a) new mem_op codes 3 (block write) and 4 (block read). addr = start, value = K * 2^20 + N (K output words forwarded, N run length, each below 2^20). Block write copies out[K:K+N] to mem[addr:addr+N] and forwards out[0:K]; block read forwards out[0:K] followed by mem[addr:addr+N]. Everything bound-checked, nothing but copying. (b) A preparsed forward pass (integer opcodes, concat chains copied once, no per-step trace formatting when untraced, parsed-network cache keyed by file bytes), bit-identical to v1.
- Approval: the project owner approved this harness change explicitly. Reason: one write per step at about 57 us per traced step made a 1280 x 800 frame about a million steps, roughly a minute per frame. This cannot be done in weights: the one-word-per-step limit is in the harness itself.
- Alternatives: payload as the trailing N words (variable N would change the successor's input length); a fixed split at word 64 (puts the application state width into the harness); numba (not installed, and a compiled loop changes dense summation order versus BLAS, breaking R5 rows).
- Why bit-identical: dense keeps the same `W @ v` BLAS call and an elementwise bias add; all other layers are copies or single correctly rounded elementwise operations. Verified on every harness run in the full suite (v1 and v2 side by side, 830 runs, 0 differences) and a 3000-network fuzz.
- Affects: harness/harness.py, harness/FORMAT.md, docs/HARNESS.md, encodings/control.md section 1, encodings/memory-map.md section 1, harness/FROZEN.sha256 re-frozen. Codes 3 and 4 were ignored in v1 and were never produced by any existing network. New tests: tests/output/test_block_ops.py with weights/smoke/blk_*.wt.

## 2026-11-06, Stage 3: math functions, first network (func math agent; details in log/func-math-agent.md)
### FM1 (DECISION): family networks with a selector for the math functions
- Decided: one-argument piecewise-linear and constant math functions share one network, fm_unary (id 264), selected by T0, computing all candidates in one pass and selecting by one-hot MUX.
- Alternatives: one network per function (9 ids, about 9 copies of the coercion and FLOOR blocks).
- Why: the id budget (264..295 for all math functions) and rule 4 (shared blocks); the extra candidates cost about 400 parameters and no steps.
- Affects: the ABI dispatch (FUNC_TABLE) must map ABS, SIGN, INT, TRUNC, PI, EVEN, ODD, DEGREES, RADIANS to id 264 plus a selector constant in T0, or a thin per-function wrapper sets T0.

## 2026-11-06, Stage 8 groundwork: CSV scanner (files agent; details in log/files-agent.md)

### F1 (DECISION): CSV import as a byte scanner producing a token stream, then a separate field packer
- Decided: csv_scan (id 448, weights/files/csv_scan.wt) reads the file transfer region and writes tokens (byte 0..255, -1 field end, -2 row end, -3 end) to a caller-given buffer (proposed EVAL_SCRATCH 0x0B0000). A later network packs fields into heap strings and calls the entry parser per the kernel commit contract.
- Alternatives: one network that scans, packs and commits (more than 8 phases, and coupled to parser and CELL_SET internals); block reads of several bytes per step (an unrolled multi-byte state machine per pass, much larger).
- Why: the quoting state machine is the parity-critical part and is testable alone; one byte per step costs about 2 steps per byte.
- Affects: memory map (token buffer location needs the coordinator's assignment), future ids 449 onward (packer, exporter, ZIP, inflate, XML).
- Result: 1,488 parameters; tests/output/files/test_csv_scan.py 10 passed. Open question Q-F1: Excel's handling of CR inside a quoted CRLF.

## 2026-11-06, Stage 3: function calling convention (ABI agent; details in log/abi-agent.md, spec encodings/functions.md)

### F1 (DECISION): fid = checklist FN number; fid 0 unknown
- Decided: fid 1..525 = FN-0001..FN-0525 (the parser already emitted these); FN-0526..0532 are TEXT features (fid 462); new functions 526 upward.
- Alternatives: dense renumbering by category (would break the parser's existing fids and the checklist cross-reference).
- Affects: encodings/functions.md section 9, parser, FUNC_TABLE.

### F2 (DECISION): entry and return registers
- Decided: argument n in B, arguments 1..n-1 in OPER_STACK at SP - 2(n - i), n in N0, 64 + fid in T2; return with next = 257 (FN_RET), result in A, SP and N0 unchanged; FN_RET drops the arguments and resumes ev_disp (or pushes via ev_push2 PC 1 for n = 0).
- Alternatives: pop all arguments into registers (at most 3 fit; variadic functions need memory anyway); return via LR (would forbid functions from using LR for their own CELL_GET calls without a push).
- Affects: ev_func (eval agent: read FUNC_TABLE + fid, set N0 = n, route to 256), every function network.

### F3 (DECISION): name directory by transcribed decimal keys, flags packed with the fid
- Decided: two-digit character codes ('.' 10, digits 11..20, letters 21..46, '_' 47) written side by side, 8 characters per key word, two words; sorted directory at FUNC_TABLE 0x7400 (K1), 0x7800 (K2), 0x7C00 (fid + 1024 F); binary search. Flags F leave 0x7800 + fid (memory-map section 2) for the directory entry.
- Alternatives: the parser's base-39 key (needs hand multiplication for 525 names, 10-character limit); one equality unit per name in one network (525 x 4 rows of mostly zeros, dense format); a trie table in memory (thousands of hand-computed state numbers).
- Why: the key of a name is read off its letters with no arithmetic, so 525 hand-typed keys can be checked by eye and by a black-box test that parses every name.
- Affects: encodings/memory-map.md section 2 FUNC_TABLE row (coordinator: flags now in the directory, see functions.md section 3), weights/parse wordend (unknown-name path calls FN_KEY 262).

### F4 (DECISION): all arguments evaluated eagerly; OPC 12/13 reserved for lazy jumps
- Decided: IF, IFERROR, CHOOSE etc. receive all arguments evaluated; they select. Reserved OPC 12 (jump if false) and 13 (jump) for a later optimisation.
- Why: the token stream has no side effects, so results agree with Excel; only cost differs.

### F5 (DECISION): references reach functions undereferenced; range arguments as tag 5 records
- Decided: tag 9 (cell, PAY = K) and tag 5 (PAY = 8-word record [SHEET, R1, C1, R2, C2, SHEET2, NEXT, 0] normalised, in EVAL_SCRATCH; NEXT chains union areas). Missing arguments as tag 8.
- Affects: ev_push (eval agent: OPC 6/7 should build the record and push tag 5 instead of #VALUE!), ev_disp (OPC 11 should push (8, 0) instead of skipping), union operator 32 (link records by NEXT).

### F6 (DECISION): range arguments scanned through the cell store, not cell by cell
- Decided: aggregate functions scan the 2^16-slot cell store with block reads and test each occupied key against the range, so SUM(A:A) costs the same as SUM(A1:A3).
- Alternatives: one CELL_GET per cell of the range (1M lookups for a whole column); the occupancy list (not maintained yet, K-Q3; to replace the scan once it exists).

### F2 (DECISION): FILE_SCRATCH region 0x3B0000 to 0x3BFFFF (files agent, on the coordinator's instruction)
- Decided: FILE_SCRATCH = 0x3B0000 to 0x3BFFFF (65,536 words) for the CSV token stream, the inflate output window and the XML token stream. It is taken from the top of VBA_STATE, which shrinks to 0x380000 to 0x3AFFFF; the planned VBA object table moves from 0x3B0000 to 0x3A8000 to 0x3AFFFF (frames keep 0x3A0000 to 0x3A7FFF). memory-map.md sections 2 and 10 are edited accordingly.
- Alternatives: EVAL_SCRATCH (rejected by the coordinator: committing a field runs recalculation, which uses it); the GUARD block 0x301041 to 0x301FFF (only 4,031 words, and it exists to separate the entropy block); UI_STATE upper half (active stage 2 region, ribbon and dialogs still to be placed). No address range is unassigned in the map, so a split was unavoidable.
- Why: VBA (stage 9) has no networks or data yet (checked: no file in weights or tests uses 0x380000 to 0x3BFFFF), so nothing is displaced.
- Affects: CSV import of more than 65,535 tokens needs chunking (scanner limit, open). The VBA stage plan must use the new object table range.

## 2026-11-06, Stage 1 session 2: evaluator gaps (eval agent; details in log/eval-agent.md)

### E8 (DECISION): text to number coercion calls the parser's constant entry
- Decided: ev_t2n (109) wraps a call to the parser entry 78: write HT to HEAP_TOP, block-write words 8..39 to RET_STACK, call 78, block-read them into ev_t2nb (115), which restores them and maps a rejection to #VALUE!. Non-numbers returned by the parser (text, boolean, error, formula) become #VALUE! in ev_dref as before.
- Alternatives: a self-contained converter network (duplicates the lexer, numconv and the entry rules; two places to keep in step).
- Why: entry and coercion follow the same Excel rules by construction; block ops make the save and restore 2 steps; about 48 steps per coercion.
- Affects: ids 109, 115; depends on the parser contract in weights/parse/README.md (L0..L23 preserved, B, C, T clobbered).

### E9 (DECISION): reference values on the operand stack
- Decided: TAG 9 cell (PAY = K, sheet included), TAG 5 range (PAY = pointer to a normalised 6-word record [S, R1, C1, R2, C2, S] in EVAL_SCRATCH), TAG 10 union (PAY = pointer to a node [left TAG, left PAY, right TAG, right PAY]). Corners are normalised when the record is built (decision P9 leaves typed order in the token stream).
- Alternatives: pack a range into PAY (68 bits plus sheet do not fit 53); expand unions into area lists (copy loops).
- Why: one block write per range or union; consumers walk the union tree.
- Affects: ev_push, ev_rng (88), ev_dref, ev_ref1 (108); function networks will receive these values (note for the function ABI).

### E10 (DECISION): legacy implicit intersection, no spill
- Decided: a TAG 5 range used as a value (operand of an arithmetic, comparison or & operator, or the formula result) is reduced to one cell: its row if it has one row, else the home row if inside; same for columns; otherwise #VALUE!. A union as a value is #VALUE!.
- Alternatives: dynamic-array spill (needs the spill engine, later stage).
- Why: matches Stage 1 cases and pre-dynamic-array Excel; spill can replace it later at the same hook in ev_dref.
- Affects: ev_dref, ev_ref1.

### E11 (DECISION): sheet prefix carried in T2 (evaluator) and T7 (recalc walk)
- Decided: ev_push packs the prefix sheet into T2 = mode + 4096 SHEET; the recalc token walk uses rc_scan PC 2 to mean "just after a prefix" and T7 for the sheet. Unprefixed references use sheet 0.
- Alternatives: a pending-sheet register (stale values from scratch users of T3..T10).
- Why: no stale prefix can apply to a later reference, since every push path rewrites T2 and only PC 2 of rc_scan reads T7.
- Affects: ev_disp, ev_push, rc_scan, rc_ref. Open: a home-sheet register for formulas stored on other sheets.

### E12 (DECISION): EXP and LN for ^ inside one network
- Decided: ev_pow2 (99) computes a^b = EXP(b LN a) in one forward pass for a > 0 and non-integer or huge b (NORM2, atanh series, hi/lo ln2, Taylor degree 14, exact overflow test before scaling). Negative base with non-integer exponent stays #NUM!.
- Alternatives: separate LN and EXP networks (two more ids, none left in 80..117); a table-driven reduction (larger, needs exact table products).
- Why: one step per ^; all overflow decided exactly without forming an infinity (V1).
- Affects: ev_pow0, ev_pow2; LN and EXP blocks can be retyped by stage 3 functions (LN, EXP, POWER, SQRT).

## 2026-11-06, Stage 3: Text function cores (func-text agent; details in log/func-text-agent.md)

- Built weights/func/text/: tx_len 312, tx_code 313, tx_case 314, tx_exact 315, tx_mid 316, tx_char 317, tx_t 318 (7 networks, 7045 parameters). Notes beside each file and README.md. MANIFEST.txt lines appended. tests/output/func_text/test_func_text.py: 121 passed.

### T1 (DECISION): cores before the ABI
- Decided: each Text function is a core subroutine with register arguments (A, B, C, mode in N0), called by (LR, LP) and returning in A, with arguments already coerced (text or error; number or error).
- Alternatives: wait for encodings/functions.md; build coercion into every core.
- Why: the ABI did not exist; coercion is shared by every function family and belongs in the wrapper (ev_totext 110, ev_t2n 109 exist).
- Affects: ABI wrappers needed at 319 onward (or in the ABI owner's generic wrapper) before any formula can reach these cores.

### T2 (DECISION): heap top in word 23 (HT), as the evaluator keeps it
- Decided: string-building cores allocate at word 23 and return it advanced; they never read or write HEAP_TOP (zero page 0x01).
- Why: no memory steps for allocation; matches ev_cat and rc_fin (which writes HT back after recalculation).
- Affects: any caller outside recalculation must load HEAP_TOP into word 23 before the call and store it after.

### T3 (DECISION): one MID core realigns packed words; LEFT and RIGHT are wrappers over it
- Decided: substrings are built word by word from a pair (previous, current) of source words and the offset start mod 3, two steps per 3 output units, with the last word masked.
- Alternatives: unit-at-a-time copy (6 steps per 3 units); separate LEFT (aligned) network.
- Why: one network covers LEFT, RIGHT, MID and later REPLACE/SUBSTITUTE pieces.

### T4 (DECISION): single-step block-write networks always use mem_op 3
- Decided: tx_char always outputs mem_op 3 with K = 64 and N = 0 or 3, so its output length 67 never reaches the successor.
- Why: with mem_op 0 the harness forwards all 67 words and the successor (65 inputs) refuses. This applies to any network with a block-write payload that sometimes writes nothing.

### Requests for other owners
- ABI owner: wrappers must not leave a read result above 2^23 in word 0 if any callee uses relu muxes on x0 (my cores are safe: covered by tests); worth stating in functions.md as a general rule.
- Coordinator: checklist items with core-level tests passing (no formula-level test yet, so not "done" end to end): LEN, LENB (same core), CODE (ASCII and BMP; not the Windows-1252 reverse), UPPER, LOWER (Latin-1 only), EXACT, MID, LEFT, RIGHT (with wrappers), CHAR, UNICHAR, UNICODE (BMP), T.

### FM2 (DECISION): reuse ev_pow2 by copying it with numbering-preserving edits
- Decided: fm_pw1 copies ev_pow2 (eval agent) and changes five layers in place (v1, v2, v135, v137, v138) so a mode word forces LN = 1 exactly; EXP, LN, LOG10, POWER, SQRT and SQRTPI then share one LN/EXP pass, preceded by fm_pw0 for domain rules.
- Alternatives: call ev_pow2 (not possible: it returns to ev_disp with TP += 2); EXP(x) as e^x through ev_pow2 (loses about |x| ulps); retype and renumber the EXP half (hundreds of SRC edits).
- Why: no renumbering, no added rounding for EXP, one shared core for six functions.
- Affects: if the eval agent fixes ev_pow2, fm_pw1 must be updated by hand the same way. Results within 2^-51 of an integer are snapped (POWER, EXP, LOG10, SQRT), see weights/func/math/fm_pow.md.
- Id note: math agent holds 264..289; proposes 290..295 for the ABI agent's SUM networks (FT_INIT currently maps SUM, fid 441, to 264 = fm_unary, which must change).

## 2026-11-06, Stage 3: logical and information functions (func-logic agent; details in log/func-logic-agent.md)

### LG1 (DECISION): two leaf cores selected by T0, wrapped by ABI entries
- Decided: lg_info (296) computes 18 unary functions in one pass and lg_fold (297) is an AND/OR/XOR accumulator; ABI entries lg_un (299), lg_arg (300) and lg_sheet (303) call them with LR = 257, LP = 0 so the leaf returns straight into FN_RET (no extra step).
- Alternatives: one network per fid (16 ids are not enough for 30 functions); a generator (overkill for one family of one-pass functions).
- Why: the unary functions share every feature (tag one-hot, payload tests), so one wide pass is cheaper than many networks.
- Affects: FUNC_TABLE entries (listed in weights/func/logic/README.md, to be written by FT_INIT).

### LG2 (DECISION): argument streamer with B written to memory
- Decided: lg_arg writes B to [SP, SP + 1] at entry, so argument i is always at SP - 2 (n - i); each argument is fetched by one 2-word block read into a 67-input consumer (lg_cfold 301, lg_csel 302). References are dereferenced by CELL_GET and written back over their slot (T5 = 1 marks "came from a reference").
- Alternatives: a block read of all n - 1 stored arguments (the consumer input length would vary with n); two single reads per argument (2 steps and twice the phases).
- Why: one fixed consumer width serves any n; the written words are above the stack top and FN_RET drops them.
- Affects: nothing outside weights/func/logic. Relies on functions.md sections 2 and 6 (SP, FN_RET dropping arguments).

### LG3 (DECISION): IF family is selection among eagerly evaluated arguments
- Decided: follows F4. Only arguments needed for the decision are inspected and dereferenced; the selected branch is returned as it is (a tag 9 reference stays a reference); unselected errors never propagate. IF without else gives FALSE, an omitted branch gives 0.
- Affects: when OPC 12/13 lazy jumps are emitted, lg_csel's role logic stays valid; only the evaluator skips work.

### LG4 (DECISION): lg_fold counters in T3, T4 (not N0, N1)
- Decided: N0 = n is in the ABI preserve set and N1 is the streamer's argument index.

### Open questions recorded by this entry
- Q-LG1: Excel's ISEVEN / ISODD limit for very large numbers (here |x| > 2^50 gives #NUM!).
- Q-LG2: TYPE of a multi-cell reference (16 here) and ISFORMULA of a non-reference (#VALUE! here).
- Q-LG3: SWITCH text matching needs a case-insensitive string compare (handle equality only for now).
- Result: 7 networks, 8260 dense parameters; tests/output/func_logic 217 pass.

## 2026-11-06, decision C1: borrowing from SynapseWrite
- Decided by the project owner: agents may use architecture ideas and weight values from the sibling project SynapseWrite. Values are carried over by hand only (read and typed, or entered with the Edit tool); no code may extract, convert or generate weights. Each borrowed block's note cites its source.

### F3 (DECISION): a CSV field the parser rejects is stored as text
- Decided: csv_commit stores the field as a text constant when the entry parser rejects it (for example "=1+"), instead of skipping it.
- Alternatives: skip the cell; store #NAME?.
- Why: Excel's open of a CSV never asks for corrections and does not lose data; a malformed formula stays visible as text. Open question Q-F3: verify against Excel.
- Affects: weights/files/csv_commit.wt only.

## 2026-11-06, Stage 4: date and time functions (func-date agent; details in log/func-date-agent.md)

### FD-1 (DECISION): floor division by a constant as one dense row plus ROUND
- Decided: floor(x / d) for integer x is ROUND(c x + b), c close to 1/d, b close to -0.5 + 0.5/d; the margin 0.5/d dominates the rounding of the row, so constants worked out by hand to about 12 digits are exact for all date ranges used.
- Alternatives: DIVMOD_K from encodings/primitives.md (two-sided correction, about 9 layers and 3 step units per division); a lookup by thermometer.
- Why: 3 dense layers and no step units per floor; the many floors of the civil-date algorithms stay cheap and can be merged with the linear rows that form x.
- Affects: every network in weights/func/date.

### FD-2 (DECISION): Hinnant's civil-date algorithms with an Excel quirk layer
- Decided: serial -> date uses days since 0000-03-01 (z = n + 693899 + [n < 60]) with overrides for serial 0 (1900-01-00) and 60 (1900-02-29); date -> serial uses a 250-era year offset and subtracts 1 from month starts before serial 61.
- Alternatives: lookup tables of year starts (thousands of hand-typed constants); day counting loops (thousands of steps).
- Why: one forward pass, constants all derivable by hand.
- Affects: dt_ymd, dt_date; the closed form for Jan 1 in dt_wk and dt_yf follows the same convention.

### FD-3 (DECISION): link in T9/T10 and chained subroutines for multi-date functions
- Decided: entry phases save LR/LP in T9/T10 and call dt_ymd with LR/LP pointing at the next phase of the same function; dt_ymd passes T9/T10 and AS..AR2 through, so dt_pair parks the first date's parts there and needs no memory.
- Alternatives: the RET_STACK push/pop of control.md section 4 (two extra memory steps per call).
- Why: zero memory traffic; DAYS360, DATEDIF and YEARFRAC take 6 steps in all.
- Affects: when encodings/functions.md arrives, its wrapper must not rely on T9/T10 or AS..AR2 surviving these calls.

### FD-4 (DECISION): correctly rounded secs / 86400 in TIME
- Decided: (secs / 675) / 128 with an exact residual from a 2^-26 split of q0, then one correction.
- Alternatives: retyping weights/prim/div.wt (about 140 layers, 10k parameters); a single product secs fl(1/86400) (not always correctly rounded, e.g. 1/3 could be off by an ulp).
- Why: about 15 layers; exact Excel values for every whole-second time.

### FD-5 (DECISION): variable divisors in YEARFRAC by Newton from a power-of-two start
- Decided: y0 = 2^-j from a 13-unit thermometer on Dv, six Newton steps, then the FD-4 residual correction.
- Why: Dv ranges over 360 .. 3 million (multi-year actual/actual), so a fixed start would need about 20 iterations.

### Result
- 8 networks (ids 344 to 350, 353), 18,253 dense parameters. tests/output/func_date: 279 passed.
- Checklist items passing their tests: FN-0112 DATE, FN-0113 DATEDIF, FN-0116 DAY, FN-0117 DAYS, FN-0118 DAYS360, FN-0147 EDATE, FN-0150 EOMONTH, FN-0213 HOUR, FN-0270 ISOWEEKNUM, FN-0307 MINUTE, FN-0315 MONTH, FN-0335 NOW, FN-0413 SECOND, FN-0467 TIME, FN-0474 TODAY, FN-0502 WEEKDAY, FN-0503 WEEKNUM, FN-0515 YEAR, FN-0516 YEARFRAC (as cores, before the function ABI wrapper; text date arguments not coerced).

## 2026-11-06, Stage 9 groundwork: VBA lexer and interpreter (VBA agent; details in log/vba-agent.md, spec encodings/vba.md)

### VB1 (DECISION): token stream with base-64 identifier keys, keywords by exact key plus length
- Decided: identifiers fold to KEY (last 8 characters, base 64, letters case-insensitive) and V = KEY + 2^48 length; keywords are 55 IS_K tests on V against hand-computed constants.
- Alternatives: a keyword trie of states (many networks); a hash with collisions checked by a second pass.
- Why: one forward pass, exact integers below 2^53, no table in memory. Affects: identifiers over 8 characters may collide (same length and last 8 characters).

### VB2 (DECISION): VBA source and VBA strings unpacked, one unit per word
- Decided: SRC and VSTR records hold one UTF-16 unit per word; copies move 8 units per two steps by block operations.
- Alternatives: TEXT_HEAP packing (3 per word) as for cells.
- Why: the lexer reads one char per step anyway and block copies need no repacking. Affects: Range values will convert VSTR <-> packed text at the object model boundary.

### VB3 (DECISION): Variant tags = 16 + VarType, Empty on tag 0
- Decided: Integer 18, Long 19, Single 20, Double 21, Date 23, String 24, Object 25, Boolean 27 (PAY -1/0), Byte 33; Empty uses the Excel blank tag 0.
- Why: VarType is TAG - 16; zeroed frames are Empty with no initialisation. Affects encodings/value.md tags 16..63.

### VB4 (DECISION): stack bytecode, 2 words per instruction, frames on VSTACK; division as a later loop network
- Decided: opcodes in encodings/vba.md section 7; fetch / dispatch / handler, about 3 steps per instruction. ev_div and ev_cat cannot be called (they return to the evaluator dispatcher), so VBA has its own concatenation, and / \ Mod are routed to a not yet written vi_div (434).
- Affects: a request to the eval or prim agent for an LR-returning DIV subroutine would remove the need for vi_div.

### VB5 (DECISION): VBA source is NUL-terminated
- Decided: the lexer ends at a 0 unit; the length word is still written for other readers. Why: saves a length register and a compare per char.

### VB6 (DECISION): networks with payloads use block operations on every step
- Decided: after a non-block step the harness forwards the whole output, so a network with a payload uses a block read of 0 words where it needs no memory access.

### VB7 (DECISION): number text through ev_totext
- Decided: CStr and Print of numbers call the eval agent's ev_totext (110) and unpack its packed result. Affects: VBA shows the Excel General format (differs from VBA for small numbers, below 0.1 VBA uses E notation earlier).

### VB8 (DECISION): memory inside 0x380000..0x3AFFFF
- Decided after FILE_SCRATCH (F2) took 0x3B0000 and up: VSTR 0x399000, DEBUG_OUT 0x39C000, MSG_OUT 0x39E000, VSTACK 0x3A0000..0x3A7FFF, OBJT 0x3A8000.

### Requests to other owners (not applied)
- weights/parse/numconv.wt v66 (`RID - 128 OOR`): use 1024 instead of 128 so callers with ids above 127 (VBA lexer, 391) survive the numbig route for exponents beyond 22.
- An LR-returning DIV (the prim div block with a return tail) for VBA `/`, `\`, Mod.

## 2026-11-06, coordinator fix C2: numconv gate constant
- weights/parse/numconv.wt v66 used RID - 128 OOR, so the out-of-range gate failed for callers with ids above 127 (reported by the VBA agent, whose lexer is at 384 and up). Changed the constant by hand to 2^20, larger than any network id. Parser and VBA tests: 228 passed.

### FD-6 (DECISION, func-date agent): ABI adapter for date functions; core registers moved
- Decided: one adapter pair dt_abi (351) / dt_abi1 (352) serves all 19 implemented date fids (dispatch ROM on T2), dereferences tag 9 arguments by CELL_GET, and calls the cores with LR = 257 so they return straight to FN_RET. Core selectors moved from N0 to N1 and dt_pair's parked n1 from AR2 (word 22, GEN) to P0, to respect the encodings/functions.md preserve set.
- Alternatives: one entry network per fid (19 ids, the block has 16); a finish phase that restores N0 (one more step per call).
- Affects: FUNC_TABLE[fid] = 351 for fids 112 113 116 117 118 147 150 213 270 307 315 335 413 467 474 502 503 515 516 (request to the ft_init owner); flags for those fids (MIN, MAX, volatile bit 1 for NOW 335 and TODAY 474) in fd_w0/fd_w1.
- Result: tests/output/func_date 305 passed (26 through the ABI with the preserve set checked on each).

### FM3 (DECISION): one ABI entry for all fixed-arity math functions
- Decided: fm_ent / fm_arg / fm_go (277..279) stream and dereference arguments (CELL_GET, ev_t2n), then a one-hot over T2 = 64 + fid picks the core and selector; cores return straight into FN_RET (257).
- Alternatives: one entry per family (more ids, the same dereference logic repeated); the logic agent's lg_arg (its consumers are logic-specific).
- Why: 48 fids share three networks; cores keep their simple register contract (A, B, C, T0) and stay unit-testable.
- Affects: FUNC_TABLE must map the 48 fids to 277 (ABI agent's ft_init). Aggregates (PRODUCT, SUMPRODUCT, SUMSQ and other variadic math) need the range scanning of the SUM networks (ids 30..35) and are not served by this entry.

## 2026-11-06, Stage 3 to 4: number format engine (format agent; details in log/format-agent.md)

### F1 (DECISION): one numeric core for General and custom codes
- Decided: fx_dec gives (s, e, m) with m the 15-digit mantissa; fx_rnd rounds m half away from zero at the section's last shown digit with exact integer arithmetic and left-aligns a digit stream M; executors peel digits from M one per step. Scaling by '%' and commas is added to e, not multiplied into x.
- Alternatives: rounding x * 10^k directly (fnum style; gives 1.00 for 1.005 where Excel shows 1.01); a DIGITS bank per format (15 divisions per value).
- Why: Excel rounds the 15-digit decimal value; the decimal exponent route is exact apart from the first decomposition, and needs no N x N one-hot matrices (candidate and exact-complement gates, fx_dec.md).
- Affects: weights/format only. Limits in weights/format/README.md.

### F2 (DECISION): General width in characters
- Decided: W = column width in characters, Wc = min(W, 11), W = 0 means 11 (TEXT). Fixed when it fits; scientific when fixed does not fit or shows fewer significant digits (ties stay fixed).
- Alternatives: pixel fitting with the glyph advances (needs the renderer's font metrics inside the planner).
- Affects: the renderer must pass a character width; pixel calibration is open question Q-F1.

### F3 (DECISION): compiled format records and next-code token words
- Decided: format codes are compiled once per format id into a record in 0xCA00..0xFFFF (README layout); a token word carries its successor's code so fx_fetch routes directly to a one-code executor (2 steps per displayed unit).
- Alternatives: interpreting the code string at every display (the parse state machine would run per cell); a generic executor with all codes (one large network on every step).
- Affects: FMT_TABLE at 0xC000 (proposed carve of FORMAT_STORE, below).

### F4 (DECISION): left-indexed integer and exponent placeholders
- Decided: INT and EXPD tokens store the index from the left; executors compute the index from the right as nint - 1 - jl and nexp - 1 - jl from registers N0 and T3.
- Alternatives: a counting pre-pass or patching tokens after the integer part (extra steps per compile).
- Affects: fx_int, fx_expd, General records.

### F5 (REQUEST, not applied): memory map
- encodings/memory-map.md: FORMAT_STORE 0x8000..0xFFFF is all style records today. The format engine uses 0xC000..0xFFFF (FMT_TABLE, FMT_BUF, General records, compiled records). Proposed: 1024 style records at 0x8000..0xBFFF and style word 0 = format id (FMT_TABLE index). Owner of memory-map.md to decide.

### F6 (REQUEST, not applied): hooks
- weights/kernel/boot.wt: one leaf call of fx_init (199) at boot. weights/ui: call fx_main (198) for cell text instead of ui/fnum (131). Text agent: TEXT via fx_main with W = 0. Built-in format id strings (1..49) to be written at boot or by the file loader.

### Open questions recorded by this entry
- Q-F1: Excel's pixel fitting rule for General (we use characters, max 11).
- Q-F2: whether Excel shows the minus sign for negative values in conditional sections (we always do).
- Result: 29 networks, 23,017 dense parameters. tests/output/format: 139 passed, 2 xfailed (fractions, engineering exponent).

## 2026-11-06 Stage 2: UI on harness v2 block operations (UI agent, second session)

- U6 (fill by scanline). Fills write one block per scanline. Pattern rows come from a 2560-word ROM row (absolute x phase) that is block-read once per fill and then carried in the forwarded state (K = 1344), so each row is one step. Pattern versus line row is selected by routing between two row networks, because an elementwise vector select needs a dense as wide as the row. The full grid with row headers is one block per cell row (gband, 25,600 words, 28 steps).
- U7 (glyph rows). One block write per glyph row (bg behind ink), with the string block-read once. Every glyph row is normalised to 12 digits (R 10^(12 - ADV)) so pixel j is digit 11 - j for every glyph. Only rows f..l with ink are drawn (typed table). Text is always drawn on a freshly filled background.
- U8 (change gate and one-step scan). The incremental frame scans visible cells only when (HEAP_TOP - base) + 2^20 CELL_COUNT changed since the last scan. The scan does hash, probe and compare in one step per cell, with the display-cache row in the forwarded state and the slot block-read. Alternative rejected: per-commit kernel hook (not authorized; also misses recalculated cells).
- U9 (kernel hooks, joint with ABI). boot PC 9 -> FT_INIT (259) with LR 152, LP 0; ev_next batch done -> 153. Authorized by the coordinator; documented in weights/kernel/boot.md and main_loop.md.
- U10 (row repaint and overflow). A changed visible row is repainted whole (gband one step, header cell, then non-blank cells right to left). Left-aligned text overflows into the blank cells to its right; the covered gridlines are filled white first, as in Excel. One rule covers new, cleared and shortened neighbours.
- U11 (display table, coordinator decision). DISPLAY_TABLE at 0x0F2000 + 640 r + 32 c holds the units drawn per visible cell (0-terminated, at most 31). It holds units rather than heap handles because the renderer draws from BUF; once fx_main is used, a handle column can be added.
- U12 (header highlight, edit echo). The active row and column headers are drawn #D2D2D2 with a #217346 label and a green line on the grid side. While typing, the edit text is echoed left-aligned in the active cell (clipped to it) and in the formula bar. The echo invalidates the cell's cache entry so the committed value repaints its row.
- U13 (planned, not built: object-id plane, from SynapseWrite's idea). A full-resolution parallel id plane does not fit: no free region of 1,024,000 words remains (free memory is about 2.09M words in total, and the framebuffer region holds exactly one plane). Proposal: an id plane at quarter resolution (320 x 200 = 64,000 words, one id per 4 x 4 block) in UI_STATE's upper half is not possible either (UI_STATE is 65,536 words and holds the cache, display table and ROM). Recommended: carve 64,000 words from EVAL_SCRATCH or VBA_STATE with a memory-map decision; ids: 0 background, 1..20 column headers, 32..59 row headers, 64 + 20 r + c cells, 1024+ ribbon controls, 2048+ sheet tabs. Fills would block-write the id row alongside the colour row (second block write, one extra step per scanline), so hit testing is one read.
- U14 (planned: glyph cache). Blitting a cached glyph row costs a block read plus a block write (2 steps) against 1 step now, so it does not reduce steps; it would reduce wall time (two small networks of about 10 layers against the 112-layer glyph row network, about 20 us against 105 us per row). Worth doing for repeated digits and header labels if boot wall time matters.

### F7 (DECISION, ABI agent): range precedents expanded to cell edges up to 64 cells (rc_rng 36)
- Decided: rc_scan routes OPC 6 to rc_rng, which records one cell precedent per cell of a range of at most 64 cells, reusing rc_got through rc_scan PC 1 (TP held at TPr - 2, marker 2 TPr + 1 in T10). Larger ranges record none.
- Alternatives: range edges on the sheet record (memory-map section 8; needs recalc to scan them for every cell); expanding every range (A:A is a million edges).
- Why: makes cycles and order inside small ranges right (cir07, SUM over formula cells) with no change to the DFS.
- Affects: weights/eval/rc_scan.wt, rc_rng.wt, recalc.md. Open: large ranges.

### F8 (DECISION, ABI agent): OPC 11 pushes the missing value (8, 0)
- Affects: weights/eval/ev_disp.wt (new class ms, write B.TAG at SP -> ev_push2 PC 1, TP held).

### F9 (DECISION, ABI agent): every function name through the directory
- Decided: wordend sends both function cases (fn2 now also for reference-shaped names) to FN_KEY0 262 -> FN_KEY1 263 -> FN_FIND 38 -> parse 73; not found gives fid 0, or rejects a name that is also a cell reference. The directory is part of boot (FT_INIT 259 -> FD_W0 260 -> FD_W1 261).
- Why: one mechanism for 525 names; the 14-key base-39 match could not grow (10 characters, hand multiplication).
- Affects: parser-only test drivers must run 259 first (tests/output/parse updated). About 9 steps per function name.

### F10 (DECISION, ABI agent): shared range scanner returns counts
- Decided: fs_rng 33 + fs_blk 34 return to (LR, LP) with ACC += sum (2^-8 scale), N1 += numbers, T8 += nonzero numbers, T9 += booleans, T10 += TRUE values; errors go to FN_RET. Documented in functions.md section 8b.
- Open: a value-stream mode (compact list of the selected values in EVAL_SCRATCH) for MIN, MAX, PRODUCT, statistics; not built.

### Results (ABI agent, 2026-11-06)
- Stage 1 SUM cases 14 of 14 pass through the real manifest (rng01..rng16, cir07); tests/output/func: 525 names, 14 function cases, all pass. Stage 1 overall: all except ref12, coe21 (known before).
- Zero page 0x16 TZ_OFFSET reserved for NOW and TODAY (date agent request); ids 30 to 41 recorded in control.md.
