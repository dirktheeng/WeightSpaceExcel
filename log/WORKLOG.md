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
