# Note: weights/parse/lrow.wt (id 120)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06 (session 2); decisions P6 to P10 in log/WORKLOG.md.

**Computes.** One step. lnum (formula mode, integer digits, then ':') routes here with M in X0. Output: lword registers for the row-digits state (KEY 0, KLEN 100, COL 0, ROW = M, RS 6, FLAGS 0, OPND1 0, CSn 0), read char I (the ':' again) at 0x2800 + I, RDOK 1, next 68. lword then sees ':' in RS 6 and takes the row-corner colon (crc).
**Blocks.** Three small dense heads over [I, M] (words 0..7, X0..X7, RDOK), the rest PASS slices. **Params.** 51. **Multi-role weights.** None.
