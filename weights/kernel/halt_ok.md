# Weight block notes: weights/kernel/halt_ok.wt (id 3, HALT_OK)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decision K1 in log/WORKLOG.md.

**Computes.** Clean halt. Output words 0..6 = [3, 0, 0, 0, 0, 0, 1] (next self, no memory op, no I/O, halt); words 7..63 = input words 7..63 unchanged. The caller's registers (A, STATUS, PC, ...) survive in the returned vector, which is how output tests read a subroutine's results.

**Layers.** v1 = slice of x0 (a 1-wide source for constants). v2 = dense 7x1, all weights 0, biases [3 0 0 0 0 0 1] (CONST blocks). v3 = slice 0 8 65 (PASS). v4 = concat. Encodings: encodings/control.md sections 1 and 2.

**Parameters.** 14 (7 weights, 7 biases). Steps: 1. Clobber set: words 0..6 only.

**Limits.** None. **Multi-role weights.** None.
