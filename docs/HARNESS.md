# Harness specification

The harness is the only conventional code in the project. It exists to run networks and move bytes. It must be small enough to read in one sitting and must contain no application logic.

## Responsibilities

1. **Load networks.** Read weight files from disk, or from a memory region a generator network has filled, and instantiate them using a fixed set of layer types.
2. **Run forward passes.** Evaluate a network on an input vector and return the output vector.
3. **Route.** Pass outputs to the next network as named by fields in the current network's output.
4. **Perform memory operations.** Execute reads and writes whose address, mode and value fields come from network outputs.
5. **Mechanical I/O.**
   - Display: copy a designated framebuffer region to the screen as raw pixels.
   - Input: write raw keyboard and mouse events into a designated input region.
   - Files: copy raw bytes between a named file and a memory region when a network output asks for it.
   - Clock and entropy: write raw time and random bytes into designated regions for `NOW` and `RAND`.
6. **Trace.** Optionally log every forward pass and memory operation for debugging.

## Layer types

A fixed, small set is chosen at the start and frozen with the harness: dense (matrix plus bias), elementwise activations (for example ReLU, step, identity, and possibly multiply for gating), and concatenation and slicing of vectors. Adding a layer type later counts as changing the harness and needs its own decision record.

## Step protocol

Each step, the harness:

1. Runs the active network on its input vector.
2. Reads fixed fields from the output: next network, memory operation (none, read, write, block write or block read), address, value, I/O request, and halt.
3. Carries out exactly what those fields say.
4. Builds the next input vector from the fixed layout (previous output plus any read result; for block operations the first K output words plus any block read, harness/FORMAT.md).

The harness never decides which network runs, which address is used, when to loop or when to stop. It obeys the fields.

## Block memory operations (v2)

A block write copies a run of output words to consecutive addresses; a block read copies a run of consecutive words into the next input. Start address, run length and the number of forwarded output words all come from the output fields (addr, and value packed as `K * 2^20 + N`); encoding in harness/FORMAT.md. The harness bound-checks the run against memory and against the output length and copies; it never chooses, computes or extends a run. Added by decision H2 (log/WORKLOG.md), approved by the project owner, because one write per step made a 1280 x 800 frame cost about a million steps.

## Engine and bit-identity (v2)

Each network is preparsed once at load into a list of `(opcode, src, params)` tuples holding contiguous float64 numpy arrays, and the forward pass dispatches on small integer opcodes. Results are bit-identical to v1, for these reasons:

- **dense** is evaluated with the same numpy expression as v1: `W @ v` on the same C-contiguous float64 matrix and a float64 vector of the same values, which numpy sends to the same BLAS matrix-vector routine (cblas_dgemv), then `+ b` as one IEEE addition per row. The summation order inside a row is therefore whatever v1 had; nothing that rules R1 to R6 (encodings/primitives.md) depend on can change. The bias add is done in place (`v += b`), which gives the same values as `v + b`.
- **relu, step, identity, mul, slice** are elementwise or pure copies and use the same numpy calls as v1; each element is one correctly rounded operation (or no operation), so order cannot matter.
- **concat** is a copy. A chain of concats is copied once from its leaf pieces, and a concat consumed only by other concats is never materialised. This is done only when every layer names an earlier value directly; otherwise v1's layer-by-layer concat is used unchanged.
- Fields 0 to 6 are rounded with Python's `round` (half to even), as in v1.
- A compiled engine (numba) was considered and not used: it is not installed, and a compiled loop sums dense rows in a different order from BLAS, which changes R5 rows, so it could not be bit-identical. The engine is pure numpy.

Bit-identity was checked by running every harness call in the full test suite twice, through v1 and v2, comparing outputs, memory, events and traces byte for byte (log/harness-v2-agent.md), and by a random-network fuzz of all layer types.

## Memory model

A flat address space of numeric words, with fixed designated regions for the framebuffer, input events, file transfer, clock and entropy. All other layout (cell store, stacks, tables) is defined by the networks and documented in the work log.

## What the harness must never do

Parse anything, render anything, lay out anything, compute an address, interpret file formats, interpret input events, sort, search, loop on its own initiative, or contain any spreadsheet, chart, formatting or VBA knowledge.

## Freezing

The harness is written, reviewed against this document and frozen at the end of stage 0. Any later change needs a decision record explaining why it could not be done in weights. Version 2 (block operations and the preparsed engine) is decision H2 in log/WORKLOG.md, 2026-11-06, approved by the project owner; harness/FROZEN.sha256 was re-frozen for it.

## Audit

The harness audit in docs/ACCEPTANCE.md checks every line against this specification.
