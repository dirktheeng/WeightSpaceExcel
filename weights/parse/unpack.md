# Note: weights/parse/unpack.wt (id 65)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Computes.** Copies LEN UTF-16 units from the packed heap text (HS + 2 ...) to the char buffer 0x2800 + j. PC 0: if j >= LEN -> pentry PC 4; else read word X1. PC 1: unpack x0 into c0, c1, c2 (UNPACK3), write c0 at 0x2800 + j, keep c1, c2 in X2, X3, X1 += 1. PC 2: write c1. PC 3: write c2. j += 1 on each write.
**Blocks.** UNPACK3: y = w 2^-16 (exact power of two), FLOOR by the 1.5 2^52 ROUND trick (weights/poc/round_floor.md, D5), then again on the quotient; c0 = w - 2^16 f, c1 = f - 2^16 g, c2 = g (R4, exact, w < 2^48). Phase gating by MUX_INT rows q0..q8. The last word may write up to 2 zero units past LEN (inside the buffer, never read).
**Limits.** LEN <= 2047 (buffer 0x2800..0x2FFF). 4 steps per 3 chars. 436 parameters. **Multi-role weights.** X0..X3 roles while unpacking (README).
