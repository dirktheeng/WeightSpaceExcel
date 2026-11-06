# weights/func/core: function calling plumbing (ids 256..263, 30..38)

Hand-written. Not generated. Spec: encodings/functions.md (ABI, FUNC_TABLE, name directory, fid table). Log: log/abi-agent.md; decisions F1..F10 in log/WORKLOG.md. SUM notes: sum.md.

| Id | File | Computes | Params |
|---|---|---|---|
| 256 | fn_call | FN_CALL: next = x0 (the FUNC_TABLE word ev_func read), PC 0, copy | 16 |
| 257 | fn_ret | FN_RET: n >= 1: SP -= 2 (n - 1), B = A, TP += 2, read [TP] -> ev_disp PC 0; n = 0: write B.TAG at SP -> ev_push2 PC 1. MUX_INT gates (M = 2^23) and mul gating for B.PAY | 257 |
| 258 | fn_name | A = #NAME? -> FN_RET | 20 |
| 259 | ft_init | one block write of FUNC_TABLE[0..525] from a typed table (ten fids per line) -> fd_w0 | 1228 |
| 260 | fd_w0 | directory entries 0..217 (A..H): PC 0 K1, PC 1 K2, PC 2 FF, block writes; payload row = [K1, K2, FF] times the phase one-hot | 909 |
| 261 | fd_w1 | entries 218..524 (I..Z), PC 2 returns to (LR, LP) by MUX_INT | 1307 |
| 262 | fn_key0 | block read of 16 name characters at 0x2800 + I - 1 - KLEN -> 263 | 24 |
| 263 | fn_key1 | per-lane code (4 thresholds, one row), mask p < KLEN, K1 and K2 by powers of 100; reference-shaped flag rv (RS = 4, grid bounds) in word 62; first probe K1[262] | 349 |
| 38 | fn_find | binary search: PC 0 compares K1, PC 1 K2 (exact integer differences), PC 2 fid = FF mod 1024 (FLOOR by 1.5 2^52); mid = FLOOR((lo + hi) / 2); not found: fid 0, or reject (next 79, STATUS 1) when rv | 934 |
| 30..35, 37 | fs_* | SUM, see sum.md | 3408 |

**Boot chain.** boot PC 9 (next 259, LR 152, LP 0) -> 259 -> 260 x3 -> 261 x3 -> (152, 0): 7 steps.

**Registering a function.** Edit its entry in ft_init.wt (the line whose comment gives the first fid of the decade); for flags (argument counts, volatile), edit the FF of its directory entry in fd_w0/fd_w1 (FF = fid + 1024 (MIN + 256 MAX + 65536 BITS)). Entries made so far: 30 SUM; 299 (logic) 155 165 256-265 267 268 319 320 334 481 485; 300 (logic) 12 218-221 348 449 514; 303 416 417; 351 (date) 112 113 116 117 118 147 150 213 270 307 315 335 413 467 474 502 503 515 516. Flags set: SUM (1..255), NOW and TODAY (volatile, 0 args).

**Registers on the parser side.** fn_key1 and fn_find use words 56 (K1), 58 (K2), 59 lo, 60 hi, 61 mid, 62 rv (lword's X roles, dead after wordend) and PC; everything else passes through; exit sets TO (53) and, on reject, STATUS (12).

**Limits.** Names longer than 16 characters are matched on their first 16 (four names; a word that agrees on 16 and differs later is accepted). Argument counts are not checked at entry yet (flags mostly 0). =A1(1) rejects; =FOO(1) gives #NAME?.

**Multi-role weights.** fd_w0/fd_w1 payload rows carry three values selected by exclusive phase gates. fn_find's x0 is a K1, a K2 or an FF depending on PC; each role is read only under its phase gate (the FF FLOOR block is computed every step but gated by p2). **Tests.** tests/output/func/test_names.py (all 525 names, case folding, unknown names, reference rejection), tests/output/func/cases.yaml with sumrun.py, tests/output/parse (run the boot chain first).
