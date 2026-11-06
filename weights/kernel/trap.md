# Weight block notes: weights/kernel/trap.wt (id 1, TRAP)

Hand-written. Not generated. Log: log/kernel-agent.md 2026-11-06, decision K1.

**Computes.** Writes the fault code in T0 (word 29) to FAULT (address 0) and halts: words 0..6 = [1, 2, 0, T0, 0, 0, 1]; words 7..63 copied. Fault codes: encodings/control.md section 7.

**Layers.** v1 = slice [T0]; v2 = dense 7x1: weight 1 on the value row (R1 exact copy of T0), biases next 1, mem_op 2 (write), halt 1; v3 = PASS of words 7..63; v4 = concat.

**Manifest role.** Every unlisted id below 512 is filled with this file by the launcher, so routing to an unknown id writes whatever T0 holds and halts. That makes a bad route visible as a halt with a nonzero (or zero, if T0 was 0) FAULT; a cleaner "unknown route" code 5 would need a separate network, recorded as an open item.

**Parameters.** 14. Steps: 1. **Limits.** T0 must already hold the code. **Multi-role weights.** None.
