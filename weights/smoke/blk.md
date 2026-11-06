# Weight block notes: weights/smoke/blk_w.wt, blk_r.wt, blk_c.wt, blk_line.wt

Hand-written. Not generated. Produced by log/WORKLOG.md entry "2026-11-06, Harness v2: block memory operations and faster engine" (decision H2). Purpose: black-box checks of harness mem_op 3 (block write) and 4 (block read) in tests/output/test_block_ops.py. These are test networks in the small test layout, not application networks (encodings/control.md section 1).

**Protocol used (harness/FORMAT.md).** For mem_op 3 and 4 the value field is `K * 2^20 + N`: the next input is `[0] + out[0:K]`, followed (block read only) by `mem[addr : addr + N]`. A block write copies `out[K : K + N]` to `mem[addr : addr + N]`. All four networks use K = 8, so 8 * 2^20 = 8388608 is the constant part of every value field.

## blk_w.wt (network 0 in the test), layer 1 dense 12 x 9

Input x (length 9): x3 = A, x4 = N, x5 = P0 (placed by the test). Output: `[1, 3, A, 8388608 + N, 0, 0, 0, A, P0, -2, 1e300, 0.1]`.
- Row 0 next: bias 1, routes to blk_r. Row 1 mem_op: bias 3 (block write).
- Row 2 addr: weight 1 on x3. Row 7 carries A to blk_r (weight 1 on x3), since only out0..out7 are forwarded (K = 8).
- Row 3 value: weight 1 on x4, bias 8388608, so value = 8 * 2^20 + N. Exact (R4: integers far below 2^53). N is 0 to 4 in valid tests; N = 5 makes K + N = 13 > 12 output words, which the harness must refuse.
- Rows 8 to 11 payload: row 8 copies P0 (weight 1, R1 exact); rows 9 to 11 are biases -2, 1e300 and 0.1 with zero weights, so each is the bias exactly (0 + c = c). 1e300 and 0.1 check that words are copied unrounded.
- Rows 4 to 6: zero, so no I/O and no halt.

## blk_r.wt (network 1), layer 1 dense 8 x 9

Input: `[0] + blk_w out0..out7`, so x8 = A. Output `[2, 4, A, 8388612, 0, 0, 0, 0]`: route to blk_c, block read, addr = x8 (weight 1), value = 8 * 2^20 + 4 (bias), so the next input is 1 + 8 + 4 = 13 words.

## blk_c.wt (network 2), layer 1 dense 11 x 13

Input: x0 = 0, x1..x8 = blk_r output, x9..x12 = mem[A..A+3]. Output `[0, 0, 0, 0, 0, 0, 1, x9, x10, x11, x12]`: halt (bias 1 in row 6), and rows 7 to 10 copy the read words with weight 1 (R1 exact), so the test sees them in the returned output.

## blk_line.wt, 14 layers

Input: x3 = A, x4 = colour. Layer 1 dense 8 x 9 gives the forwarded words `[0, 3, A, 8389888, 0, 0, 1, 0]`: block write, addr A (weight 1 on x3), value 8 * 2^20 + 1280 = 8388608 + 1280 = 8389888 (bias), halt (bias 1; the write happens before the halt check). Layer 2 slices x4 (the colour) to a 1-word value. Layers 3 to 12 are `concat v v`, doubling the length each time: 2, 4, 8, ..., 1024. Layer 13 joins 1024 and 256 (value 10) into 1280 copies. Layer 14 puts the 8 fields in front: output length 1288, payload out[8:1288]. Concat only copies, so every pixel equals the colour exactly. No weight is repeated by hand 1280 times: the replication is structural.

**Multi-role weights.** None. **Limits.** Test layout only (input 9 or 13), not the 65-word application convention.
