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
2. Reads fixed fields from the output: next network, memory operation (none, read or write), address, value, I/O request, and halt.
3. Carries out exactly what those fields say.
4. Builds the next input vector from the fixed layout (previous output plus any read result).

The harness never decides which network runs, which address is used, when to loop or when to stop. It obeys the fields.

## Memory model

A flat address space of numeric words, with fixed designated regions for the framebuffer, input events, file transfer, clock and entropy. All other layout (cell store, stacks, tables) is defined by the networks and documented in the work log.

## What the harness must never do

Parse anything, render anything, lay out anything, compute an address, interpret file formats, interpret input events, sort, search, loop on its own initiative, or contain any spreadsheet, chart, formatting or VBA knowledge.

## Freezing

The harness is written, reviewed against this document and frozen at the end of stage 0. Any later change needs a decision record explaining why it could not be done in weights.

## Audit

The harness audit in docs/ACCEPTANCE.md checks every line against this specification.
