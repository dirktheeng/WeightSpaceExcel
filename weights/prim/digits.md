# weights/prim/digits.wt: DIGITS(n)

Hand-written. Not generated. Conventions: weights/prim/CONVENTIONS.md. Log: log/prim-agent.md "batch 2".

**Computes.** n = A.PAY, an integer with 0 <= n < 10^15. Words 29..43 = decimal digits d0 (units) .. d14. Used by the number formatter (encodings/value.md section 4).

**Chains k = 1..14 (values 7k - 5 .. 7k + 1).** Each computes f_k = floor(n / 10^k) as in divmod_k.md: q0 = round(fl(n fl(10^-k))) (weight 1e-k, biases +C then -C); the product is within 10^(15 - k) * 2.3e-16 < 0.03 of n / 10^k, so q0 is f_k or f_k + 1; then rows 10^k q0 - n and n - 10^k q0 - 10^k + 0.5 (R4, all terms below 2^53 because 10^k q0 <= n + 10^k < 1.1e15), step gives lo and hi, and f_k = q0 - lo + hi. The chains are independent (parallel, as in primitives.md), each with 1x1, 1x1, 2x2 and 1x3 dense blocks rather than one wide block-diagonal matrix, which keeps the parameters at 14 per chain.
**v100..v113.** concat [n, f1, ..., f14]. **v114 (dense 15x15).** d0 = n - 10 f1, d_k = f_k - 10 f_(k+1), d14 = f14 (exact integers).

**Limits.** 0 <= n < 10^15 (15 digits, the Excel display precision). Negative n is not handled (callers pass |n|). Cost: 28 step units, 436 parameters (196 in chains, 240 in the digit matrix, mostly zeros), 114 layers, all in one forward pass.
**Multi-role weights.** None. **Tests.** test_digits (9 cases incl. 999999999999999 and 100000000000000): pass.
