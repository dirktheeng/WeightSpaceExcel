# Note: weights/parse/spill.wt (id 78)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Computes.** PC k = 0..11: write L(12+k) (word 52 + k) to RSP + k. At PC 11 also RSP += 12 and next = 64 (pentry) with PC 0; otherwise next = 78, PC + 1. A, address register, LR, LP untouched.
**Blocks.** v2, v3: thermometer s_j = [PC >= j], j = 1..11 (biases -(j - 0.5)). v4: one-hot h_k = s_k - s_(k+1) (h0 = 1 - s1, h11 = s11), exact integers. v7: mul of h with L12..L23, so exactly one product is nonzero; v12 row 3 sums them (exact, one nonzero term). addr = RSP + PC (R4). next = 78 - 14 s11; PC' = PC + 1 - 12 s11; v13 RSP' = RSP + 12 s11.
**Limits.** Needs RSP + 12 inside RET_STACK (no overflow check yet; fault 2 is not raised). 12 steps. 400 parameters.
**Multi-role weights.** None.
