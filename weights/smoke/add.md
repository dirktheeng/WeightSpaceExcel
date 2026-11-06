# Weight block note: weights/smoke/add.wt, layer 1 (dense 7x8)

Hand-written. Not generated. Produced by log/WORKLOG.md entry "2026-11-06 Stage 0: smoke network".

**What it computes.** One dense layer `y = W x + b`, x of length 8, y of length 7. Output: `y = [0, 2, 0, a + b, 0, 0, 1]` where `a = x[1]`, `b = x[2]`. Under the step protocol (harness/FORMAT.md) this means: next network 0, memory write, address 0, value a + b, no I/O, halt.

**Encodings.** Input uses the step protocol input layout: x[0] is the read result slot, x[1..7] are the previous output slots. The test supplies the first input directly and places a in slot 1 and b in slot 2. Output uses the 7 fixed protocol fields and nothing more. Values are plain floats (rule 8).

**Derivation.**
- Row 3 (value): weight 1 on columns 1 and 2, all else 0, bias 0, so y3 = 1*a + 1*b = a + b.
- Row 1 (mem_op): all weights 0, bias 2, the code for write.
- Row 6 (halt): all weights 0, bias 1; the harness halts when halt > 0.
- Rows 0, 2, 4, 5: all zero, so next = 0, address = 0, io = none, io_arg = 0. Next is irrelevant because halt is set.

**Limits.** Exact for any a, b whose float sum is exact. Value is used unrounded. No activation, so no clipping. Input must be length 8.

**Multi-role weights.** None.
