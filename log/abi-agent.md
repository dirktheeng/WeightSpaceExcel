# ABI agent log (encodings/functions.md, weights/func/core, ids 256..263, function-name recognition in weights/parse)

## 2026-11-06 session 1: reading
- Read docs/AGENT_BRIEF.md, RULES.md, harness/FORMAT.md, encodings (value, control, memory-map incl. section 13, address, primitives), weights/eval/README.md and evaluator.md, ev_func.wt (stub), weights/parse/README.md and wordend.md, kernel boot.md and cs_hash.md, tail of log/WORKLOG.md and log/eval-agent.md, the Stage 1 SUM cases (rng01..16, cir07).
- Facts that drive the ABI: the parser already emits OPC 64 + fid with fid = checklist FN number (14 names known, base-39 keys, names up to 10 chars); the evaluator keeps TOS in register B and the rest of the operand stack in memory at SP - 2, SP - 1; cell references stay lazy as tag 9 (PAY = K); ranges currently push #VALUE! (ev_push); missing args (OPC 11) are skipped by ev_disp; the occupancy list (NEXTOCC) is not maintained (K-Q3), so range scans cannot walk it yet.
- Plan: (1) write encodings/functions.md first (others wait on it); (2) function-name recognition for all names by a sorted name directory in FUNC_TABLE free space and a binary search; (3) FUNC_TABLE init chain at boot; (4) SUM end to end.
- functions.md written and published (sections 1-9, 525 fids). Core 256 FN_CALL, 257 FN_RET, 258 FN_NAME, 259 FT_INIT written; FT_INIT probe: FUNC_TABLE[0..1023] = 258, [441] = 264, returns to (LR, LP).
- SUM networks (fs_sum, fs_item, fs_cell, fs_rng, fs_blk, fs_uni) written but had taken ids 264..269, which the math agent owns: duplicate manifest id. Removed my 6 lines, moved files to weights/func/core/, not registered. They hard-code each other's ids 264..269 and need 6 new ids before testing.
- Section 4 updated to eval E9 (6-word range record, tag 10 union).
