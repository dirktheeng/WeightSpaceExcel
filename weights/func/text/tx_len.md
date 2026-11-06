# tx_len (id 312): LEN core

Hand-written, not generated. Log: log/func-text-agent.md session 1; WORKLOG "2026-11-06, Stage 3: Text function cores". Conventions: README.md here.

**Computes** LEN(A) = number of UTF-16 code units (Excel counts a surrogate pair as 2, so this matches). In: A = (2, h) or (4, e). Out: A = (1, mem[h]) or the error. Clobbers nothing else.

| PC | Step | Next |
|---|---|---|
| 0 | error: return; else read [h] | self PC 1 |
| 1 | A = (1, x0) | (LR, LP) |

**Blocks**: G = [x0 PC LR LP TAG PAY]. Thresholds PC - 0.5 (p1), TAG - 3.5, TAG - 4.5 (error = difference). g = step(0.5 - p1 - e) = "PC 0 and not error". MUX_INT relus (M = 2^23): a = LR (1 - g), b = LP (1 - g), c = PAY (1 - p1). d = p1 x0 by a mul, because in PC 0 x0 is whatever the caller's previous step read and may be any finite double (a relu mux would leak it when x0 > 2^23; covered by test_stale_x0_*). next = a + 312 g, mem_op = g, addr = PAY, PC = b + g; A.TAG' = TAG - p1 (2 becomes 1), A.PAY' = c + d.

**Limits**: argument must already be text (wrapper coerces numbers).
