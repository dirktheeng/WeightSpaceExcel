# Weight block note: lg_cfold (id 301)

Hand-written. Not generated. Log: log/func-logic-agent.md.

**Computes.** Block consumer (67 inputs: state, then the fetched argument at inputs 65, 66). One step:
- N1 > N0: finish. next = lg_fold (297), T0 = 4 + [T2 >= 412] + [T2 >= 578] (AND 4, OR 5, XOR 6), LR = 257, LP = 0: lg_fold returns straight into FN_RET.
- argument tag 9: next = CELL_GET (16), address register = unpacked key, T1 = 0, LR = 300, LP = 2.
- otherwise: next = lg_fold, T0 = 2 + T5 (direct, or from a reference), A = argument, LR = 300, LP = 1, N1 = N1 + 1, T5 = 0.
lg_fold's accumulator (C, T3, T4) is carried by every network on the path unchanged (CELL_GET clobbers only T0, T1, P0, A, STATUS).

**Blocks.** v8 to v12 thresholds and four conjunctions; v14 to v33 key unpack retyped from lg_un; v35 output rows (integer, R4). **Limits.** Range (tag 5) and array arguments give #VALUE! (no range scan yet; the core range scanner of functions.md F6 is to be used when it exists). **Parameters.** 294. **Steps.** 3 per argument, + 5 to 7 per reference, + 3 to finish, + FN_RET. **Tests.** test_abi_fold.py (15).
