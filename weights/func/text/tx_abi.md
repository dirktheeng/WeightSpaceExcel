# Text ABI layer (ids 319 to 323, 335 to 338): tx_w0, tx_av, tx_ld, tx_fin, tx_rgt, tx_val, tx_tx, tx_tx2, tx_tx3

Hand-written, not generated. Log: log/func-text-agent.md session 2; WORKLOG "2026-11-06, Stage 3: Text functions, ABI layer" (decisions T5 to T8). ABI: encodings/functions.md sections 2 to 7. FUNC_TABLE: every Text fid below maps to 319.

## Flow

FN_CALL -> **tx_w0** PC 0 (class ROM, count check, B stored over argument n) -> for each argument: tx_w0 PC 1 block read -> **tx_av** (classify by kind; convert in place, or call CELL_GET 16 / ev_totext 110 / ev_t2n 109, which return to tx_w0 PC 3 / 2 / 4) -> after the last argument tx_w0 block reads arguments 1..4 -> **tx_ld** (first error in argument order, register set-up per class) -> core or driver -> **tx_fin** (P1 from T9, N0 from T10) -> FN_RET 257.

| fid | Name | class | entered at | kinds (arg 1..4) | counts |
|---|---|---|---|---|---|
| 279, 280 | LEN, LENB | 0 | 312 | T | 1 |
| 69 | CODE | 1 | 313 N0 0 | T | 1 |
| 487 | UNICODE | 2 | 313 N0 1 | T | 1 |
| 489 | UPPER | 3 | 314 N0 0 | T | 1 |
| 292 | LOWER | 4 | 314 N0 1 | T | 1 |
| 158 | EXACT | 5 | 315 | T T | 2 |
| 302, 303 | MID, MIDB | 6 | 316 | T N N | 3 |
| 277, 278 | LEFT, LEFTB | 7 | 316 (B = 1) | T N | 1..2 |
| 397, 398 | RIGHT, RIGHTB | 8 | 323 then 316 | T N | 1..2 |
| 56 | CHAR | 9 | 317 N0 0 | N | 1 |
| 486 | UNICHAR | 10 | 317 N0 1 | N | 1 |
| 451 | T | 11 | 318 | R | 1 |
| 68 | CLEAN | 12 | 326 N0 1 | T | 1 |
| 478 | TRIM | 13 | 326 N0 2 | T | 1 |
| 374 | PROPER | 14 | 326 N0 3 | T | 1 |
| 75, 76 | CONCAT, CONCATENATE | 15 | 327 N0 0 | T ... | 1..255 |
| 465 | TEXTJOIN | 16 | 327 N0 1 | T N T ... | 3..255 |
| 396 | REPT | 17 | 328 | T N | 2 |
| 394, 395 | REPLACE, REPLACEB | 18 | 329 | T N N T | 4 |
| 171, 172 | FIND, FINDB | 19 | 332 N0 0 | T T N | 2..3 |
| 409, 410 | SEARCH, SEARCHB | 20 | 332 N0 1 | T T N | 2..3 |
| 490 | VALUE | 21 | 335 | R | 1 |
| 462 | TEXT | 22 | 336 | R T | 2 |
| 439 | SUBSTITUTE | 23 | 334 | T T T N | 3..4 |

Kinds: T text (numbers and booleans through ev_totext, blank and missing to ""), N number (text through ev_t2n, booleans to 1 / 0, blank and missing to 0; a t2n result that is not a number becomes #VALUE!), R raw (references read, nothing else converted). Ranges, arrays, unions and lambdas give #VALUE! for every kind (no implicit intersection yet; open item). The B variants equal the plain functions (Excel documents this for non-DBCS default languages).

## tx_w0 (319)
ROM over T2 = 64 + fid: a 42-step thermometer at the class boundaries; class, kind map KM (base-4 digits per argument position), minimum and maximum counts are each one dense row of telescoped differences (the row for value v at threshold h is v(above h) - v(below h)), so the ROM costs one step layer and four rows. Count check: lo = [n < min], hi = [n > max]. Registers kept for the whole call: T7 KM, T8 class, T9 = P1, T10 = n (the cores and drivers clobber P1 and N0, both in the preserve set). Phases 0..4 as in the file header; every output is a block op (66 words, decision T4). Values that can be large or any double (B, A, N1, T7..T10, the class) are selected with mul gates; addresses with MUX_INT relus (M = 2^23).

## tx_av (320)
Block consumer of one argument. Kind = base-4 digit N1 - 1 of KM: three FLOOR(x / 4) stages (exact scaling by 0.25), then one relu per position, relu(d_k - 4 (1 - e_k)), with e_k the position one-hot. The cell reference K is unpacked with FLOOR(K 2^-34) and FLOOR(rem 2^-14) for CELL_GET. All exits are block writes (N = 2 to store the converted value, N = 0 when a converter is called).

## tx_ld (321)
Block consumer of 8 words (arguments 1..4). Errors: e1 = [tag 4], e_k = [tag 4][n >= k]; the first one is selected by sel_k = e_k and none before (step rows with -1 on earlier errors). Core id, mode N0 and register routing are telescoped rows over the 23-step class thermometer. Optional arguments: LEFT and RIGHT count default 1, FIND / SEARCH start default 1, SUBSTITUTE instance (0, 0) when omitted.

## tx_fin (322)
Pure copy plus P1 = T9, N0 = T10, next 257.

## tx_rgt (323)
RIGHT start = 1 + max(0, L - TRUNC(count)) after one read of the length, then the MID core with C = count.

## tx_val (335)
VALUE: number or error returned; blank 0; text through ev_t2n (LP 1) and a non-number result becomes #VALUE!; boolean, array: #VALUE!. Limits: whatever the parser's number lexer accepts is accepted (VALUE("$1,000"), dates and times in text, "1:30 PM" are not handled unless the lexer does).

## tx_tx, tx_tx2, tx_tx3 (336 to 338): TEXT
Uses the format engine (weights/format/README.md, fx_main 198). tx_tx: PC 0 HEAP_TOP = HT (fx_pack allocates at HEAP_TOP), PC 1 FMT_TABLE entry 511 = [code handle, 0] (0 = not compiled, so each call compiles the code; COMPILE_TOP grows by one record per call), PC 2 spill words 8..39 at RSP (fx_main clobbers 19..39, including GEN 22, CYC 24, T9, T10), call fx_main with B = (511, 0), PC 3 block read HEAP_TOP. tx_tx2 sets HT and block reads the spill. tx_tx3 restores words 8..39 except A and HT. A blank value is formatted as 0. Limits are the engine's (no dates, fractions or '@' yet; a text value with no text section and booleans come back unchanged).
**Needs:** FMT_TABLE entry 511 reserved for TEXT (format agent / coordinator).

## Limits common to the layer
- No implicit intersection: a multi-cell range argument gives #VALUE!.
- Result length is not checked against 32767 except in REPT.
- Parameters (dense weights and biases, zeros included, counted from the layer headers): tx_w0 3116, tx_av 934, tx_ld 2895, tx_fin 24, tx_rgt 59, tx_val 269, tx_tx 403, tx_tx2 27, tx_tx3 16.
