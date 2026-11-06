# Weight block note: brd (id 464) and bz (id 465)

Hand-written. Not generated. Log: log/files-agent.md session 2. Exercised by every inflate, deflate and ZIP test.

**brd (464).** Generic block read: mem_op 4 at addr T8, N = T9, K = 64 (value 64 * 2^20 + T9), next = T10, PC = T7. All other words pass. Purpose: a network whose own step already holds a memory operation (a write) hands the following block read to this shared step instead of a dedicated issuer network, which saves network ids (the files range has 64). Costs one step, the same as a dedicated issuer. 40 parameters.

**bz (465).** Block write of 64 zeros at T8, T8 += 64, T9 -= 1, again while T9 > 1, then next = T10, PC = T7. Requires T9 >= 1. Output 128 words, always mem_op 3 (brief update on payload networks). The zero payload is one zero-weight dense row doubled by six concats (no typed zeros beyond one). Used to zero Huffman count tables (one chunk) and the 4096-word deflate hash head table (64 chunks). 91 parameters.

**Clobbers.** T7..T10 (brd reads them, bz advances T8 and T9). **Limits.** brd's consumer must take 65 + T9 inputs. **Multi-role weights.** None.
