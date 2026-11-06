# Note: weights/parse/lstr.wt (id 70)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Computes.** Packs characters 3 per word into a new heap string at SH (encodings/memory-map.md section 9). scale = 2^(16 SK) = 1 + 65535 [SK >= 1] + 4294901760 [SK >= 2]; newacc = SACC + c scale (mul, exact below 2^48). When SK = 2 the word is written at SH + 2 + SW (appW) and the next step fetches (RDOK 0); otherwise the next char is read in the same step (appR).
**Phases.** PC 1: quote (formula mode) -> PC 2; other char or quote in entry mode -> append; end -> formula reject, entry finish. PC 2: quote -> append a quote, PC 1; anything else -> finish (char not consumed). Finish (fin) writes the partial word SACC; PC 3 writes the length at SH, sets HT = SH + 2 + SW + [SK > 0], TK 1, TO 2, TV = SH (or TEXT_EMPTY 0x302000 for length 0), then -> parse 73 (formula) or const 76 PC 6 (entry).
**Limits.** Reference count word left 0 (open question Q-M2). An empty string still advances HT by 2. 1,454 parameters. **Multi-role weights.** X0..X4 (README).
