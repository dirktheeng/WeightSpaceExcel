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
| 1 | mem_op | 0 none, 1 read, 2 write |
| 2 | addr | memory address for mem_op and for I/O request 7 |
| 3 | value | word to write (used unrounded) |
| 4 | io | 0 none, 1 display framebuffer, 2 file in, 3 file out, 4 clock, 5 entropy, 6 input events, 7 load network from memory |
| 5 | io_arg | file id for 2 and 3, network id for 7 |
| 6 | halt | > 0 stops after this step's operations |

Remaining output words are free state for the networks. The next input is `[read result] + previous output` (read result is 0 when no read was done), so a network that follows a network with output length M takes input length M + 1.

Order inside a step: forward pass, memory op, I/O request, then halt check.

## Memory regions (word addresses)

| Region | Base | Size | Contents |
|---|---|---|---|
| framebuffer | 0x100000 | 0x100000 | raw pixel words, sent unchanged to the display |
| input events | 0x200000 | 0x1000 | word 0 = count, then raw event words |
| file transfer | 0x201000 | 0x100000 | word 0 = byte count, then one byte per word |
| clock | 0x301000 | 1 | seconds since Unix epoch |
| entropy | 0x301001 | 64 | random bytes |

Everything else (total 0x400000 words) is laid out by networks.
