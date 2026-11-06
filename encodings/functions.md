# Encoding: FUNCTIONS (function ids, FUNC_TABLE, calling convention for worksheet functions)

Status: design, stage 3 (written 2026-11-06 by the ABI agent; log/abi-agent.md, decisions F1 to F8 in log/WORKLOG.md). Related: encodings/control.md (registers, ids), encodings/value.md (tags), encodings/memory-map.md (FUNC_TABLE, token stream, section 13), weights/eval/evaluator.md (operand stack), weights/func/core/README.md (the core networks named here).

Every worksheet function is a network (or a short chain of networks) that the evaluator enters through FUNC_TABLE and that returns through one fixed network, FN_RET. This document fixes what a function network may assume on entry, what it must leave on exit, and how ids are assigned. Function writers need sections 2 to 7; section 9 is the fid table.

## 1. Function ids (fid)

- **fid = the checklist FN number** (checklist/CHECKLIST.csv, id FN-0001 to FN-0525 has fid 1 to 525). The parser already emits these (memory-map section 13), so a function keeps one number in the checklist, the token stream and FUNC_TABLE.
- **fid 0** is the unknown function: a name followed by '(' that is not in the directory. FUNC_TABLE maps it to FN_NAME, which returns #NAME?.
- Rows FN-0526 to FN-0532 are TEXT format-code features, not functions; they use fid 462 (TEXT). FN-0522 to FN-0525 (COPILOT, PY, IMPORTCSV, IMPORTTEXT) get their fids so that their names parse; until a scope decision they map to FN_NAME.
- fid < 1024 (FUNC_TABLE section 3), and OPC = 64 + fid < 1088 in the token stream.
- New functions (later Excel versions) take fids 526 upward in order of addition, recorded here.

## 2. Calling convention (entry)

The evaluator meets token OPC = 64 + fid with OPND = n (argument count, 0 to 255). All n arguments have already been evaluated (section 5) and sit on the operand stack in order. ev_func (id 116) reads FUNC_TABLE word fid and hands the network id to FN_CALL (256), which routes to it. **On entry to a function network** (its PC 0):

| Word | Name | Contents on entry |
|---|---|---|
| 7 | PC | 0 |
| 15, 16 | B | argument n (the last one), if n >= 1; if n = 0, B is the previous top of stack and must be left alone |
| 27 | N0 | n |
| 31 | T2 | 64 + fid (lets one network serve several fids, for example a family) |
| 53 | SP | operand stack pointer: argument i (1 <= i <= n - 1) has TAG at SP - 2 (n - i) and PAY at SP - 2 (n - i) + 1 |
| 52 | TP | address of the function token (do not change) |
| 56 | SCR | next free word in EVAL_SCRATCH (bump; a function that allocates advances it) |
| 23 | HT | next free word in TEXT_HEAP (a function that makes a string writes it at HT and advances HT) |
| 54, 55 | HR, HC | row and column of the cell being evaluated (for ROW(), COLUMN(), implicit intersection) |

Argument order in memory is left to right at increasing addresses: argument 1 is the deepest, at SP - 2 (n - 1). Reading argument i costs one read of TAG and one of PAY, or one block read (mem_op 4) of all n - 1 stored arguments: addr = SP - 2 (n - 1), N = 2 (n - 1).

**Preserve set.** A function must return with these words exactly as it found them: 10 and 11 (RSP balanced, MODE), 22 (GEN), 24 (CYC), 26 (P1), 27 (N0 = n), 40 to 63 (kernel locals L0 to L11 and the evaluator registers TP, SP, HR, HC, CS, DEPTH, FLI, FLN, LOW, CIRCV, RET), except that it advances 56 (SCR) and 23 (HT) when it allocates. **Free to clobber:** 8 and 9 (LR, LP), 12 (STATUS), 13 to 21 (A, B, C, address register), 25 (P0), 28 to 39 (N1, T0 to T10). A function that needs more working words spills L words to RET_STACK (one block write) and restores them before returning, or uses EVAL_SCRATCH above SCR as a private frame (it is reset after each top-level evaluation).

**Sub-calls.** LR and LP are free for the function's own calls (CELL_GET, coercion helpers) because the return to the evaluator never uses them (section 6). A function that calls a subroutine which itself needs LR follows control.md section 4 (push the link on RET_STACK).

## 3. FUNC_TABLE (0x007000 to 0x007FFF)

| Address | Contents |
|---|---|
| 0x7000 + fid, fid 0..1023 | network id implementing fid (FN_NAME 258 while not implemented) |
| 0x7400 + j, j 0..1023 | K1[j]: name directory entry j, key word 1 |
| 0x7800 + j, j 0..1023 | K2[j]: entry j, key word 2 |
| 0x7C00 + j, j 0..1023 | FF[j] = fid + 1024 F: entry j's fid and its flags word F |

Deviation from encodings/memory-map.md section 2 (decision F3): the flags word is not at 0x7800 + fid but packed with the fid in the directory entry, because only the parser needs the flags (argument count check, volatile bit into the formula record) and it reads them in the same step that gives it the fid. This frees two 1024-word areas for the directory.

**Flags word F** = MIN + 256 MAX + 65536 BITS (F < 2^20, so FF < 2^30, exact), with MIN and MAX the minimum and maximum argument counts (MAX 255 for "up to 255"). BITS: 1 volatile (RAND, NOW, TODAY, OFFSET, INDIRECT, CELL, INFO, RANDBETWEEN, RANDARRAY), 2 lazy (section 5), 4 error tolerant (the function inspects error arguments itself: IFERROR, IFNA, ISERROR, ISERR, ISNA, ERROR.TYPE, TYPE, the IS functions, AGGREGATE), 8 needs a reference at some position (ROW, COLUMN, OFFSET, AREAS, CELL, ISREF, SUBTOTAL, AGGREGATE, FORMULATEXT, ISFORMULA, SHEET). F = 0 means "not yet described" and the parser then accepts any argument count; each function's owner fills in F when the function is built (a hand edit of that entry in fd_w0.wt or fd_w1.wt, or a FUNC_TABLE write by its generator). Until the parser checks counts, a function network must tolerate any n and return #VALUE! (or what Excel's evaluator would) for counts Excel would refuse at entry.

**Name directory (decision F3).** Function names are recognised by key. A name c_1 .. c_L is mapped character by character to two-digit codes: '.' 10, '0' to '9' 11 to 20, 'A' to 'Z' (and 'a' to 'z', folded) 21 to 46, '_' 47. The codes keep the ASCII order of upper-case names. Key words, read as decimal digit strings:
- K1 = codes of characters 1 to 8 side by side, padded on the right with 00 to 16 digits (SUM: 39 41 33, K1 = 3941330000000000);
- K2 = codes of characters 9 to 16 the same way (0 for names of at most 8 characters).
K1, K2 <= 4747474747474747 < 2^53, exact. Every key is the plain transcription of the letters, so a key is checked by reading it, with no arithmetic. Entries are sorted by (K1, K2) ascending, which is ASCII order of the names with '.' before digits before letters; lookup is a binary search (FN_FIND, 263). Four names are longer than 16 characters (CUBEMEMBERPROPERTY, FORECAST.ETS.CONFINT, FORECAST.ETS.SEASONALITY, FORECAST.ETS.STAT); characters 17 onward are not part of the key, which still separates every pair of names (no two names share their first 16 characters), but a word that agrees with one of these four on 16 characters and differs later is accepted as that function (documented limit).

## 4. Argument kinds

Every argument is a value (TAG, PAY), encodings/value.md. The kinds a function can receive:

| TAG | Argument | Notes |
|---|---|---|
| 0 | blank | only as the value of an empty cell after dereference |
| 1, 2, 3, 4 | number, text, boolean, error | a literal or a computed scalar ("direct" argument) |
| 5 | range reference | PAY = address of a reference record in EVAL_SCRATCH (below) |
| 6 | array | PAY = address of an array record: [rows, cols, then rows * cols values of 2 words, row major] |
| 7 | lambda | PAY = lambda record (stage 4) |
| 8 | missing | an omitted argument (OPC 11 in the token stream, IF(A1,,1)) |
| 9 | single-cell reference, not dereferenced | PAY = packed key K (encodings/address.md section 3; NS 0) |

**Reference record (tag 5)** (eval decision E9, as built by ev_rng 88): 6 words in EVAL_SCRATCH [S, R1, C1, R2, C2, S], normalised (R1 <= R2, C1 <= C2, 0-based absolute). Whole column R1 = 0, R2 = 1048575; whole row C1 = 0, C2 = 16383.
**Union (tag 10)**: PAY points to a node [left TAG, left PAY, right TAG, right PAY]; children may be tags 9, 5 or 10 (nested unions). A function walks it left first.

**References are never pre-dereferenced (E6).** Every function receives references as references (tag 9 or 5) and decides what to do. Helpers do the common cases (weights/func/core/README.md and the library networks of each family):
- **Scalar argument** (ABS(x), LEFT(t, n)): tag 9 is read with CELL_GET; tag 5 with one cell is the same; tag 5 with more cells is implicit intersection with (HR, HC) for now (legacy behaviour; dynamic-array lifting is stage 4 and will change this row only).
- **Aggregate argument** (SUM, AVERAGE, MAX, COUNT ...): see section 7, value classes.

## 5. Evaluation order and lazy arguments (decision F4)

All arguments are evaluated before the function runs, left to right (eager RPN). This gives Excel's results for IF, IFERROR, IFS, CHOOSE, SWITCH, AND/OR and LET because the token stream has no side effects: an error or a slow branch that is not selected is computed and then discarded, and the function returns the selected value. Two observable differences are known and accepted for now: cost (the unused branch is computed), and volatile functions in an unused branch (RAND is still drawn; no visible difference). Circular references through an unselected branch are reported by Excel too (it records the dependency), so they agree.

Reserved for a later speed-up (not emitted yet): OPC 12 "jump if false" (OPND = token offset) and OPC 13 "jump" (OPND = offset), which a lazy function's parser rule would place around its branches, and flag bit 2 (lazy) in F to tell the evaluator to expect them. Functions must not rely on eager evaluation of their arguments beyond what Excel itself guarantees.

## 6. Results and return (FN_RET, 257)

A function returns in one step with **next = 257, PC = 0, result in A** (13, 14), N0 = n unchanged, SP unchanged from entry, preserve set intact. FN_RET (one step) then:
- n >= 1: SP = SP - 2 (n - 1) (the stored arguments are dropped), B = A (the result becomes the top of stack), TP = TP + 2, read [TP] and go to ev_disp (96) PC 0;
- n = 0: write B.TAG at SP and go to ev_push2 (98) PC 1, which writes B.PAY, advances SP and TP, and sets B = A (the result is pushed above the old top).

A result is always one value. Arrays are returned as tag 6 (record in EVAL_SCRATCH); spilling is the evaluator's job (stage 4). A function that wants to return a reference (INDEX, OFFSET, INDIRECT, CHOOSE over references, IF returning a range) returns tag 9 or tag 5; the evaluator dereferences at the end of the formula (ev_end) or passes it on to the next function.

**Errors.** A function's result is an error value (TAG 4, PAY code). There is no out-of-band error channel; STATUS is not read by FN_RET.

## 7. Error propagation and value classes (Excel rules functions must follow)

- **Default (no flag bit 4):** if any argument the function uses is an error, the result is the first such error in argument order (left to right); inside a range or array, the first in row-major order (row by row, then column). An argument the function does not use (the unselected branch of IF, CHOOSE beyond the index) does not propagate.
- **Error tolerant functions (bit 4)** see errors as ordinary values.
- **Aggregate value classes** (SUM, PRODUCT, AVERAGE, MIN, MAX, COUNT, STDEV and friends without the A suffix), per argument:
  - direct number: used; direct boolean: coerced (TRUE 1, FALSE 0); direct text: coerced by the number lexer (ev_t2n, 109), #VALUE! if it is not a number; direct missing (SUM(1,)): 0 for SUM; direct error: propagates;
  - number in a referenced cell or array element: used; text, boolean or blank in a referenced cell or array element: ignored; error in a referenced cell or array element: propagates.
  - The A variants (AVERAGEA, MAXA, COUNTA ...) count referenced text as 0 and booleans as 0/1; each family note states its row of this table.
- **Coercion of a scalar argument** follows the evaluator's operator coercion (TRUE 1, FALSE 0, blank 0 or "", text through ev_t2n).
- **Range scans** use the cell store directly (weights/func/core/README.md, section "range scan"), so the cost of a range argument does not depend on the range's area.

## 8. Network ids

| Ids | Use |
|---|---|
| 256 | FN_CALL: next = x0 (the FUNC_TABLE word ev_func read), copy the state |
| 257 | FN_RET: section 6 |
| 258 | FN_NAME: returns #NAME? (fid 0 and every not yet implemented fid) |
| 259 | FT_INIT: boot-time FUNC_TABLE initialisation chain (fills 0x7000 + fid with 258 and writes the implemented entries), then the directory writers, then returns to (LR, LP) |
| 260, 261 | FD_W0, FD_W1: name directory writers (block writes of hand-typed keys) |
| 262 | FN_KEY: parser side, builds (K1, K2) of the word just lexed (block read of the character buffer) |
| 263 | FN_FIND: parser side, binary search of the directory, returns the fid |
| 264 to 295 | math and trigonometry (including the shared range scanner and SUM) |
| 296 to 311 | logical and information |
| 312 to 343 | text |
| 344 to 359 | date and time |
| 360 to 383 | lookup and reference |
| 512 and up | generated networks (Block G in section 9, and any overflow of the hand-written blocks: 80 math functions share 32 ids, so one network serves several fids by T2, for example a unary-math network for ABS, SIGN, INT, and families such as the trigonometric functions come from a generator): families too large for the hand-written budget (statistical distributions, financial, engineering, database, compatibility aliases, cube, web) are written by hand-written generator networks per RULES.md rule 3, which take ids from the allocator (control.md section 5) and write FUNC_TABLE entries for their fids at construction time |

A generator that builds function networks writes FUNC_TABLE[fid] = new id for each fid it serves (and the F part of that fid's directory entry FF[j] if it changes it), after loading the network (io 7).

## 9. fid table

fid = FN number. Category from the checklist; Block is the hand-written id range the function belongs to (G = a generated family, ids 512 and up). Rows 526 to 532 are TEXT features and share fid 462.

| fid | Name | Category | Block |
|---|---|---|---|
| 1 | ABS | Math and trigonometry | M 264-295 |
| 2 | ACCRINT | Financial | G |
| 3 | ACCRINTM | Financial | G |
| 4 | ACOS | Math and trigonometry | M 264-295 |
| 5 | ACOSH | Math and trigonometry | M 264-295 |
| 6 | ACOT | Math and trigonometry | M 264-295 |
| 7 | ACOTH | Math and trigonometry | M 264-295 |
| 8 | AGGREGATE | Math and trigonometry | M 264-295 |
| 9 | ADDRESS | Lookup and reference | R 360-383 |
| 10 | AMORDEGRC | Financial | G |
| 11 | AMORLINC | Financial | G |
| 12 | AND | Logical | L 296-311 |
| 13 | ARABIC | Math and trigonometry | M 264-295 |
| 14 | AREAS | Lookup and reference | R 360-383 |
| 15 | ARRAYTOTEXT | Text | X 312-343 |
| 16 | ASC | Text | X 312-343 |
| 17 | ASIN | Math and trigonometry | M 264-295 |
| 18 | ASINH | Math and trigonometry | M 264-295 |
| 19 | ATAN | Math and trigonometry | M 264-295 |
| 20 | ATAN2 | Math and trigonometry | M 264-295 |
| 21 | ATANH | Math and trigonometry | M 264-295 |
| 22 | AVEDEV | Statistical | G |
| 23 | AVERAGE | Statistical | G |
| 24 | AVERAGEA | Statistical | G |
| 25 | AVERAGEIF | Statistical | G |
| 26 | AVERAGEIFS | Statistical | G |
| 27 | BAHTTEXT | Text | X 312-343 |
| 28 | BASE | Math and trigonometry | M 264-295 |
| 29 | BESSELI | Engineering | G |
| 30 | BESSELJ | Engineering | G |
| 31 | BESSELK | Engineering | G |
| 32 | BESSELY | Engineering | G |
| 33 | BETADIST | Compatibility | G |
| 34 | BETA.DIST | Statistical | G |
| 35 | BETAINV | Compatibility | G |
| 36 | BETA.INV | Statistical | G |
| 37 | BIN2DEC | Engineering | G |
| 38 | BIN2HEX | Engineering | G |
| 39 | BIN2OCT | Engineering | G |
| 40 | BINOMDIST | Compatibility | G |
| 41 | BINOM.DIST | Statistical | G |
| 42 | BINOM.DIST.RANGE | Statistical | G |
| 43 | BINOM.INV | Statistical | G |
| 44 | BITAND | Engineering | G |
| 45 | BITLSHIFT | Engineering | G |
| 46 | BITOR | Engineering | G |
| 47 | BITRSHIFT | Engineering | G |
| 48 | BITXOR | Engineering | G |
| 49 | BYCOL | Logical | L 296-311 |
| 50 | BYROW | Logical | L 296-311 |
| 51 | CALL | Add-in and Automation | G |
| 52 | CEILING | Compatibility | G |
| 53 | CEILING.MATH | Math and trigonometry | M 264-295 |
| 54 | CEILING.PRECISE | Math and trigonometry | M 264-295 |
| 55 | CELL | Information | L 296-311 |
| 56 | CHAR | Text | X 312-343 |
| 57 | CHIDIST | Compatibility | G |
| 58 | CHIINV | Compatibility | G |
| 59 | CHITEST | Compatibility | G |
| 60 | CHISQ.DIST | Statistical | G |
| 61 | CHISQ.DIST.RT | Statistical | G |
| 62 | CHISQ.INV | Statistical | G |
| 63 | CHISQ.INV.RT | Statistical | G |
| 64 | CHISQ.TEST | Statistical | G |
| 65 | CHOOSE | Lookup and reference | R 360-383 |
| 66 | CHOOSECOLS | Lookup and reference | R 360-383 |
| 67 | CHOOSEROWS | Lookup and reference | R 360-383 |
| 68 | CLEAN | Text | X 312-343 |
| 69 | CODE | Text | X 312-343 |
| 70 | COLUMN | Lookup and reference | R 360-383 |
| 71 | COLUMNS | Lookup and reference | R 360-383 |
| 72 | COMBIN | Math and trigonometry | M 264-295 |
| 73 | COMBINA | Math and trigonometry | M 264-295 |
| 74 | COMPLEX | Engineering | G |
| 75 | CONCAT | Text | X 312-343 |
| 76 | CONCATENATE | Text | X 312-343 |
| 77 | CONFIDENCE | Compatibility | G |
| 78 | CONFIDENCE.NORM | Statistical | G |
| 79 | CONFIDENCE.T | Statistical | G |
| 80 | CONVERT | Engineering | G |
| 81 | CORREL | Statistical | G |
| 82 | COS | Math and trigonometry | M 264-295 |
| 83 | COSH | Math and trigonometry | M 264-295 |
| 84 | COT | Math and trigonometry | M 264-295 |
| 85 | COTH | Math and trigonometry | M 264-295 |
| 86 | COUNT | Statistical | G |
| 87 | COUNTA | Statistical | G |
| 88 | COUNTBLANK | Statistical | G |
| 89 | COUNTIF | Statistical | G |
| 90 | COUNTIFS | Statistical | G |
| 91 | COUPDAYBS | Financial | G |
| 92 | COUPDAYS | Financial | G |
| 93 | COUPDAYSNC | Financial | G |
| 94 | COUPNCD | Financial | G |
| 95 | COUPNUM | Financial | G |
| 96 | COUPPCD | Financial | G |
| 97 | COVAR | Compatibility | G |
| 98 | COVARIANCE.P | Statistical | G |
| 99 | COVARIANCE.S | Statistical | G |
| 100 | CRITBINOM | Compatibility | G |
| 101 | CSC | Math and trigonometry | M 264-295 |
| 102 | CSCH | Math and trigonometry | M 264-295 |
| 103 | CUBEKPIMEMBER | Cube | G |
| 104 | CUBEMEMBER | Cube | G |
| 105 | CUBEMEMBERPROPERTY | Cube | G |
| 106 | CUBERANKEDMEMBER | Cube | G |
| 107 | CUBESET | Cube | G |
| 108 | CUBESETCOUNT | Cube | G |
| 109 | CUBEVALUE | Cube | G |
| 110 | CUMIPMT | Financial | G |
| 111 | CUMPRINC | Financial | G |
| 112 | DATE | Date and time | D 344-359 |
| 113 | DATEDIF | Date and time | D 344-359 |
| 114 | DATEVALUE | Date and time | D 344-359 |
| 115 | DAVERAGE | Database | G |
| 116 | DAY | Date and time | D 344-359 |
| 117 | DAYS | Date and time | D 344-359 |
| 118 | DAYS360 | Date and time | D 344-359 |
| 119 | DB | Financial | G |
| 120 | DBCS | Text | X 312-343 |
| 121 | DCOUNT | Database | G |
| 122 | DCOUNTA | Database | G |
| 123 | DDB | Financial | G |
| 124 | DEC2BIN | Engineering | G |
| 125 | DEC2HEX | Engineering | G |
| 126 | DEC2OCT | Engineering | G |
| 127 | DECIMAL | Math and trigonometry | M 264-295 |
| 128 | DEGREES | Math and trigonometry | M 264-295 |
| 129 | DELTA | Engineering | G |
| 130 | DETECTLANGUAGE | Text | X 312-343 |
| 131 | DEVSQ | Statistical | G |
| 132 | DGET | Database | G |
| 133 | DISC | Financial | G |
| 134 | DMAX | Database | G |
| 135 | DMIN | Database | G |
| 136 | DOLLAR | Text | X 312-343 |
| 137 | DOLLARDE | Financial | G |
| 138 | DOLLARFR | Financial | G |
| 139 | DPRODUCT | Database | G |
| 140 | DROP | Lookup and reference | R 360-383 |
| 141 | DSTDEV | Database | G |
| 142 | DSTDEVP | Database | G |
| 143 | DSUM | Database | G |
| 144 | DURATION | Financial | G |
| 145 | DVAR | Database | G |
| 146 | DVARP | Database | G |
| 147 | EDATE | Date and time | D 344-359 |
| 148 | EFFECT | Financial | G |
| 149 | ENCODEURL | Web | G |
| 150 | EOMONTH | Date and time | D 344-359 |
| 151 | ERF | Engineering | G |
| 152 | ERF.PRECISE | Engineering | G |
| 153 | ERFC | Engineering | G |
| 154 | ERFC.PRECISE | Engineering | G |
| 155 | ERROR.TYPE | Information | L 296-311 |
| 156 | EUROCONVERT | Add-in and Automation | G |
| 157 | EVEN | Math and trigonometry | M 264-295 |
| 158 | EXACT | Text | X 312-343 |
| 159 | EXP | Math and trigonometry | M 264-295 |
| 160 | EXPAND | Lookup and reference | R 360-383 |
| 161 | EXPON.DIST | Statistical | G |
| 162 | EXPONDIST | Compatibility | G |
| 163 | FACT | Math and trigonometry | M 264-295 |
| 164 | FACTDOUBLE | Math and trigonometry | M 264-295 |
| 165 | FALSE | Logical | L 296-311 |
| 166 | F.DIST | Statistical | G |
| 167 | FDIST | Compatibility | G |
| 168 | F.DIST.RT | Statistical | G |
| 169 | FILTER | Lookup and reference | R 360-383 |
| 170 | FILTERXML | Web | G |
| 171 | FIND | Text | X 312-343 |
| 172 | FINDB | Text | X 312-343 |
| 173 | F.INV | Statistical | G |
| 174 | F.INV.RT | Statistical | G |
| 175 | FINV | Compatibility | G |
| 176 | FISHER | Statistical | G |
| 177 | FISHERINV | Statistical | G |
| 178 | FIXED | Text | X 312-343 |
| 179 | FLOOR | Compatibility | G |
| 180 | FLOOR.MATH | Math and trigonometry | M 264-295 |
| 181 | FLOOR.PRECISE | Math and trigonometry | M 264-295 |
| 182 | FORECAST | Statistical | G |
| 183 | FORECAST.ETS | Statistical | G |
| 184 | FORECAST.ETS.CONFINT | Statistical | G |
| 185 | FORECAST.ETS.SEASONALITY | Statistical | G |
| 186 | FORECAST.ETS.STAT | Statistical | G |
| 187 | FORECAST.LINEAR | Statistical | G |
| 188 | FORMULATEXT | Lookup and reference | R 360-383 |
| 189 | FREQUENCY | Statistical | G |
| 190 | F.TEST | Statistical | G |
| 191 | FTEST | Compatibility | G |
| 192 | FV | Financial | G |
| 193 | FVSCHEDULE | Financial | G |
| 194 | GAMMA | Statistical | G |
| 195 | GAMMA.DIST | Statistical | G |
| 196 | GAMMADIST | Compatibility | G |
| 197 | GAMMA.INV | Statistical | G |
| 198 | GAMMAINV | Compatibility | G |
| 199 | GAMMALN | Statistical | G |
| 200 | GAMMALN.PRECISE | Statistical | G |
| 201 | GAUSS | Statistical | G |
| 202 | GCD | Math and trigonometry | M 264-295 |
| 203 | GEOMEAN | Statistical | G |
| 204 | GESTEP | Engineering | G |
| 205 | GETPIVOTDATA | Lookup and reference | R 360-383 |
| 206 | GROUPBY | Lookup and reference | R 360-383 |
| 207 | GROWTH | Statistical | G |
| 208 | HARMEAN | Statistical | G |
| 209 | HEX2BIN | Engineering | G |
| 210 | HEX2DEC | Engineering | G |
| 211 | HEX2OCT | Engineering | G |
| 212 | HLOOKUP | Lookup and reference | R 360-383 |
| 213 | HOUR | Date and time | D 344-359 |
| 214 | HSTACK | Lookup and reference | R 360-383 |
| 215 | HYPERLINK | Lookup and reference | R 360-383 |
| 216 | HYPGEOM.DIST | Statistical | G |
| 217 | HYPGEOMDIST | Compatibility | G |
| 218 | IF | Logical | L 296-311 |
| 219 | IFERROR | Logical | L 296-311 |
| 220 | IFNA | Logical | L 296-311 |
| 221 | IFS | Logical | L 296-311 |
| 222 | IMABS | Engineering | G |
| 223 | IMAGE | Lookup and reference | R 360-383 |
| 224 | IMAGINARY | Engineering | G |
| 225 | IMARGUMENT | Engineering | G |
| 226 | IMCONJUGATE | Engineering | G |
| 227 | IMCOS | Engineering | G |
| 228 | IMCOSH | Engineering | G |
| 229 | IMCOT | Engineering | G |
| 230 | IMCSC | Engineering | G |
| 231 | IMCSCH | Engineering | G |
| 232 | IMDIV | Engineering | G |
| 233 | IMEXP | Engineering | G |
| 234 | IMLN | Engineering | G |
| 235 | IMLOG10 | Engineering | G |
| 236 | IMLOG2 | Engineering | G |
| 237 | IMPOWER | Engineering | G |
| 238 | IMPRODUCT | Engineering | G |
| 239 | IMREAL | Engineering | G |
| 240 | IMSEC | Engineering | G |
| 241 | IMSECH | Engineering | G |
| 242 | IMSIN | Engineering | G |
| 243 | IMSINH | Engineering | G |
| 244 | IMSQRT | Engineering | G |
| 245 | IMSUB | Engineering | G |
| 246 | IMSUM | Engineering | G |
| 247 | IMTAN | Engineering | G |
| 248 | INDEX | Lookup and reference | R 360-383 |
| 249 | INDIRECT | Lookup and reference | R 360-383 |
| 250 | INFO | Information | L 296-311 |
| 251 | INT | Math and trigonometry | M 264-295 |
| 252 | INTERCEPT | Statistical | G |
| 253 | INTRATE | Financial | G |
| 254 | IPMT | Financial | G |
| 255 | IRR | Financial | G |
| 256 | ISBLANK | Information | L 296-311 |
| 257 | ISERR | Information | L 296-311 |
| 258 | ISERROR | Information | L 296-311 |
| 259 | ISEVEN | Information | L 296-311 |
| 260 | ISFORMULA | Information | L 296-311 |
| 261 | ISLOGICAL | Information | L 296-311 |
| 262 | ISNA | Information | L 296-311 |
| 263 | ISNONTEXT | Information | L 296-311 |
| 264 | ISNUMBER | Information | L 296-311 |
| 265 | ISODD | Information | L 296-311 |
| 266 | ISOMITTED | Information | L 296-311 |
| 267 | ISREF | Information | L 296-311 |
| 268 | ISTEXT | Information | L 296-311 |
| 269 | ISO.CEILING | Math and trigonometry | M 264-295 |
| 270 | ISOWEEKNUM | Date and time | D 344-359 |
| 271 | ISPMT | Financial | G |
| 272 | JIS | Text | X 312-343 |
| 273 | KURT | Statistical | G |
| 274 | LAMBDA | Logical | L 296-311 |
| 275 | LARGE | Statistical | G |
| 276 | LCM | Math and trigonometry | M 264-295 |
| 277 | LEFT | Text | X 312-343 |
| 278 | LEFTB | Text | X 312-343 |
| 279 | LEN | Text | X 312-343 |
| 280 | LENB | Text | X 312-343 |
| 281 | LET | Logical | L 296-311 |
| 282 | LINEST | Statistical | G |
| 283 | LN | Math and trigonometry | M 264-295 |
| 284 | LOG | Math and trigonometry | M 264-295 |
| 285 | LOG10 | Math and trigonometry | M 264-295 |
| 286 | LOGEST | Statistical | G |
| 287 | LOGINV | Compatibility | G |
| 288 | LOGNORM.DIST | Statistical | G |
| 289 | LOGNORMDIST | Compatibility | G |
| 290 | LOGNORM.INV | Statistical | G |
| 291 | LOOKUP | Lookup and reference | R 360-383 |
| 292 | LOWER | Text | X 312-343 |
| 293 | MAKEARRAY | Logical | L 296-311 |
| 294 | MAP | Logical | L 296-311 |
| 295 | MATCH | Lookup and reference | R 360-383 |
| 296 | MAX | Statistical | G |
| 297 | MAXA | Statistical | G |
| 298 | MAXIFS | Statistical | G |
| 299 | MDETERM | Math and trigonometry | M 264-295 |
| 300 | MDURATION | Financial | G |
| 301 | MEDIAN | Statistical | G |
| 302 | MID | Text | X 312-343 |
| 303 | MIDB | Text | X 312-343 |
| 304 | MIN | Statistical | G |
| 305 | MINIFS | Statistical | G |
| 306 | MINA | Statistical | G |
| 307 | MINUTE | Date and time | D 344-359 |
| 308 | MINVERSE | Math and trigonometry | M 264-295 |
| 309 | MIRR | Financial | G |
| 310 | MMULT | Math and trigonometry | M 264-295 |
| 311 | MOD | Math and trigonometry | M 264-295 |
| 312 | MODE | Compatibility | G |
| 313 | MODE.MULT | Statistical | G |
| 314 | MODE.SNGL | Statistical | G |
| 315 | MONTH | Date and time | D 344-359 |
| 316 | MROUND | Math and trigonometry | M 264-295 |
| 317 | MULTINOMIAL | Math and trigonometry | M 264-295 |
| 318 | MUNIT | Math and trigonometry | M 264-295 |
| 319 | N | Information | L 296-311 |
| 320 | NA | Information | L 296-311 |
| 321 | NEGBINOM.DIST | Statistical | G |
| 322 | NEGBINOMDIST | Compatibility | G |
| 323 | NETWORKDAYS | Date and time | D 344-359 |
| 324 | NETWORKDAYS.INTL | Date and time | D 344-359 |
| 325 | NOMINAL | Financial | G |
| 326 | NORM.DIST | Statistical | G |
| 327 | NORMDIST | Compatibility | G |
| 328 | NORMINV | Compatibility | G |
| 329 | NORM.INV | Statistical | G |
| 330 | NORM.S.DIST | Statistical | G |
| 331 | NORMSDIST | Compatibility | G |
| 332 | NORM.S.INV | Statistical | G |
| 333 | NORMSINV | Compatibility | G |
| 334 | NOT | Logical | L 296-311 |
| 335 | NOW | Date and time | D 344-359 |
| 336 | NPER | Financial | G |
| 337 | NPV | Financial | G |
| 338 | NUMBERVALUE | Text | X 312-343 |
| 339 | OCT2BIN | Engineering | G |
| 340 | OCT2DEC | Engineering | G |
| 341 | OCT2HEX | Engineering | G |
| 342 | ODD | Math and trigonometry | M 264-295 |
| 343 | ODDFPRICE | Financial | G |
| 344 | ODDFYIELD | Financial | G |
| 345 | ODDLPRICE | Financial | G |
| 346 | ODDLYIELD | Financial | G |
| 347 | OFFSET | Lookup and reference | R 360-383 |
| 348 | OR | Logical | L 296-311 |
| 349 | PDURATION | Financial | G |
| 350 | PEARSON | Statistical | G |
| 351 | PERCENTILE.EXC | Statistical | G |
| 352 | PERCENTILE.INC | Statistical | G |
| 353 | PERCENTILE | Compatibility | G |
| 354 | PERCENTOF | Math and trigonometry | M 264-295 |
| 355 | PERCENTRANK.EXC | Statistical | G |
| 356 | PERCENTRANK.INC | Statistical | G |
| 357 | PERCENTRANK | Compatibility | G |
| 358 | PERMUT | Statistical | G |
| 359 | PERMUTATIONA | Statistical | G |
| 360 | PHI | Statistical | G |
| 361 | PHONETIC | Text | X 312-343 |
| 362 | PI | Math and trigonometry | M 264-295 |
| 363 | PIVOTBY | Lookup and reference | R 360-383 |
| 364 | PMT | Financial | G |
| 365 | POISSON.DIST | Statistical | G |
| 366 | POISSON | Compatibility | G |
| 367 | POWER | Math and trigonometry | M 264-295 |
| 368 | PPMT | Financial | G |
| 369 | PRICE | Financial | G |
| 370 | PRICEDISC | Financial | G |
| 371 | PRICEMAT | Financial | G |
| 372 | PROB | Statistical | G |
| 373 | PRODUCT | Math and trigonometry | M 264-295 |
| 374 | PROPER | Text | X 312-343 |
| 375 | PV | Financial | G |
| 376 | QUARTILE | Compatibility | G |
| 377 | QUARTILE.EXC | Statistical | G |
| 378 | QUARTILE.INC | Statistical | G |
| 379 | QUOTIENT | Math and trigonometry | M 264-295 |
| 380 | RADIANS | Math and trigonometry | M 264-295 |
| 381 | RAND | Math and trigonometry | M 264-295 |
| 382 | RANDARRAY | Math and trigonometry | M 264-295 |
| 383 | RANDBETWEEN | Math and trigonometry | M 264-295 |
| 384 | RANK.AVG | Statistical | G |
| 385 | RANK.EQ | Statistical | G |
| 386 | RANK | Compatibility | G |
| 387 | RATE | Financial | G |
| 388 | RECEIVED | Financial | G |
| 389 | REDUCE | Logical | L 296-311 |
| 390 | REGEXEXTRACT | Text | X 312-343 |
| 391 | REGEXREPLACE | Text | X 312-343 |
| 392 | REGEXTEST | Text | X 312-343 |
| 393 | REGISTER.ID | Add-in and Automation | G |
| 394 | REPLACE | Text | X 312-343 |
| 395 | REPLACEB | Text | X 312-343 |
| 396 | REPT | Text | X 312-343 |
| 397 | RIGHT | Text | X 312-343 |
| 398 | RIGHTB | Text | X 312-343 |
| 399 | ROMAN | Math and trigonometry | M 264-295 |
| 400 | ROUND | Math and trigonometry | M 264-295 |
| 401 | ROUNDDOWN | Math and trigonometry | M 264-295 |
| 402 | ROUNDUP | Math and trigonometry | M 264-295 |
| 403 | ROW | Lookup and reference | R 360-383 |
| 404 | ROWS | Lookup and reference | R 360-383 |
| 405 | RRI | Financial | G |
| 406 | RSQ | Statistical | G |
| 407 | RTD | Lookup and reference | R 360-383 |
| 408 | SCAN | Logical | L 296-311 |
| 409 | SEARCH | Text | X 312-343 |
| 410 | SEARCHB | Text | X 312-343 |
| 411 | SEC | Math and trigonometry | M 264-295 |
| 412 | SECH | Math and trigonometry | M 264-295 |
| 413 | SECOND | Date and time | D 344-359 |
| 414 | SEQUENCE | Math and trigonometry | M 264-295 |
| 415 | SERIESSUM | Math and trigonometry | M 264-295 |
| 416 | SHEET | Information | L 296-311 |
| 417 | SHEETS | Information | L 296-311 |
| 418 | SIGN | Math and trigonometry | M 264-295 |
| 419 | SIN | Math and trigonometry | M 264-295 |
| 420 | SINH | Math and trigonometry | M 264-295 |
| 421 | SKEW | Statistical | G |
| 422 | SKEW.P | Statistical | G |
| 423 | SLN | Financial | G |
| 424 | SLOPE | Statistical | G |
| 425 | SMALL | Statistical | G |
| 426 | SORT | Lookup and reference | R 360-383 |
| 427 | SORTBY | Lookup and reference | R 360-383 |
| 428 | SQRT | Math and trigonometry | M 264-295 |
| 429 | SQRTPI | Math and trigonometry | M 264-295 |
| 430 | STANDARDIZE | Statistical | G |
| 431 | STDEV | Compatibility | G |
| 432 | STDEV.P | Statistical | G |
| 433 | STDEV.S | Statistical | G |
| 434 | STDEVA | Statistical | G |
| 435 | STDEVP | Compatibility | G |
| 436 | STDEVPA | Statistical | G |
| 437 | STEYX | Statistical | G |
| 438 | STOCKHISTORY | Information | L 296-311 |
| 439 | SUBSTITUTE | Text | X 312-343 |
| 440 | SUBTOTAL | Math and trigonometry | M 264-295 |
| 441 | SUM | Math and trigonometry | M 264-295 |
| 442 | SUMIF | Math and trigonometry | M 264-295 |
| 443 | SUMIFS | Math and trigonometry | M 264-295 |
| 444 | SUMPRODUCT | Math and trigonometry | M 264-295 |
| 445 | SUMSQ | Math and trigonometry | M 264-295 |
| 446 | SUMX2MY2 | Math and trigonometry | M 264-295 |
| 447 | SUMX2PY2 | Math and trigonometry | M 264-295 |
| 448 | SUMXMY2 | Math and trigonometry | M 264-295 |
| 449 | SWITCH | Logical | L 296-311 |
| 450 | SYD | Financial | G |
| 451 | T | Text | X 312-343 |
| 452 | TAN | Math and trigonometry | M 264-295 |
| 453 | TANH | Math and trigonometry | M 264-295 |
| 454 | TAKE | Lookup and reference | R 360-383 |
| 455 | TBILLEQ | Financial | G |
| 456 | TBILLPRICE | Financial | G |
| 457 | TBILLYIELD | Financial | G |
| 458 | T.DIST | Statistical | G |
| 459 | T.DIST.2T | Statistical | G |
| 460 | T.DIST.RT | Statistical | G |
| 461 | TDIST | Compatibility | G |
| 462 | TEXT | Text | X 312-343 |
| 463 | TEXTAFTER | Text | X 312-343 |
| 464 | TEXTBEFORE | Text | X 312-343 |
| 465 | TEXTJOIN | Text | X 312-343 |
| 466 | TEXTSPLIT | Text | X 312-343 |
| 467 | TIME | Date and time | D 344-359 |
| 468 | TIMEVALUE | Date and time | D 344-359 |
| 469 | T.INV | Statistical | G |
| 470 | T.INV.2T | Statistical | G |
| 471 | TINV | Compatibility | G |
| 472 | TOCOL | Lookup and reference | R 360-383 |
| 473 | TOROW | Lookup and reference | R 360-383 |
| 474 | TODAY | Date and time | D 344-359 |
| 475 | TRANSLATE | Text | X 312-343 |
| 476 | TRANSPOSE | Lookup and reference | R 360-383 |
| 477 | TREND | Statistical | G |
| 478 | TRIM | Text | X 312-343 |
| 479 | TRIMMEAN | Statistical | G |
| 480 | TRIMRANGE | Lookup and reference | R 360-383 |
| 481 | TRUE | Logical | L 296-311 |
| 482 | TRUNC | Math and trigonometry | M 264-295 |
| 483 | T.TEST | Statistical | G |
| 484 | TTEST | Compatibility | G |
| 485 | TYPE | Information | L 296-311 |
| 486 | UNICHAR | Text | X 312-343 |
| 487 | UNICODE | Text | X 312-343 |
| 488 | UNIQUE | Lookup and reference | R 360-383 |
| 489 | UPPER | Text | X 312-343 |
| 490 | VALUE | Text | X 312-343 |
| 491 | VALUETOTEXT | Text | X 312-343 |
| 492 | VAR | Compatibility | G |
| 493 | VAR.P | Statistical | G |
| 494 | VAR.S | Statistical | G |
| 495 | VARA | Statistical | G |
| 496 | VARP | Compatibility | G |
| 497 | VARPA | Statistical | G |
| 498 | VDB | Financial | G |
| 499 | VLOOKUP | Lookup and reference | R 360-383 |
| 500 | VSTACK | Lookup and reference | R 360-383 |
| 501 | WEBSERVICE | Web | G |
| 502 | WEEKDAY | Date and time | D 344-359 |
| 503 | WEEKNUM | Date and time | D 344-359 |
| 504 | WEIBULL | Compatibility | G |
| 505 | WEIBULL.DIST | Statistical | G |
| 506 | WORKDAY | Date and time | D 344-359 |
| 507 | WORKDAY.INTL | Date and time | D 344-359 |
| 508 | WRAPCOLS | Lookup and reference | R 360-383 |
| 509 | WRAPROWS | Lookup and reference | R 360-383 |
| 510 | XIRR | Financial | G |
| 511 | XLOOKUP | Lookup and reference | R 360-383 |
| 512 | XMATCH | Lookup and reference | R 360-383 |
| 513 | XNPV | Financial | G |
| 514 | XOR | Logical | L 296-311 |
| 515 | YEAR | Date and time | D 344-359 |
| 516 | YEARFRAC | Date and time | D 344-359 |
| 517 | YIELD | Financial | G |
| 518 | YIELDDISC | Financial | G |
| 519 | YIELDMAT | Financial | G |
| 520 | Z.TEST | Statistical | G |
| 521 | ZTEST | Compatibility | G |
| 522 | COPILOT | Unconfirmed | G |
| 523 | PY | Unconfirmed | G |
| 524 | IMPORTCSV | Unconfirmed | G |
| 525 | IMPORTTEXT | Unconfirmed | G |
| (462) | TEXT format codes: digit placeholders 0 # ? and decimal point | Text | TEXT feature |
| (462) | TEXT format codes: thousands separator and scaling by trailing commas | Text | TEXT feature |
| (462) | TEXT format codes: percent and scientific E+ E- | Text | TEXT feature |
| (462) | TEXT format codes: date and time tokens d m y h s AM/PM and elapsed [h] [m] [s] | Text | TEXT feature |
| (462) | TEXT format codes: literal text quoting backslash escape and @ | Text | TEXT feature |
| (462) | TEXT format codes: sections and conditions | Text | TEXT feature |
| (462) | TEXT format codes: fractions | Text | TEXT feature |
