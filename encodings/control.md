# Encoding: CONTROL (state vector, control words, network ids, calling convention)

Status: design, stage 1. Decision records: log/WORKLOG.md "2026-11-06 Stage 1: shared encodings design", decisions D1 (state width 64), D10 (register map), D11 (calling convention), D12 (network id plan). Related: harness/FORMAT.md (fixed fields 0 to 6), encodings/memory-map.md (zero page, RET_STACK), encodings/primitives.md (ONEHOT, MUX).

## 1. One state width for every network

Every application network outputs exactly **S = 64 words** and takes **65 input words**. Input word 0 is the read result of the previous step (0 if no read); input word i + 1 is the previous output word i. In this document "word i" means output word i, found at input index i + 1 in the next network.

The harness requires each network's input length to equal 1 + the previous network's output length. Since any network may return to any caller, a single width is the only way to keep every pair compatible. Wide pass-through costs no weights: a network that changes a few words builds its output with `concat` of computed pieces and `slice`s of its input (for example, unchanged words 40 to 63 are `slice 0 41 65`), so S = 64 adds compute but no parameters. 64 was chosen over 32 because the register map below already uses 40 words before locals, and over 128 because no subsystem planned so far needs more than 24 locals.

The proof-of-concept networks under weights/poc and weights/smoke use the 8-word test layout and are not application networks.

## 2. Register map

| Words | Name | Role | Saved by |
|---|---|---|---|
| 0 to 6 | next, mem_op, addr, value, io, io_arg, halt | harness fields (harness/FORMAT.md); rounded to integers except value | rewritten every step |
| 7 | PC | phase within the running network or subsystem | set by every step |
| 8 | LR | link: network id to return to | caller (pushes if it needs its own LR later) |
| 9 | LP | link phase: PC to resume with | caller |
| 10 | RSP | return stack pointer, next free word in RET_STACK | everyone preserves |
| 11 | MODE | application mode (section 6) | preserved except by the main loop |
| 12 | STATUS | 0 ok, otherwise a callee result code (for example "not found" from a lookup) | callee sets |
| 13, 14 | A.TAG, A.PAY | value register A (encodings/value.md); first argument and the result | caller-saved |
| 15, 16 | B.TAG, B.PAY | value register B; second argument | caller-saved |
| 17, 18 | C.TAG, C.PAY | value register C; third argument | caller-saved |
| 19 to 24 | AS, AR1, AC1, AR2, AC2, AS2 | address register: cell (AS, AR1, AC1) or range (all six), encodings/address.md section 2 | caller-saved |
| 25, 26 | P0, P1 | pointer registers (memory addresses) | caller-saved |
| 27, 28 | N0, N1 | counters | caller-saved |
| 29 to 39 | T0 to T10 | temporaries; any callee may clobber | caller-saved |
| 40 to 63 | L0 to L23 | locals of the current subsystem | callee-saved |

**Non-interference.** Each word has one owner at a time, fixed by this table and by the call discipline in section 4: arguments and temporaries belong to the callee during a call and to the caller otherwise; locals belong to whichever subsystem is active, and a callee that needs locals spills them first. A network's note lists which words it reads and writes ("clobber set"), and the crosstalk tests in each stage call the same subroutine from two different callers in alternation.

**Words 0 to 6 are not state.** They are rewritten every step and mean something only to the harness. A network may read the previous step's fields from its input (for example, input word 3 + 1 holds the value it wrote last step), but no value is ever kept there across steps by convention, so their harness role never conflicts with storage.

## 3. Phases (PC) inside a network

A network that takes several steps keeps its position in PC. Each step it computes the outputs for every phase it implements in parallel and selects the active one with ONEHOT(PC) and MUX (encodings/primitives.md). Cost grows with the number of phases, so a network is split when it has more than about 8 phases; the split is a routing choice (`next`), not a harness feature. Each network note includes a phase table (PC value, what the step does, next PC, next network).

Phase values are local to a network: PC 3 in the lexer and PC 3 in the evaluator are unrelated. The pair (network id, PC) is the full program counter, which is why the link is the pair (LR, LP).

## 4. Calling convention

**Call.** In one step the caller outputs: next = callee id, PC = callee entry phase (normally 0), LR = caller's own id (a bias constant in its weights), LP = phase at which the caller resumes, and arguments in A, B, C, the address register and P0, P1, N0, N1 as the callee's note specifies.

**Nested call (caller must keep its own link).** If the caller was itself called and still has to return, it saves its link in the same call step, since the memory operation slot of that step is free: mem_op = write, addr = RSP, value = LINK = LR * 2^16 + LP (from its inputs, one dense row), RSP = RSP + 1. Ids and phases are below 2^16, so LINK is exact and unpacks with one FLOOR.

**Return.** In its last step the callee outputs next = LR and PC = LP, with results in A and STATUS. This is a pure copy (dense rows of weight 1), so a return costs no extra step.

**Restoring the link.** At the resume phase, a caller that pushed issues mem_op = read at addr = RSP - 1 and sets RSP = RSP - 1; in the following step input word 0 holds LINK and the caller unpacks it into LR and LP while it continues its work. Before popping it checks RSP > 0x000100 (encodings/address.md rule A1) and routes to TRAP otherwise.

**Return through the stack (trampoline).** A network that wants to return to whatever link is on top of the stack (deep recursion, for example the evaluator calling itself for LAMBDA bodies) issues the pop read and sets next = RET (id 2). RET computes next = floor(x0 / 2^16), PC = x0 - 2^16 * next from input word 0 and copies everything else unchanged. One extra step per such return.

**Spilling locals.** A callee that writes any of L0 to L23 first writes the ones it uses to RET_STACK (one write per step, RSP advancing) and restores them before returning. Most library subroutines are written to use only T and argument registers so they never spill.

**Why a link register plus a memory stack.** Leaf calls are the common case (hash lookup, string compare, allocation), and with a link register they cost zero extra steps to call and return. A stack-only design would cost a write on call and a read plus a step on every return. A register-only design cannot nest. This is the same trade as the ARM link register.

## 5. Network id allocation

Network ids are positions in the harness network list. The launcher (an output test, or later a start script that only lists paths) passes a fixed manifest of exactly 512 hand-written weight file paths, defined in weights/MANIFEST.md (to be created with the first application network). Unused ids in the manifest are filled with copies of the TRAP network path.

| Ids | Owner |
|---|---|
| 0 | BOOT: first network run (`run(0, zeros(65))`); initialises zero page pointers and enters the main loop |
| 1 | TRAP: writes the fault code from T0 to FAULT (address 0) and halts |
| 2 | RET: return trampoline (section 4) |
| 3 | HALT_OK: clean halt |
| 4 to 15 | main loop, event dispatch, network id allocator, generator driver |
| 16 to 63 | memory utilities: cell lookup and write, heap allocation, string operations, dependency edges |
| 64 to 127 | formula engine: lexer, parser, evaluator, operators, coercion, recalculation |
| 128 to 191 | rendering: grid, headers, formula bar, glyph pages (encodings/glyph.md) |
| 192 to 255 | formatting: number format interpreter, styles |
| 256 to 383 | hand-written function networks (FUNC_TABLE maps function id to these or to generated ids) |
| 384 to 447 | VBA |
| 448 to 511 | files (CSV, ZIP, XML) |
| 512 and up | generated networks |

**Generated ids and the harness load rule.** On io 7 the harness replaces network io_arg if io_arg < number of loaded networks, and otherwise appends at the end, whatever io_arg says. So a new id must equal the current count exactly. The allocator network keeps NET_NEXT (zero page 0x05) equal to the count: it starts at 512, a generator obtains an id by calling the allocator (which returns NET_NEXT in A.PAY and increments it), and only that generator's load step may use it. Regenerating an existing network loads into its id (io_arg < count, replace). Ids are never freed (open question Q-C2: reuse lists if run-time specialisation creates many).

## 6. MODE values

0 boot, 1 ready (waiting for input), 2 cell edit, 3 recalculating, 4 rendering, 5 dialog or menu, 6 VBA running, 7 file I/O, 8 generating networks. MODE is set only by the main loop and by subsystem entry networks; other networks pass it through. Its role is dispatch in the main loop and choice of behaviour in shared networks (for example a key event means different things in modes 1 and 2).

## 7. Fault codes (FAULT word)

1 stack underflow, 2 stack overflow, 3 heap full, 4 cell store full, 5 unknown network route, 6 bad phase (PC outside a network's phase table), 7 dependency pool full, 8 staging full. Every network routes an impossible phase to TRAP with T0 = 6; phase decoding treats any PC not in the table as this case.
