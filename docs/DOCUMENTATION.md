# Documentation and logging conventions

## Weight-block notes

Every weight block (a layer, or a named slice of a layer) has a note, kept beside the weight file or in a matching notes file. Each note states:

- What the block computes, in plain terms and as a formula.
- The input and output encodings it expects and produces, with references to the latent layout definitions.
- Why each group of values is what it is (the derivation, not just the numbers).
- Known limits: input ranges, precision, cases it does not handle.
- For generated blocks: which generator network produced it, from what inputs, whether it was made at construction time or run time, and the full chain of generators back to hand-written weights.

## Multi-role weights

When a weight or neuron serves more than one purpose, its note also lists:

- Every role it plays.
- The latent subspace or encoding each role uses.
- The argument for why the roles do not interfere (for example, orthogonal subspaces, mutually exclusive gating, or separated value ranges).
- Which crosstalk tests cover it.

## Latent layout definitions

Each encoding (values, types, addresses, operators, glyphs, styles, control state) has one definition document listing its dimensions, what each dimension or subspace means, and its value ranges. Notes refer to these instead of repeating them.

## Work log

One dated log file in the repo, appended as work proceeds. Each entry records:

- Date and stage.
- What I was trying to do.
- What I changed, naming the weight files.
- What the forward passes showed.
- What I concluded and what comes next.

## Decision records

Major decisions get their own entries in the log, marked as decisions. Each states:

- What was decided.
- The alternatives considered.
- Why this one was chosen.
- What it affects later (encodings, latent layouts, memory maps, network boundaries, generator designs, harness).

When a decision is reversed, the original entry stays unchanged and a new entry records the reversal and the reason. Any change to the harness after it is frozen requires a decision record explaining why the change could not be done in weights.

## Traceability

Every weight block's note names the log entries that produced or last changed it, so a reader can go from any block to the reasoning behind it.
