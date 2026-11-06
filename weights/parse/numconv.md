# Note: weights/parse/numconv.wt (id 75)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Computes.** E10 = DROP - FRAC + EXPV - 2 ESGN EXPV (v2 mul, v4 integer row). k = |E10| = relu(E10) + relu(-E10). One-hot of k over 0..22 (thermometer t1..t23 then bidiagonal differences, v9). ROM v10: D = 10^k (exact doubles up to 10^22, typed as decimal integers) and y = fl(10^-k) (typed as 1e-k, parsed to the nearest double). E10 >= 0: P = fl(M D), one correctly rounded multiply. E10 < 0: q0 = fl(M y); Dekker split of q0 and D with 2^27 + 1 (v16..v22); TwoProduct err (v25..v34, each step one IEEE op: mul or a 2-term unit row); r = (M - p) - err, where M - p is exact by Sterbenz; q = q0 + fl(r y). Select by g = [E10 < 0] with a mul MUX (v45..v48). OOR = t23 (k > 22) sets TK = 11.
**Returns** to (X6, X7) with the value in TV.
**Forward passes (log).** 3 E-1 = 0.3, 0.1, 0.2, 0.12, 0.007, 0.33, 1.7, 0.04, 0.69, 0.9, 1.1e-21, 0.123456789012345, 1234567.89012345, 9.99999999999999e-08 all equal the Python literal doubles; 1000, 25, 1500, 0.01, 3.25 exact.
**Limits.** |k| <= 22; beyond that marked out of range. Correct rounding of q0 + r y without a fused multiply add is argued, not proven (Q-P1 analogue); no failure seen. 995 parameters. **Multi-role weights.** None.
