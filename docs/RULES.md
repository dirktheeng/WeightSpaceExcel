# Rules

These rules govern all work on the project. If a situation is not covered, choose the reading that keeps more of the behavior in hand-written weights, and record the decision in the work log.

## 1. Weights are written by hand

Every weight and bias I author is typed into a weight file directly, as a value I worked out.

- Allowed: deriving values by reasoning, algebra and hand calculation; reusing a block I wrote earlier by referencing it.
- Not allowed: training, fine-tuning, gradient descent, evolutionary or random search, distillation, or fitting of any kind.

## 2. No code generates or reasons about weights

I may not write or run any program, script, template, macro, spreadsheet or tool that produces, computes, checks, optimizes or suggests weight values.

- Not allowed: a script that emits a lookup table, a generator that expands a pattern into weights, a checker that searches for values that pass a test, or a calculator script used to compute a weight.
- Allowed: the frozen harness (docs/HARNESS.md), plain text editing, and reading the harness's output after a forward pass.
- Allowed: test code of two kinds, described below.

### Permitted test code

1. **Output tests.** Code that feeds inputs to the networks through the harness and compares their outputs (cell values, memory state, framebuffer, file bytes) with expected results. Output tests treat the networks as black boxes: they never read, inspect, analyze or report on weight values, and they never suggest a fix. A failing output test tells me *that* something is wrong; finding *why* and choosing the new weights is my job.
2. **Compliance tests.** Code that scans the repo to confirm that no conventional code exists beyond what is strictly allowed (the frozen harness and these two kinds of tests), that the harness is unchanged since it was frozen, and that test code stays within these limits. Compliance tests may look at file types, file contents and code structure, but they may not read or evaluate weight values.

Test code contains no application logic and is never called by the networks or the harness during normal operation. The expected results in output tests come from Excel or from the parity documentation, never from computing them with conventional code.

## 3. Networks may build networks

A network may write the weights and biases of another network into memory, where the harness can load them as a network.

- This is allowed because the generator's own weights are hand-written, so every value traces back to something I wrote.
- Generator networks may be used in two ways:
  - **Construction time:** building networks that make up the main program before it runs (for example, compiling each Excel function from a shared library of primitives).
  - **Run time:** writing or rewriting networks while the main program is operating (for example, specializing a network for a particular formula, chart or VBA procedure).
- In both cases, the generation must be started and controlled by a network that is hand-written or derived from a hand-written network. A derived network is one whose weights were written by such a network, at any depth of the chain.
- Every chain of generation must trace back to hand-written weights. No conventional code may start, steer or parameterize generation.
- Generator networks follow every other rule, including documentation.
- Generated weight files are marked as generated and name their generator.

## 4. Small, fast networks built on latent spaces

- Carry information in compact latent encodings (values, types, addresses, operators, glyphs, styles, control state) instead of wide one-hot layouts wherever that makes a network smaller or faster.
- Weights and neurons may serve several roles (superposition, shared subspaces, reuse across functions) as long as every role is deliberate, understood and documented with a non-interference argument.
- Parameter count, network count and forward-pass steps per operation are design goals and are measured (docs/ACCEPTANCE.md).

## 5. Memory is allowed, but networks control it

Networks may use as much external memory as they need: cell store, format store, stacks, scratch buffers, dependency tables, framebuffer, VBA state, file buffers, and storage for generated weights.

- Every address, read/write choice, value written and ordering of accesses is decided by network outputs.
- Access patterns (range scans, graph walks, rasterization loops, iteration to convergence) are network decisions.
- Memory is passive storage. It never computes, indexes, sorts or decides anything.

## 6. The runtime is fixed and generic

A single minimal harness runs everything. Its full specification is docs/HARNESS.md. In brief, it loads weights, runs forward passes, routes outputs between networks, carries out the memory operations networks request, and does mechanical I/O (raw pixels out, raw input events in, raw file bytes in and out). It contains no application logic and is frozen once written. All behavior changes are made in weights.

## 7. Forward passes are for debugging

I may run the networks as often as needed to observe behavior. When something is wrong, I reason through the cause and edit weights by hand. The harness output is evidence for my reasoning, never input to an automated fix.

## 8. Number representation

Floats or integers, whichever is convenient for each part. The choice for each encoding is recorded in the work log.

## 9. Documentation and logging

Every weight block has a note explaining it, and a running work log records each step and every major decision. Formats are defined in docs/DOCUMENTATION.md.
