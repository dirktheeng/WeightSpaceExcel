# Note: weights/parse/lnum.wt (id 67)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Phases.** PC 1 integer digits, 2 after '.', 3 after E/e, 4 after exponent sign, 5 exponent digits.
**Accumulation (15-digit truncation, value.md section 4).** full = [SIG >= 15]. A digit d with not full: M' = M + (9M + d) = 10M + d (mul gate gA, M < 10^15 so exact), SIG += [M + d > 0] (leading zeros are not significant), FRAC += 1 after the point. A digit when full: before the point DROP += 1, after it ignored. Exponent digits: EXPV' = 10 EXPV + d (mul gate dE); ESGN = 1 for '-' after E.
**Transitions.** CONT = dI + dF + dot1 + eI + sgn + dE + cm, all disjoint gates (AND rows in v23, biases n - 0.5). Token end (not CONT) in PC 1, 2, 5: formula -> numconv 75; entry (EM) -> const 76 PC 2. Not CONT in PC 3, 4 (bad exponent): formula -> reject 79; entry -> const 76 PC 5 (text). On CONT: consume, read next char, stay. In entry mode ',' is skipped in the integer part (thousands separator, lenient: "1,2" reads 12).
**Limits.** No range check on EXPV (handled by numconv). 1,233 parameters. **Multi-role weights.** X0..X5 number roles (README).
