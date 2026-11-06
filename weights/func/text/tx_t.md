# tx_t (id 318): T core

Hand-written, not generated. Log: log/func-text-agent.md; WORKLOG Stage 3 Text entry. Conventions: README.md.

**Computes** T(A): text (tag 2) and errors (tag 4) are returned unchanged, anything else becomes "" = (2, TEXT_EMPTY 0x302000). One step, no memory. k = IS2 + IS4 from a 4-step thermometer on TAG; A.TAG' = relu(TAG - M (1 - k)) + 2 (1 - k); A.PAY' = k PAY (mul, since PAY may be any double) + 3153920 (1 - k).

**Limits**: a reference argument (tag 9 / 5) must be dereferenced by the wrapper first; T of a reference to a text cell returns that text in Excel.
