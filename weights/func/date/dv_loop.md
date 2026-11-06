# dv_loop (id 355): character loop of the date/time text parser

Hand-written (log/func-date-agent.md session 2; decision FD-7). One character per step.

| PC | Does | Next |
|---|---|---|
| 1 | read mem[a] (string length; a = handle) | 355 PC 2 |
| 2 | rem = L (0 and perr = 1 when L > 40), a = a + 2, read mem[a] | 355 PC 3 |
| 3 | x0 = packed word of character i: c = code unit j = i mod 3 (two exact FLOORs by 2^16, 2^32), or a space when rem = 0; token update; a += [j = 2], j = (j + 1) mod 3, rem -= 1; read mem[a] | 355 PC 3, or 356 PC 0 after the virtual space |

PC values other than 1..3 behave as the nearest of them (not trapped).

**State words.** 15 mode, 16 a, 17 j, 18 rem, 19 acc (current number), 20 innum, 21 lk (letter key), 22 lc (letters seen, max 3), 23..25 d1..d3 (date numbers), 26 nf, 27..29 t1..t3 (time numbers), 30 nt, 31 mn (month 1..12), 32 mpos (nf when the month name ended), 33 ampm (1 AM, 2 PM), 34 perr, 35 tmode (a ':' was seen), 36 ecode0.

**Token machine (layers v21..v89).** Classes from 13 thresholds on c: digit, ':', letter (upper or lower), lower, other (anything that is not a digit, letter, ':', space, ',', '-' or '/'; '.' is other). A digit sets acc = 10 acc + digit. A non-digit after a digit ends the number: to t[nt + 1] when the character is ':' or tmode is set, else to d[nf + 1]; a fourth date or time number sets perr. Letters build lk = 32 lk + code for the first three (A = 1, case folded); a non-letter ends the word, which must be a month (keys 1024 c1 + 32 c2 + c3: JAN 10286 FEB 6306 MAR 13362 APR 1554 MAY 13369 JUN 10926 JUL 10924 AUG 1703 SEP 19632 OCT 15476 NOV 14838 DEC 4259, by IS_K pairs) or A, AM, P, PM (1, 45, 16, 525); key ranges by letter count are disjoint (one letter <= 26, two <= 858, three >= 1057). A second month or a second AM/PM, an unknown word, or an 'other' character sets perr. All updates are written as gated products (one mul layer of 12 pairs), and the new state is gated by [PC = 3] so the PC 1 and 2 steps leave it at zero.

**Limits.** At most 40 characters (Excel allows 255). Separators are not checked for order or repetition ("1//2/2000" is accepted); only the first three letters of a word are checked ("Janxyz" is January). No fractional seconds, no '.' separators, no day names.

**Parameters.** 2010 dense parameters, 108 layers. **Tests.** test_dv.py.
