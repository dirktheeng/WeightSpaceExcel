# Harness v2 agent log (block memory ops, faster engine)

## 2026-11-06, setup and baseline
- Read GOAL.md, docs/HARNESS.md, docs/RULES.md, harness/*, encodings/control.md, memory-map.md, io.md, primitives.md (R1 to R6), tests/compliance, tests/output/blackbox.py, WORKLOG, ui-agent log.
- Saved v1 harness copy to /tmp/hv2/harness_v1 for differential runs.
- Baseline suite (v1, weights at that moment): 318 passed, 246 failed (stage1 cases awaiting evaluator), 14 skipped, 15.4 s. One compliance failure came from tests/output/ui/ui_util.py line 71 (UI agent's file, not mine).
- Benchmark (script outside the repo, /tmp/hv2/bench/bench.py, weights snapshot): boot plus 7 typed cells, and ui_fill (net 128) on a 200 x 60 rectangle. v1: about 31 to 33 us per step untraced, 52 to 65 us traced.
- numba: not installed. Declined anyway: a compiled loop sums dense rows in a different order from OpenBLAS dgemv (checked: a naive sequential sum differs from W @ x on random R5-type rows), so it could not be bit-identical.

## Block op encoding (design)
- mem_op 3 = block write, 4 = block read. addr = start. value (rounded) = K * 2^20 + N, K = output words forwarded, N = run length (each < 2^20).
- Block write: mem[addr + i] = out[K + i], i < N; next input = [0] + out[0:K]. An app network writing a scanline outputs 64 + 1280 words with value = 64 * 2^20 + 1280; its successor still takes 65.
- Block read: next input = [0] + out[0:K] + mem[addr:addr+N] (65 + N for K = 64).
- Bound checks (raise): 0 <= value < 2^40, addr >= 0, addr + N <= MEM_SIZE, K <= len(out), K + N <= len(out) for writes.
- Alternatives rejected: payload as the last N words (variable N would change the forwarded length); hard-coded 64 split (the harness should not know the state width; test networks use 8).
- Trace adds `bwrite A K N` / `bread A K N`; step-line counting unchanged.

## Engine changes
- Preparse each network into (opcode, src, params) tuples; integer dispatch; slice objects precomputed.
- dense: still `W @ v` (same cblas_dgemv call), bias added in place. Elementwise ops unchanged calls.
- concat chains copied once from leaf pieces; concats feeding only concats not materialised (only when all sources are direct earlier indices; otherwise v1 path).
- Fields rounded with Python round on tolist() values (same half-even as v1).
- Trace string building skipped when trace is None (v1 built list(out) every step).
- Parsed-network cache keyed by file bytes (512 files parsed per boot was the dominant cost of the suite).

## Bit-identity checks
- Twin plugin (/tmp/hv2/bench/twin_probe.py): every Harness.run of the full suite executed through v1 and v2 on identical state: 830 runs, 0 mismatches in output, memory, events or trace. No existing network ever issued mem_op 3 or 4.
- Fuzz: 3000 random networks of all layer types, v1 vs v2 forward, 0 mismatches. Negative-src networks checked by hand streams.
- Parse: all 141 .wt files in the snapshot parse to byte-identical layers under the cache loader.

## Block op tests
- Hand-written weights/smoke/blk_w.wt, blk_r.wt, blk_c.wt, blk_line.wt, notes weights/smoke/blk.md. tests/output/test_block_ops.py: 10 tests (round trip, N = 0..3, N beyond payload refused, address bounds, last word, full 1280 scanline in one step built by concat doubling). All pass.

## Speed (process time, same weights snapshot)
- Per step: boot workload 33.0 -> 25.6 us; fill workload 31.6 -> 22.5 to 24.0 us (1.3 to 1.4x). Traced fill 55 -> 42 to 46 us.
- Full suite on the same repo copy: v1 99 to 101 s, v2 92 to 94 s before the file cache, 71 s with it. Remaining 65 s is tests/output/ui/test_ui.py setup (pixel-per-step rendering), which block writes are meant to remove.
- Scanline: 1280 steps -> 1 step, so a full 800-row frame drops from about 1.02 million steps to 800.
