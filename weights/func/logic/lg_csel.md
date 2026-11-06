# Weight block note: lg_csel (id 302)

Hand-written. Not generated. Log: log/func-logic-agent.md.

**Computes.** Block consumer for IF (T2 282), IFERROR (283), IFNA (284), IFS (285), SWITCH (513). Arguments are evaluated eagerly by the evaluator (decision F4), so "lazy" here means that only the selected branch is used and only the arguments needed to decide are looked at (an unselected error never propagates; an unselected branch is never dereferenced). State: T3 = 1 means "return the next argument fetched"; C = SWITCH expression.

Roles of argument i (n = N0, a = the argument):
- i > n: IF -> FALSE; IFS, SWITCH -> #N/A.
- T3 = 1: return a as it is (references stay references, functions.md section 6); a missing argument returns 0.
- Condition (IF i = 1, IFS odd i): tag 9 -> dereference. Error -> return it. Text, range, array -> #VALUE!. Nonzero number or TRUE -> T3 = 1, fetch i + 1. Zero, FALSE, blank, missing -> IF: T3 = 1, fetch i + 2; IFS: fetch i + 2.
- Tested value (IFERROR, IFNA i = 1): tag 9 -> dereference. Error (IFNA: #N/A only) -> T3 = 1, fetch i + 1; else return a.
- Expression (SWITCH i = 1): tag 9 -> dereference; error -> return it; else C = a, fetch 2.
- Case value (SWITCH even i < n): tag 9 -> dereference; error -> return it; equal to C -> T3 = 1, fetch i + 1; else fetch i + 2. Default (SWITCH even i = n): return a.

**Blocks.** S1 (v8, v9): thresholds on T2, the argument tag (0..10), its payload (= 7, = 0), i against n, i >= 2, C's tag (0..10), and Cp versus ap both ways. v10 to v16 parity of i (as in lg_fold). L1 (v20): linear features; tag equality uses d' = (C tag with blank as number) - (a tag likewise), written as sums of thermometer bits (tag = sum of [tag >= k] for k >= 1, plus [tag = 0]), so d' = 0 exactly when the classes agree. S2, S3, S4 (v21 to v28): conjunctions, each a step of a sum of 0/1 features minus (count - 0.5). Q (v30): 8 exclusive action gates. v36 to v39 one mul for the gated values; v42 output rows; v43 to v62 key unpack.

**Limits.** SWITCH compares text by handle (the same string object), not by content: two different strings with equal text do not match (needs a string compare; ev_scmp or a text-agent helper). Blank matches number 0 but not FALSE or "". Numbers compare exactly (Excel's SWITCH uses the = comparison). Text "TRUE" as an IF condition gives #VALUE!. Ranges as conditions give #VALUE! (no implicit intersection).

**Parameters.** 3199. **Steps.** 3 per argument looked at (fetch, consume) + 1 entry + FN_RET; a reference adds 5 to 7. **Tests.** test_abi_sel.py (45).
