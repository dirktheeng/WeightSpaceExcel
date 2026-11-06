# Weight block note: lg_fold (id 297)

Hand-written. Not generated. Log: log/func-logic-agent.md. Blocks: GE_K, ROUND, MUX (mul), MUX_INT (relu big-M), encodings/primitives.md.

**Computes.** One step. Accumulator: C = (4, code) of the first error met, or (0, 0); T3 = number of logical values counted; T4 = number of TRUE values. Selector T0: 1 init (C = (0, 0), T3 = T4 = 0); 2 add direct argument A; 3 add value A that came from a reference; 4 finish AND, 5 OR, 6 XOR (result in A). Other T0 values change nothing. Returns next = LR, PC = LP, STATUS = 0. Clobbers words 0 to 7, STATUS, A (finish only), C, T3, T4.

**Add rules (Excel).** Number: counted, TRUE when nonzero. Boolean: counted. Missing argument (tag 8): counted as FALSE. Blank: ignored. Text: #VALUE! when direct (mode 2), ignored when from a reference (mode 3). Tags 5, 6, 7, 9 and higher: #VALUE! (ranges and arrays are not iterated here). Error: recorded if no earlier error. Finish: earlier error -> that error; no logical values -> #VALUE!; AND = [T4 = T3], OR = [T4 > 0], XOR = T4 odd.

**Blocks.** v8, v9 thresholds (tag, selector, pay sign, C tag > 3.5 = "Has", T3 > 0, T4 > 0, T4 >= T3, T3 >= T4). v10 to v15 parity of T4 (h = T4 / 2, r = ROUND(h); odd = [r > h] + [h > r], since h - r is 0 or +-0.5). v17 linear features. v18, v19 conjunctions (tinc = (number or boolean) and nonzero, text-direct, finish results gated by "has values and no error"). v21, v22 Epay = I4 pay. v27, v28 MUX_INT with M = 2^20: (1 - Has) err_new and Has Cp (error codes and counts are small integers). v33 candidates, v35 gates (finish, add, pass, keep), v38 one mul, v39 sums.

**Invariant.** C must be (0, 0) or an error before the first add (init, or lg_arg's entry). **Parameters.** 1533. **Tests.** test_fold.py (16 argument lists x 3 functions), test_abi_fold.py.
