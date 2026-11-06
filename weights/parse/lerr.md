# Note: weights/parse/lerr.wt (id 71)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Computes.** After '#': key chars (letters folded, '/' 27, '0' 28; v = c - 64 U - 96 L - 20 / - 20 0) accumulate KEY' = 39 KEY + v up to 10 chars; '!' or '?' ends the literal and is consumed; any other char ends it unconsumed. Match against 13 keys by exact differences (as in ckey); found -> parse with TK 1, TO 4, TV = ERROR.TYPE code; else reject.
**Keys (hand computed, base 39).** NULL 862887, DIV/0 9822178, VALUE 50974097, REF 27579, NAME 832499, NUM 22126, N/A 22348, SPILL 44918652, CALC 179949, FIELD 14422594, CONNECT 11942820650, BLOCKED 8155074412, UNKNOWN 75183059810.
**Limits.** The terminator is not checked against the name (#NAME! is read as #NAME?, #NULL without ! accepted). #GETTING_DATA unsupported. 509 parameters. **Multi-role weights.** X0, X1 (README).
