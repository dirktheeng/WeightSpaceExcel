# Note: weights/parse/ckey.wt (id 77)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Computes.** Scans the whole entry from char 0. Key value v(c) = c - 64 U - 96 L - 8 # - 19 / - 19 0 - 3 ! - 32 ? (maps A..Z and a..z to 1..26, # 27, / 28, 0 29, ! 30, ? 31; written over thresholds). KEY' = 32 KEY + v while KLEN <= 9 (gK, mul gate); a non-key char or an 11th char sets KLEN = 100 and KEY = 0. At END: equality with 11 keys by d = KEY - k (exact integer), eq = 1 - step(d) - step(-d); tag and payload are sum minus the non-matching terms, gated by END (MUX_INT). Found -> restore with A = (3, b) or (4, code); not found -> const PC 5.
**Keys (hand computed, base 32).** TRUE 674469, FALSE 6337125, #NULL! 921350558, #DIV/0! 29135434686, #VALUE! 29730690238, #REF! 28906718, #NAME? 920695999, #NUM! 28792254, #N/A 899969, #SPILL! 29645648286, #CALC! 909160574.
**Limits.** Exact, case-insensitive match of the whole text; no surrounding spaces. Other errors (#FIELD!, #CONNECT! ...) are text as entries. 357 parameters. **Multi-role weights.** X0, X1 (README).
