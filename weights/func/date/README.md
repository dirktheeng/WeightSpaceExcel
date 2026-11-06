# weights/func/date: Excel date and time functions (ids 344 to 359)

Hand-written. Not generated. Log: log/func-date-agent.md; decisions FD-1 to FD-5 in log/WORKLOG.md ("2026-11-06, Stage 4: date and time functions"). Tests: tests/output/func_date (black box, expected serials stated by hand).

| Id | File | Functions | Steps |
|---|---|---|---|
| 344 | dt_ymd | YEAR MONTH DAY HOUR MINUTE SECOND WEEKDAY (core used by all others) | 1 |
| 345 | dt_date | DATE; EDATE and EOMONTH (entry PC 3 and 4, finish PC 1 and 2) | 1; 3 for EDATE/EOMONTH |
| 346 | dt_time | TIME | 1 |
| 347 | dt_pair | two-date driver for DAYS DAYS360 DATEDIF YEARFRAC | 3 + finisher = 6 in all |
| 348 | dt_fin2 | DAYS DAYS360 DATEDIF finish | 1 |
| 349 | dt_now | NOW TODAY | 3 |
| 350 | dt_wk | WEEKNUM ISOWEEKNUM | 3 (entry, dt_ymd, finish) |
| 353 | dt_yf | YEARFRAC finish | 1 |
| 351, 352 | dt_abi, dt_abi1 | ABI entry for all the fids above and DATEVALUE, TIMEVALUE (encodings/functions.md) | 3 + 2 per reference |
| 354 to 357 | dv_ent, dv_loop, dv_fin, dv_rest | date/time text parser: DATEVALUE, TIMEVALUE, text coercion (leaf, keeps every word but A) | L + 10 for L characters |
| 358 | dt_coer | coerces text date arguments through the parser, then jumps to the core | 1 + parser per text argument |
| 359 | | free (planned: NETWORKDAYS, WORKDAY and .INTL; design in the log, needs one more id) | |

## Calling convention

The evaluator enters every date fid at dt_abi (351, see dt_abi.md), which gathers and dereferences the arguments and calls a core. The cores are leaf subroutines in the control.md section 4 style: arguments in A, B, C (TAG, PAY); selector in T0 (dt_ymd, dt_now) or N1 (dt_pair, dt_wk) or PC (dt_date); result in A with STATUS 0; return next = LR, PC = LP. Multi-network functions (EDATE, EOMONTH, WEEKNUM, the dt_pair family) save the caller's link in T9, T10 at their entry phase and return there. Clobber sets are in each note.

Argument coercion common to all: number (tag 1) and boolean (tag 3) use PAY; blank (0) and missing (8) are 0 (or the documented default); an error (4) propagates, left to right; text (2) is coerced by dt_coer through the parser in coercion mode (a date, a time, a date with time, or a plain integer; otherwise #VALUE!), except DATEDIF's unit and the DATEVALUE/TIMEVALUE argument; every other tag gives #VALUE!.

## Serial number rules (Excel 1900 system)
- Valid serials are 0 <= s < 2958466 (9999-12-31 is 2958465); outside that, #NUM!.
- Serial 0 decodes as 1900-01-00 (YEAR 1900, MONTH 1, DAY 0); serial 60 is the fictitious 1900-02-29; serials 1 to 59 are one day earlier than the proleptic Gregorian count from 1899-12-30, serials from 61 on agree with it.
- Weekday is (serial mod 7) based, so 1900-01-01 counts as a Sunday, as in Excel.

## Shared technique (decision FD-1): floor division by a constant
For an integer x and constant d, floor(x / d) = ROUND(c x + b) with c close to 1/d and b close to -0.5 + 0.5/d. Since x/d has fractional part in [0, (d-1)/d], c x + b stays at least 0.5/d away from every half integer, so ROUND (C = 1.5 * 2^52 trick, encodings/primitives.md) is exact as long as |c - 1/d| |x| + |b - b_true| is far below 0.5/d. Every constant is worked out by hand to 12 or more digits; for |x| < 4e6 about 8 digits would already be enough. Cost: one dense row for c x + b (often merged with the linear combination that forms x), then the two ROUND rows.

## Evaluator change for coe21 ("1/2/2000" used as a number)

Operator coercion (`="1/2/2000"+0`) goes through ev_t2n (109) / ev_t2nb (115), not through a date function, so the evaluator owner has to route date text here. The parser chain is a leaf subroutine that keeps every word except A and STATUS, so the change is local to ev_t2nb: when the number parser rejected the text (today's branch that sets #VALUE!), instead of returning, output next = 354, PC = 0, A = the original text value (TAG 2, handle, as restored from the saved block words 13, 14), T0 = 2 (word 29), with the restored words otherwise, and LR, LP = the restored link (words 8, 9 from the saved block). dv_rest then returns to that link with A = the serial (36527 for "1/2/2000") or #VALUE!, exactly where ev_t2nb would have returned. Cost about L + 10 steps, and only for text the number parser rejected. No change to the parser chain is needed; tested here as mode 2 (test_dv.py::test_coercion).
