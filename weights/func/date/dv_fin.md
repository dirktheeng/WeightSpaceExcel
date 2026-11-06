# dv_fin (id 356): interpretation and result of the date/time text parser

Hand-written (log/func-date-agent.md session 2; decision FD-7). Three phases.

| PC | Does | Next |
|---|---|---|
| 0 | choose the date form, validate; AS AR1 AC1 = y m d; T2 plain, T3 hasdate, T4 hastime, T5 err, T6 mode, T8 = d1; call TIME with A B C = h mi s, LR 356, LP 1 | 346 |
| 1 | T1 = A.PAY (time fraction); call DATE with A B C = y m d, LR 356, LP 2 | 345 PC 0 |
| 2 | result by mode; block read of 32 words at RSP - 32 (the dv_ent spill) | 357 |

**Date forms** (nf' = date numbers after removing an "h AM" hour, hm = month name present): no name and 3 numbers: y/m/d when the first is > 31, else m/d/y; no name and 2 numbers with the second > 31: m/yyyy, day 1; name and 2 numbers (name before or after the first): day = first, year = second; name and 1 number > 31: month and year, day 1; no name and 1 number with no time: plain integer (coercion mode only). Anything else with a date part is #VALUE!. Years 0..29 become 2000..2029, 30..99 become 1930..1999, 100..1899 and > 9999 are rejected; month 1..12; day 1..month length, February 29 valid in leap years (y/4, y/100, y/400 by FD-1 floors) and in 1900 (Excel's leap day, serial 60).

**Time.** h:mm or h:mm:ss (one time number alone, "6:", is rejected), or "h AM"/"h PM" with no colon; minutes and seconds below 60; with AM/PM the hour is 0..12 (12 AM is 0, PM adds 12 below 12), without it below 10000. The fraction comes from dt_time, so it is correctly rounded and wraps at 24 hours.

**Results.** DATEVALUE: the serial when a date part exists (a time-only text is #VALUE!; Excel's behaviour for that case is not verified). TIMEVALUE: the time fraction when a date or time part exists (a date alone gives 0). Coercion: serial + fraction, or the plain integer. An error argument propagates, any other non-text is #VALUE!.

**Limits.** No date without a year ("1/2", "Jan 2": Excel uses the current year; here #VALUE!). "h AM" after a three-number date is rejected. Coercion of hours >= 24 wraps like TIMEVALUE (Excel's "25:00" + 0 is 1.0417; here 0.0417). Decimal and exponent number text is not coerced here (only digits); the evaluator's own number lexer covers those.

**Parameters.** 3666 dense parameters, 111 layers. **Multi-role weights.** Words 19..21 and 30..37 hold PC 0 results through the two calls (dt_time keeps words 15..63, dt_date keeps 15..28 and 30..37). **Tests.** test_dv.py, test_dv_abi.py.
