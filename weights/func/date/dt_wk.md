# dt_wk (id 350): WEEKNUM and ISOWEEKNUM

Hand-written (log/func-date-agent.md). PC 0 entry (save link in T9, T10, call dt_ymd with LR 350, LP 1); PC 1 finish. N1 = 0 WEEKNUM (B = return type 1, 2, 11..17, 21), 1 ISOWEEKNUM.

**Derivation.** J(Y) = 365 (Y - 1900) + floor((Y-1901)/4) - floor((Y-1901)/100) + floor((Y-1601)/400) + 1 + [Y > 1900] gives the Jan 1 serial including Excel's 1900-02-29 (checked by hand: J(1900) = 1, J(1901) = 367, J(2000) = 36526, J(2025) = 45658). Computed for Y - 1, Y, Y + 1 with FD-1 rows whose biases fold the year offsets. WEEKNUM = floor((n - J + o)/7) + 1 with o = (weekday of Jan 1 - start day) mod 7. ISO: th = 7 floor((n + 5)/7) - 2 is the Thursday of the ISO week (Monday-based); its year is Y - 1, Y or Y + 1 by two compares with J(Y) and J(Y + 1); week = floor((th - J(year of th))/7) + 1.

**Limits.** WEEKNUM(0) gives 0 (serial 0 is before Jan 1 1900); Excel's value not verified.

**Parameters.** 2536 dense parameters, 95 layers. **Tests.** test_dt_wk.py.
