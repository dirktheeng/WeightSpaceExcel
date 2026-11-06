# Weight file format (.wt)

Plain text, whitespace separated. `#` starts a comment to end of line. Line breaks carry no meaning, so a dense matrix is normally typed one row per line.

```
input N                  # length of the network input vector
<layer> ...              # layers, in order; layer k (k = 1, 2, ...) produces value k
```

Value 0 is the network input. Every layer names a source value `SRC` produced earlier. The network output is the value of the last layer.

| Layer | Header | Then | Result |
|---|---|---|---|
| dense | `dense SRC ROWS COLS` | ROWS x COLS weights (row major), then ROWS biases | `W @ v[SRC] + b` |
| relu | `relu SRC` | nothing | `max(v, 0)` |
| step | `step SRC` | nothing | `1 if v > 0 else 0` |
| identity | `identity SRC` | nothing | `v` |
| mul | `mul SRC A B C D` | nothing | `v[SRC][A:B] * v[SRC][C:D]` (gating) |
| slice | `slice SRC A B` | nothing | `v[SRC][A:B]` |
| concat | `concat SRC SRC2` | nothing | `v[SRC]` followed by `v[SRC2]` |

## Memory form (networks written by generator networks)

The same token stream as numbers, starting at a memory address: `N`, then for each layer a type code followed by its header numbers and values, then code `0` to end. Codes: 1 dense, 2 relu, 3 step, 4 identity, 5 mul, 6 slice, 7 concat. A network asks the harness to load it with I/O request 7 (see harness.py): address field = start address, I/O argument = network id to fill.

## Step protocol fields

Every network output starts with 7 fixed fields (rounded to integers, except value):

| Index | Field | Meaning |
|---|---|---|
| 0 | next | id of the network to run next |
| 1 | mem_op | 0 none, 1 read, 2 write, 3 block write, 4 block read (other codes: none) |
| 2 | addr | memory address for mem_op (start address for 3 and 4) and for I/O request 7 |
| 3 | value | mem_op 2: word to write (used unrounded). mem_op 3 and 4: rounded, `K * 2^20 + N` (below) |
| 4 | io | 0 none, 1 display framebuffer, 2 file in, 3 file out, 4 clock, 5 entropy, 6 input events, 7 load network from memory |
| 5 | io_arg | file id for 2 and 3, network id for 7 |
| 6 | halt | > 0 stops after this step's operations |

Remaining output words are free state for the networks. The next input is `[read result] + previous output` (read result is 0 when no read was done), so a network that follows a network with output length M takes input length M + 1.

**Block operations (harness v2, log/WORKLOG.md decision H2).** For mem_op 3 and 4 the rounded value field packs two integers: `value = K * 2^20 + N` with `0 <= K < 2^20` and `0 <= N < 2^20`. K is the number of output words forwarded to the next network, N the number of words in the block.

| mem_op | Memory effect | Next input |
|---|---|---|
| 3 block write | `mem[addr + i] = out[K + i]` for i = 0 .. N - 1 (words used unrounded) | `[0] + out[0:K]` |
| 4 block read | none | `[0] + out[0:K] + mem[addr : addr + N]` |

So an application network (state width 64) that writes one 1280-pixel scanline has output length 64 + 1280 = 1344, puts the pixels at words 64 to 1343, sets value = 64 * 2^20 + 1280, and its successor still takes 65 inputs. A block read with K = 64 and N words gives the next network 65 + N inputs, block word i at input index 65 + i. The harness refuses (raises) unless `0 <= value < 2^40`, `addr >= 0`, `addr + N <= MEM_SIZE`, `K <= len(out)`, and for a block write `K + N <= len(out)`. It copies and does nothing else. mem_op 0, 1 and 2 are unchanged from v1, and a network that never uses 3 or 4 sees exactly the v1 behaviour. Codes 3 and 4 were ignored (no memory operation) in v1; no network ever produced them (checked over the full suite, log/harness-v2-agent.md).

Order inside a step: forward pass, memory op, I/O request, then halt check.

## Trace lines

When a trace list is given: `step S net ID out [...]` once per step, then `read ADDR VALUE` or `write ADDR VALUE` for mem_op 1 and 2, `bwrite ADDR K N` and `bread ADDR K N` for mem_op 3 and 4, and `io IO ARG` for an I/O request. Only `step` lines start with "step", so step counts from traces are unchanged by block operations.

## Memory regions (word addresses)

| Region | Base | Size | Contents |
|---|---|---|---|
| framebuffer | 0x100000 | 0x100000 | raw pixel words, sent unchanged to the display |
| input events | 0x200000 | 0x1000 | word 0 = count, then raw event words |
| file transfer | 0x201000 | 0x100000 | word 0 = byte count, then one byte per word |
| clock | 0x301000 | 1 | seconds since Unix epoch |
| entropy | 0x301001 | 64 | random bytes |

Everything else (total 0x400000 words) is laid out by networks.
