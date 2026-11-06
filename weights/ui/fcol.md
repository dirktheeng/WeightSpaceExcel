# Weight block notes: weights/ui/fcol.wt (id 132, column letters)

Hand-written. Log: log/ui-agent.md.
**Computes.** Writes the column letters for col = T1 (0-based, bijective base 26: A..Z, then AA..ZZ) at P0 + i, then a 0, and returns with P0 at the terminator so that fnum can append the row number (name box).
**Derivation.** hi = floor(c/26) = ROUND(c/26 - 0.48), safe because the fractions are multiples of 1/26; lo = c - 26 hi. Two letters iff c >= 26: 64 + hi, then 65 + lo. Selects are MUX_INT with M = 2^20.
**Limits.** Columns up to ZZ (701); AAA and beyond are wrong. **Parameters.** about 405. **Steps.** letters + 1. **Tests.** test_fcol.
