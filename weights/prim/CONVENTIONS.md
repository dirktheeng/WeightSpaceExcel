# weights/prim: shared conventions of the primitive test networks

Hand-written. Not generated. Log: log/prim-agent.md; decisions P-D1 and P-D2 in log/WORKLOG.md ("2026-11-06 Stage 1: primitive library").

Every file here is a standalone one-step test network for one block of encodings/primitives.md. The block itself is the middle of the file; the first slices and the final "tail" only adapt it to the 64-word convention (encodings/control.md) so the block can be tested through the harness. To reuse a block, retype its middle layers into the host network and renumber SRC indices (encodings/primitives.md section 3).

- **Input** (65 words): arguments are read from the register map: A.TAG input 14, A.PAY input 15, B.PAY input 17, C.PAY input 19, AS, AR1, AC1 inputs 20 to 22, T0 and T1 inputs 30 and 31.
- **Output** (64 words): words 0 to 6 are [0, 0, 0, 0, 0, 0, 1] (no memory op, halt); results occupy T0, T1, ... (words 29 onward); every other word equals its input word.
- **Tail** (same in every file): a dense 7x1 from a one-word value with zero weights and biases 0 0 0 0 0 0 1 (the protocol fields; the zero weight multiplies a finite value, V1), `slice 0 8 30` (words 7 to 28), the result vector, `slice 0 (30 + k) 65` (the rest), joined by three concats. The tail costs 14 parameters and is not part of any block's cost.
- **Ids**: none. These networks are loaded by path in tests/output/prim/test_prim.py and never routed to, so they take no manifest id (decision P-D2).
- **Parameter counts** in each note count every dense weight and bias written (zeros included), excluding the 14 of the tail.
