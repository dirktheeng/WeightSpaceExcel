# Weight block notes: Debug.Print and MsgBox (ids 430, 436, 437, 438, 441, 442)

Hand-written. Not generated. Buffers: encodings/vba.md section 2. Log: log/vba-agent.md; decision VB7.

| Id | File | Computes |
|---|---|---|
| 430 | vo_main | class of the value; DST = DOUT or MOUT (MUX_INT); string: read its length -> vo_slen -> copy loop; number: writes the sign space (kept only for PRINT of x >= 0), calls ev_totext (eval agent, id 110) with A = (1, x), return to vo_num; Boolean: writes True / False (5-word payload, letters linear in [isBool, isFalse]); Empty: nothing |
| 436 | vo_num | after ev_totext: UXIT = 438, read the packed length |
| 437 | vu_wr | PC 0: CNT = length, read first packed word; PC 1: c2 = FLOOR(x 2^-32), c1 = FLOOR(r 2^-16), c0 = r - 2^16 c1 (exact powers of two), block write 3 units |
| 442 | vu_rd | read next packed word or exit to UXIT |
| 438 | vo_tail | PC 0 writes [' ' if TRAIL, LF if NL]; PC 1 pushes Integer 1 for MsgBox (vbOK), stores DST back into DOUT or MOUT, IP += 2 |
| 441 | vo_slen | CNT = length, then the copy loop |

**Format.** Print of a number: " 5 ", "-3 " (sign space, trailing space; VBA's Print rule); Boolean True/False; strings as is; ';' (ARG 1) suppresses the line end. MsgBox writes CStr(value) and LF. Number text is the evaluator's General format (15 significant digits, E+xx above 1e15); VBA switches to E notation for small numbers earlier than Excel (limit). Lines end with LF only.
**Limits.** Print zones (',') and Spc/Tab are not done. **Multi-role weights.** UXIT (62) selects the unpack exit: 438 here, 445 for CStr. **Tests.** test_print_formats, test_strings_concat_msgbox.
