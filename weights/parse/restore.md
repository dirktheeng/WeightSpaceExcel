# Note: weights/parse/restore.wt (id 79)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Computes.** PC 0: read RSP - 12. PC k = 1..12: x0 is L(12+k-1); store it in word 52 + k - 1; read the next saved word (k < 12). PC 12: next = LR, PC = LP, RSP -= 12. A, STATUS, P1 untouched.
**Blocks.** s1..s12 thermometer; v4 holds h1..h12 and 1 - h1..1 - h12; v6 copies x0 twelve times (R1 weight 1); v10 mul gives h x0 and (1 - h) old; v11 adds each pair (one term is exactly 0). next = 79 - 79 s12 + relu(LR + M s12 - M); PC' = PC + 1 - 13 s12 + relu(LP + M s12 - M) (MUX_INT, LR and LP small). addr = RSP - 12 + PC.
**Limits.** 13 steps. Assumes the matching spill ran. 865 parameters. **Multi-role weights.** None.
