# Encoding: PRIMITIVES (library plan of reusable hand-written blocks)

Status: design, stage 1. Decision records: log/WORKLOG.md "2026-11-06 Stage 1: shared encodings design", decisions D5 (ROUND by magic constant), D13 (IEEE-faithful dense rows), D14 (gated mux for doubles, big-M mux for bounded integers), D15 (division by Newton plus exact residual), D16 (generator stamping). Related: encodings/value.md (invariants V1, V2), encodings/control.md (registers, phases).

A primitive is a short sequence of layers with a documented input slice and output slice. Each is written once by hand as a reference block in weights/lib/ (with its note), and then either retyped by hand into a network (renumbering SRC indices, which is plain editing of a block I wrote earlier, rules 1 and 2) or stamped out by a generator network (section 5). Proof of concept so far: weights/poc/round_floor.wt (ROUND and FLOOR), forward passes in its note.

Notation: `fl(.)` is IEEE double rounding to nearest even. `step(x)` is 1 if x > 0 else 0. Layer counts are layers in one forward pass; no primitive needs an extra harness step unless it says so.

## 1. Arithmetic exactness rules (D13)

numpy evaluates a dense row as a dot product followed by the bias add. The summation order inside the dot product, and whether a fused multiply add is used, are not specified. These rules make the result independent of that:

- **R1 (scaling).** A row with exactly one nonzero weight w and bias 0 computes fl(w x). Every zero term contributes an exact 0, whatever the order. This is a correctly rounded multiply by a constant; exact when w is a power of two (barring overflow and underflow).
- **R2 (add, subtract).** A row with exactly two nonzero weights, each +1 or -1, and bias 0 computes fl(x1 +- x2), correctly rounded, the same as Excel's IEEE add. Products with unit weights are exact, so a fused multiply add gives the same result.
- **R3 (bias add).** A row with one unit weight and a bias c computes fl(x + c). This is how ROUND works.
- **R4 (integer rows).** When every input and weight in a row is an integer and every partial sum stays below 2^53 in magnitude, any number of terms is exact (encodings/value.md V2). Addresses, codes and counters use this freely.
- **R5 (everything else).** Rows with three or more real-valued terms, or non-unit weights on more than one term, may round in an implementation-dependent order. They are used only where the result is then rounded to an integer by ROUND, compared with a margin, or where a tolerance of a few ulps is documented.
- **R6 (mul layer).** `mul` multiplies elementwise: fl(a b), correctly rounded.

## 2. Block catalogue

### Copy and constants
- **PASS** (0 layers of weights): `slice` and `concat` assemble outputs from input words. Every network uses PASS for the words it does not change, so pass-through costs no parameters.
- **CONST**: a dense row with zero weights and bias c. Used for ids (LR = own id), base addresses and codes.

### Integer tests (inputs exact integers, V2)
- **IS_K(x, k)**, x == k: dense 2 rows `x - k + 0.5`, `x - k - 0.5`, step, dense 1 row `[1, -1]`. 3 layers, 2 step units. With R4 all exact.
- **ONEHOT(x; k1..kn)**: n parallel IS_K blocks sharing the layers: 2n step units, outputs n indicator words. Used for tags, opcodes, phases (PC) and characters.
- **GE_K(x, k)**, x >= k: `step(x - k + 0.5)`. 2 layers, 1 unit. A bank of these is a thermometer code; differences of neighbours give ONEHOT more cheaply (n + 1 units for n values when the values are consecutive).

### Real comparisons (any finite doubles)
- **GT(a, b)** = step(a - b), with the subtraction in an R2 row. Exact: for finite doubles fl(a - b) > 0 exactly when a > b (gradual underflow makes fl(a - b) = 0 only if a = b). If a - b overflows, the infinity feeds only the step layer, whose output is 0 or 1 (V1 is kept because nothing but step reads that value).
- **GE(a, b)** = 1 - step(b - a). **EQ(a, b)** = 1 - step(a - b) - step(b - a). **SIGN(x)** = step(x) - step(-x).

### Logic on 0/1 words
- **AND(p, q)** = step(p + q - 1.5); **OR** = step(p + q - 0.5); **NOT** = 1 - p (dense); **XOR** = OR - AND. One dense plus one step.

### Select (D14)
- **MUX(g; a, b)** for arbitrary doubles: arrange the value as [g, 1 - g, a, b] (dense for the gates, concat), `mul SRC 0 2 2 4` gives [g a, (1 - g) b], then an R2 row `[1, 1]`. One product is exactly 0 and the other is exactly the selected value, so the sum is exact. n-way: n gates from ONEHOT, one mul over n pairs, one dense row summing them (exactly one nonzero term, so exact under R1 or R4 reasoning). Requires V1: 0 times infinity would be NaN.
- **MUX_INT(g; a)** for integers with |a| < M (M = 2^23 for addresses and fields): `relu(a - M (1 - g)) - relu(-a - M (1 - g))` gives a when g = 1 and 0 when g = 0. Uses relu instead of mul, so it fits into networks whose last layers are dense and relu. Not used for real values: a - M would round and a + M could overflow.
- **Vector MUX**: phase dispatch selects a whole output block per PC value with the same mul layer on many words at once (gates replicated by a dense layer).

### Integer arithmetic
- **INC, DEC, ADD_K, ADD, SUB, SCALE_K**: single dense rows under R4.
- **ROUND(x)**, |x| < 2^51: R3 row `x + C`, then a row `y - C`, C = 1.5 * 2^52 = 6755399441055744. Round half to even. 2 layers. Validated (weights/poc/round_floor.md).
- **FLOOR(x)** = r - step(r - x) with r = ROUND(x). 4 layers plus a concat. Validated. **CEIL(x)** = -FLOOR(-x). **TRUNC(x)** = MUX by SIGN between FLOOR and CEIL.
- **MOD2K(x, k)**, 0 <= x < 2^51: x - 2^k FLOOR(x 2^-k); the scaling is exact (R1, power of two), so the result is exact. Used for hashing, unpacking keys, tokens and characters.
- **DIVMOD_K(x, d)** for a constant integer d: q = FLOOR(x (1/d)) with 1/d as an R1 weight; the product may be off by a tiny relative amount, so q may be one too small or too large; r = x - d q (R4, exact); then q = q - step(-r + 0.5) ... precisely: q = q - [r < 0] + [r >= d], r = r + d [r < 0] - d [r >= d], with the two indicators from GE_K. Exact for 0 <= x < 2^51.
- **DIVMOD(x, d)** for a variable integer d: q from DIV (below), then the same two-sided correction.
- **DIGITS(n)**, 0 <= n < 10^15: parallel f_k = DIVMOD_K(n, 10^k) quotients for k = 1..15 (each an independent block in one wide layer stack), digit d_k = f_k - 10 f_{k+1} (R4). Depth about 6 layers, width about 15 blocks; one forward pass gives all digits.

### Safe real arithmetic (V1 guards)
- **SAFE_ADD(a, b)**: h = fl(0.5 a + 0.5 b) never overflows (two R1-style power-of-two products; the sum is formed in an R2 row of the halves). Overflow of a + b happens exactly when |h| > MAXD / 2 (MAXD the largest double), tested by GT. If not overflowing, the result is an R2 row a + b; otherwise the inputs are gated to 0 by MUX before the add and the block reports overflow, which the operator network turns into #NUM!.
- **SAFE_MUL(a, b)**: s = fl(fl(a 2^-600) fl(b 2^-600)) cannot overflow (each factor is below 2^424). The product overflows when |s| >= 2^-176 (2^1024 scaled by 2^-1200); the boundary is tested with GE. Both inputs are gated to 0 on overflow before the real mul layer. Underflow of s is harmless because it only means the true product is small.
- **SAFE rule**: any block whose output could be infinite is preceded by its guard; the guard result also goes to the caller as STATUS.

### Normalisation and division (D15)
- **NORM(x)**, x > 0 finite: binary exponent cascade. Down stages k = 512, 256, ..., 1: g = GE(x, 2^k); x = x * (1 + g (2^-k - 1)) (factor by dense from g, mul layer; exact because it is a power of two). Up stages k = 512, 512, 256, ..., 1 (512 twice so subnormals as small as 2^-1074 reach range): g = GT(2^(1 - k), x); x = x * (1 + g (2^k - 1)). Exponent e = sum of +-k g (R4). Result m in [1, 2) with x = m 2^e, exact. About 23 stages of 3 layers.
- **RECIP(m)**, m in [1, 2): y0 = 24/17 - (8/17) m (R1 row plus bias; relative error at most 1/17; corrected per decision P-D4, the earlier 48/17 - (32/17) m line is the fit for [0.5, 1]), then 4 Newton steps y = y (2 - m y) (mul, dense, mul). The error squares each step: 1/17, about 3.5e-3, 1.2e-5, 1.5e-10, 2e-20, so y is within an ulp or two of 1/m.
- **DIV(a, b)**, b nonzero: m, e = NORM(|b|); y = RECIP(m); q0 = sign * |a| y 2^-e (scaling split into two power-of-two factors so neither overflows; SAFE_MUL guard for overflow of the quotient). Correction for correct rounding: compute the exact product q0 b as a pair (p, err) with Dekker's TwoProduct (split by the constant 2^27 + 1 in an R1 row, then R2 rows and mul layers, every operation a single IEEE operation); r = fl(fl(a - p) - err), where a - p is exact by Sterbenz because p is within a factor 2 of a; q = fl(q0 + fl(r y 2^-e)). About 60 layers in one forward pass. Whether this is correctly rounded in every case without a fused multiply add is open question Q-P1; it must at least make `=6/3=2` and similar exact quotients exact, which holds because q0 is then within an ulp of an exactly representable q and the residual correction moves it there.
- **SQRT, EXP, LN, POW, trig**: stage 3 plan, the same pattern: NORM to a reduced range, a polynomial in Horner form (mul and R2 rows, hand-derived coefficients such as Taylor coefficients 1/n!), and scaling back. Not designed in detail yet.

### Memory and table blocks
- **HASH(sheet, row, col, ns)**: encodings/address.md section 4; one R4 dense row, one MOD2K, one dense row for the address.
- **ROM(i; table)**: ONEHOT(i) over the table's indices, then a dense layer whose column j is entry j. Exact (one nonzero term per row). Cost: 2n step units plus n times the entry width in weights. Used for glyph bitmaps, character classes, operator precedence, format code tables.
- **DISPATCH(i)**: next = BASE + i (one dense row). A table lookup done by routing instead of weights: zero parameters, one step. Used for FUNC_TABLE entries (where the id is read from memory) and glyph pages.
- **UNPACK3(w)**: three UTF-16 code units from a heap word: c0 = MOD2K(w, 16), w1 = (w - c0) 2^-16 (exact), c1 = MOD2K(w1, 16), c2 = (w1 - c1) 2^-16.
- **LOOP**: a counter in N0 or N1 compared with a limit by GE_K or GT, choosing PC (continue) or the exit phase. Loops cost one step per iteration because a memory operation is needed per iteration in almost every loop.

## 3. Composition rules

- A network's layers are numbered values; a block inserted into a network uses consecutive value indices, and its SRC fields are written relative to the block's first value. Retyping a block is renumbering only.
- Blocks that consume a possibly infinite value must be step layers (V1). Blocks that need V2 state their integer range in their note.
- Parallel blocks share layers by stacking rows of the same dense layer; this is how a network computes all phases at once and then selects with vector MUX.

## 4. Cost reference (approximate)

| Block | Layers | Step or relu units | Weights (nonzero) |
|---|---|---|---|
| IS_K | 3 | 2 | 4 |
| ROUND | 2 | 0 | 2 |
| FLOOR | 5 | 1 | 6 |
| MUX (doubles, 1 word) | 3 | 0 | 4 |
| DIVMOD_K | about 9 | 3 | about 14 |
| NORM | about 70 | 23 | about 100 |
| DIV | about 140 | about 25 | about 200 |

These are planning figures, replaced by actual counts in each block's note.

## 5. Generator stamping (D16)

A generator network writes a memory-form network (harness/FORMAT.md) into WEIGHT_STAGING, one token per step, and then requests io 7. Its weights are hand-written, so every generated value traces back to them (rule 3).

**Structure of a generator.** Registers: N0 = token index i within the current template segment, N1 = segment, P0 = write address (STAGING_TOP + running offset), parameters in A, B, C and the T registers. Each step writes one token: mem_op = write, addr = P0, value = v(i, params), P0 = P0 + 1, and advances i or the segment.

**Computing token values.** Three kinds of segment, chosen to keep the generator small:

1. **Fixed header tokens** (layer type codes, SRC, sizes): a ROM over i with a handful of entries, or bias constants selected by ONEHOT on a short counter.
2. **Parameter tokens**: a weight or bias that equals a parameter or a linear function of parameters (a threshold k in IS_K, a base address, a network id), selected by ONEHOT(i) and copied from a register by MUX.
3. **Patterned matrices**: a dense block written row by row with two counters (r, c); the weight is a small function of (r, c) computed by compare blocks, for example `[c == r + offset]` for shifted pass-through or `[c == src] * coefficient` for a gather. The generator never holds the matrix; it holds the rule.

**Keeping generated networks small.** Because pass-through uses slice and concat, a generated network is mostly a few small dense blocks plus headers, so the token count (and the steps to write it) stays in the hundreds rather than the thousands. A full 64 x 65 dense layer (4225 tokens) is avoided.

**Planned generators.** Stage 1: an operator specialiser (a straight-line evaluator network for one formula's RPN stream, run time, cached per formula record). Stage 3 onward: a function compiler that stamps function networks from a per-function description table of primitive calls. Each generator's note documents its templates; each generated network is marked generated in its memory-form provenance (generator id and inputs) recorded in the work log, since the generated network has no file of its own (open question Q-P2: how generated networks are documented when they exist only in memory).
