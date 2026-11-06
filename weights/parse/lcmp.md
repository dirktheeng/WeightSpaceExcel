# Note: weights/parse/lcmp.wt (id 72)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Computes.** lt = step(28 - TO) (TO 27 or 29). a = lt and '=' -> TO 28; b = lt and '>' -> TO 26; g = not lt and '=' -> TO 30; TO' = TO + a - b + g, I += a + b + g. next = parse with TK 4 (set by idle). 102 parameters. **Multi-role weights.** None.
