# Goal: Excel, built entirely in weight space

Build a complete spreadsheet application with full parity with Microsoft Excel, using neural network weights written by hand in plain text files. All of the application's behavior must live in the weights: the calculation engine, every built-in function, formatting, charts, the user interface, the VBA language and file handling. Parity covers appearance too: the interface should closely match the visual design and layout of Excel's GUI. The networks should be small and fast and should make heavy use of latent representations.

The project is open-ended and staged. The aim is to see how far it can go, with progress measured against a fixed parity checklist. There is no deadline; correctness and adherence to the rules matter more than speed.

## Core rules (full text in docs/RULES.md)

1. Every weight and bias I author is written by hand. No training, fine-tuning or automated search.
2. No code may generate, compute, check or suggest weight values. I reason them out myself. The only code allowed besides the harness is output tests (black-box checks of results that never read weights) and compliance tests (checks that no other conventional code exists).
3. Networks may write the weights of other networks, both to construct the main program and while it runs, as long as generation is controlled by a network that is hand-written or derived from one.
4. Use compact latent spaces. Weights may serve several roles if every role is deliberate and understood.
5. Networks may use external memory, but network outputs decide every read, write, address and access pattern.
6. A single frozen, generic harness runs forward passes and does mechanical I/O only. It contains no application logic (spec in docs/HARNESS.md).
7. Forward passes are for debugging; fixes are made only by editing weights.
8. Floats or integers, whichever is convenient.
9. Every weight block is documented, and I keep a running work log of steps and decisions (conventions in docs/DOCUMENTATION.md).

## Reference documents

| Document | Contents |
|---|---|
| docs/RULES.md | Full rules, with what is and is not allowed under each |
| docs/HARNESS.md | Specification of the frozen runtime: memory model, I/O regions, step protocol, audit requirements |
| docs/PARITY.md | The parity checklist: functions, formula language, formatting, data features, charts, UI, VBA, files |
| docs/ACCEPTANCE.md | Conformance suite design, tolerances, audits, metrics and progress reporting |
| docs/STAGES.md | Staged plan, with deliverables and exit criteria for each stage |
| docs/DOCUMENTATION.md | Weight-block notes, multi-role weight notes, work log and decision record formats |

## Definition of done

The project is done when every item in docs/PARITY.md passes its tests in docs/ACCEPTANCE.md, the harness and repo audits pass, and every weight block and decision is documented. Until then, progress is reported as the fraction of the checklist passing, by category, at the end of each stage.
