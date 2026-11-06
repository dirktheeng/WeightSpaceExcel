# Weight block notes: number to text and concatenation (ids 110..113)

Hand-written. Not generated. Log: log/eval-agent.md; decision E7 in log/WORKLOG.md. Text heap: encodings/memory-map.md section 9.

| Id | File | Computes | Params |
|---|---|---|---|
| 110 | ev_totext | blank -> TEXT_EMPTY; boolean -> writes "TRUE"/"FALSE" (4 writes; the packed words are integer rows linear in the boolean: FAL = 326421774406, TRU = 365077594196, SE = 4522067, E = 69); number -> ev_fmt0 | 498 |
| 111 | ev_fmt0 | General format setup: 31 thresholds 10^k (k = -10..20) give e; exact one-hot (32 rows) selects 10^(14 - e) from a ROM; m = ROUND(|x| 10^(14 - e)); carry when m = 10^15. Fixed layout for -9 <= e <= 14, else d.dddE+xx. Prefix and tail as 4-bit code queues | 1649 |
| 112 | ev_fmt_emit | one unit per step: prefix, then digits (d = DIVMOD_K(m, 10^14), m = 10 (m - 10^14 d)) with the point when dp reaches 0, stopping when m = 0 past the point; then the tail; packs units as ev_decode does; writes header and returns | 3313 |
| 113 | ev_cat | error precedence, then a unit copy loop over both strings (one read per 3 units, one write per unit) into a new string | 4346 |

**Simplest General format and its limits.** Up to 15 significant digits, trailing zeros removed, rounded half even after one scaling multiply (a value within about 0.04 ulp of a 15-digit midpoint can round the other way). Scientific notation for |x| >= 1e15 and |x| < 1e-9, exponent always two digits. Correct only for 1e-10 <= |x| < 1e21 (the threshold bank range); outside it the exponent saturates and the text is wrong (for example 2.5E-12). Strings are never freed (Q-M2).

**Multi-role weights.** The value word of ev_fmt_emit carries ACC, LEN or 1 by exclusive phase gates. **Tests.** test_single_cell & cases, test_diamond_and_text_chain.
