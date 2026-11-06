# weights/func/logic: Logical and Information functions (ids 296 to 311)

Hand-written. Not generated. Log: log/func-logic-agent.md; decisions LG1 to LG4 in log/WORKLOG.md ("2026-11-06 Stage 3: logical and information functions"). ABI: encodings/functions.md.

| Id | File | Role | Params | Steps |
|---|---|---|---|---|
| 296 | lg_info | leaf: 18 unary functions on A by selector T0 | 1302 | 1 |
| 297 | lg_fold | leaf: AND / OR / XOR accumulator (C, T3, T4) by selector T0 | 1533 | 1 |
| 299 | lg_un | ABI entry: ISBLANK ... ISTEXT, ISREF, ISFORMULA, N, NA, TYPE, ERROR.TYPE, NOT, TRUE, FALSE | 1158 | 1 to 3 (+ CELL_GET) |
| 300 | lg_arg | ABI entry and argument streamer for AND, OR, XOR, IF, IFS, SWITCH, IFERROR, IFNA (66-word output, block ops only) | 350 | 1 per fetch |
| 301 | lg_cfold | block consumer (67 inputs) for AND / OR / XOR | 294 | 1 per argument |
| 302 | lg_csel | block consumer (67 inputs) for IF, IFERROR, IFNA, IFS, SWITCH | 3199 | 1 per argument looked at |
| 303 | lg_sheet | ABI entry: SHEET, SHEETS | 424 | 1 or 2 |

Total 8260 dense weights and biases (zeros included). Ids 298 and 304 to 311 are free.

## FUNC_TABLE entries needed (owned by the ABI agent's FT_INIT)

FUNC_TABLE[fid] = 299 for fids 155 ERROR.TYPE, 165 FALSE, 256 ISBLANK, 257 ISERR, 258 ISERROR, 259 ISEVEN, 260 ISFORMULA, 261 ISLOGICAL, 262 ISNA, 263 ISNONTEXT, 264 ISNUMBER, 265 ISODD, 267 ISREF, 268 ISTEXT, 319 N, 320 NA, 334 NOT, 481 TRUE, 485 TYPE.
FUNC_TABLE[fid] = 300 for fids 12 AND, 218 IF, 219 IFERROR, 220 IFNA, 221 IFS, 348 OR, 449 SWITCH, 514 XOR.
FUNC_TABLE[fid] = 303 for fids 416 SHEET, 417 SHEETS.
Flags F (MIN + 256 MAX + 65536 BITS): IS functions, N, TYPE, ERROR.TYPE: 1 + 256 + 65536 * 4 (ISREF, ISFORMULA add bit 8); NOT 1 + 256; NA, TRUE, FALSE 0 + 0; AND, OR, XOR 1 + 256 * 255; IF 2 + 256 * 3; IFERROR, IFNA 2 + 512 + 65536 * 4; IFS 2 + 256 * 254; SWITCH 3 + 256 * 254; SHEET 0 + 256 (+ bit 8, volatile no); SHEETS 0 + 256.

## Calling pattern

- Unary: FN_CALL -> lg_un PC 0 -> (CELL_GET -> lg_un PC 1 [-> PC 2]) -> lg_info with LR = 257, LP = 0, so lg_info returns straight into FN_RET.
- Many-argument: lg_arg PC 0 writes B to [SP, SP + 1] so every argument i is at SP - 2 (n - i); then per argument: lg_arg PC 1 block read -> consumer (301 or 302). The consumer either fetches the next argument (lg_cfold via lg_fold with LR = 300, LP = 1), dereferences (CELL_GET with LR = 300, LP = 2; lg_arg PC 2 writes the value over the slot and refetches), or returns to FN_RET.
- Registers used beyond the ABI entry set: N1 (argument index), C, T3, T4, T5 (state), T0, T1 (leaf selectors and CELL_GET), A, B, address register. All are in the ABI's free set. The write at [SP, SP + 1] is above the stack top and is dropped by FN_RET (functions.md section 6).
