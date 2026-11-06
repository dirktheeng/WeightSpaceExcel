# Note: weights/parse/shpack.wt (id 121)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06 (session 2); decisions P6 to P10 in log/WORKLOG.md.

**Role.** Collect a sheet name into the sheet key buffer 0x27F0..0x27FF (16 words, memory-map section 13), case-folded (a..z minus 32) and packed 3 units per word like a heap string body, then hand its length N to shlook.
**Registers.** X0 J, X1 END, X2 MODE, X3 SACC, X4 SK, X5 SW, X6 N, X7 QS. Entry from lword at '!' (PC 0: J = TV, END = I) or from idle at an apostrophe (PC 1, J = I + 1, MODE 1, others 0, RDOK 0).
**Gates.** Layer 1 (each needs ph1 = [PC >= 1]): FETCH, U_AP (unquoted, J < END), U_F (unquoted, J = END), QE (quoted, end of text), Q1 (quote, QS 0), Q2 (other, QS 0), Q3 (quote after quote), Q4 ('!' after the closing quote), Q5 (anything else after it). Layer 2: APW (append, word full: write it, next step fetches), APR (append, read char J + 1), FOK (finish, N >= 1), REJ1 (N would pass 31), REJ2 (empty name), P0.
**Debug fixes (log).** In PC 0 the MODE and QS slots still hold lword's COL and CSn, so the layer-1 gates carry ph1 with weight 1 + 2^23 and biases lowered by 2^23. J and N slots hold lword's KEY (up to 8e15) and OPND1 (up to 2^38) in PC 0, so every use of J or N is gated by a mul layer (v44..v52), not by MUX_INT.
**Finish.** Writes the partial word (zeros pad the unused units), I = J + 1 (the char after '!'), -> 122 PC 0 with X0 = 0, X2 = N.
**Limits.** ASCII case folding only. Names of 1 to 31 units (Excel's limit). The characters Excel forbids in sheet names (: \ / ? * [ ]) are not checked inside quotes. **Params.** 2,270. **Multi-role weights.** X0..X7 shpack roles (exclusive by lexer state, README).
