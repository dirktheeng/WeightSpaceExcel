# Value stream: vs_ent 42, vs_nxt 43, vs_item 44, vs_cel 45, vs_rng 46, vs_uni 47, vs_txt 48

Hand-written. Not generated. Spec and call: encodings/functions.md section 8b (value-stream mode). Log: log/func-agg-agent.md; decision AG1 in log/WORKLOG.md.

**What it computes.** For an aggregate function, the list of selected argument values in Excel order (arguments left to right, ranges row by row) as 4-word entries [TAG, PAY, dr, dc] at SCR upward, with the first error returned directly to FN_RET (257).

**Registers.** CUR 32, E 33, WL 34 (union work list, above E), OUT 35, R2 36, C1 37, C2 38, MD 39, EF 18, VIS 17, R1 15 (B.TAG), CONT 28 (N1), walk address AS, r, c in 19..21 (CELL_GET's address register, which CELL_GET preserves together with B, C, N1 and T2..T10).

| Net | Step |
|---|---|
| vs_ent | ONEHOT of 22 fids (44 step units, thresholds t - k +- 0.5) -> ROM [MD, EF, CONT, A0, ONE] (indicator i = s(2i) - s(2i + 1), so each ROM column is (+v, -v)). Block-writes B at SP. CUR = SP - 2n + 2 + 2 A0; E = SP + 2 - 2 ONE n + 2 ONE + 2 A0 (ONE n by a mul layer; A0 = 1 only where ONE = 1). |
| vs_nxt | wl = [WL > E], more = [E > CUR], gc = more AND NOT wl; addresses by relu MUX_INT (M = 2^23); done -> next = done CONT (mul). |
| vs_item | thermometer s1..s11 on the tag, u2 u4 on MD; nc = 1 - u2, rw = u2 - u4, lg = u4; AND gates by step(a + b - 1.5). Emit tag eT = is1 + 3 is3 - 2 (is3 AND nc) + 2 is2 + 4 is4 + is8 + 7 (is8 AND rw). PAY-dependent words are gated by mul (never MUX_INT, since PAY can be any double). Tag 9: K unpacked by two FLOORs (1.5 2^52 rounding plus a step correction; exact because K < 2^50). |
| vs_cel | the referenced-value table: number emit; boolean [1, b] in MD 1, [3, b] in MD 2..4; text [1, 0] in MD 1 (PAY gated to 0), [2, h] in MD 2, 3; error emit in MD 2, 3, else FN_RET unless EF; blank [0, 0] only in MD 3. Advance with wrap = [c >= C2], c' by relu MUX_INT, fin = wrap AND [r >= R2]. Payload dr = r - R1, dc = c - C1. |
| vs_rng | copies the record into the walk registers, CELL_GET. |
| vs_uni | pushes [right, left] so the left child pops first. |
| vs_txt | number -> emit; else #VALUE! (EF 0) or skip (EF 1). |

**Exactness.** All addresses, counters and offsets are integers below 2^53 (R4). PAY moves only by unit weights or 0/1 mul gates, so values are copied bit for bit.

**Cost.** Per direct argument 2 steps; per range cell 1 step plus CELL_GET (about 4). Params (hand tally from the layer shapes, zeros included): vs_ent 44 + 44 + 225 + 80 + 20 + 10 + 40 + 10 = 473; others not tallied yet.

**Limits.** Whole-column and whole-row ranges cost about 5 steps per cell of the area (a hybrid with the fs_blk store scan is the planned fix). Arrays (tag 6) give #VALUE!. Zero-argument calls (parser should refuse) are not guarded. 3D references not handled. Direct missing arguments count as 0 (MD 0, 1, 4) and as tag 8 entries (MD 2, 3); COUNTA(1,) = 2 assumed, not checked against Excel.

**Multi-role weights.** B.TAG holds R1 during a walk (dead argument word by then). PAY lanes carry numbers, handles and error codes, separated by the tag gates. **Tests.** tests/output/func_agg/cases.yaml (cnt01..cnt06, cta01, cta02): 8 of 8 pass.
