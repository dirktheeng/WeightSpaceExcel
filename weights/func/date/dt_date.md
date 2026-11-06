# dt_date (id 345): DATE, and EDATE / EOMONTH entry and finish

Hand-written (log/func-date-agent.md, 2026-11-06; decisions FD-1, FD-3). One step per phase.

**Phases.** PC 0 DATE(A = year, B = month, C = day). PC 3 / PC 4: EDATE / EOMONTH entry: T9, T10 = LR, LP; call dt_ymd (next 344, T0 0, LR 345, LP 1 or 2). PC 1 EDATE finish, PC 2 EOMONTH finish: inputs T1..T3 = y m d of the start date from dt_ymd, A = dt_ymd result (an error propagates), B = months; return to T9, T10. Any PC above 4 behaves as PC 4 (not trapped; open point).

**Computes.** Arguments are clamped (year to [-1, 10000], month to +-1e6, day to +-1e8) and truncated toward zero. DATE: year 0..1899 adds 1900, year < 0 or >= 10000 is #NUM!. Both sets of (Yr, Mo, Da) are computed in parallel: S1 = serial(Yr, Mo, Da) and S2 = serial(Yr, Mo + 1, 1) - 1 (the month end). DATE returns S1, EDATE min(S1, S2) (a day past the month end clamps to the month end), EOMONTH S2, with Mo = m + trunc(months) in the finish phases.

**Derivation.** carry = floor((Mo - 1)/12) by FD-1 (rows c Mo - 0.5416666..., c Mo - 0.4583333...); month index m0 = Mo - 1 - 12 carry; Hinnant days_from_civil on yo = yy - [m0 <= 1] + 100000 (the 250-era offset keeps every floor on positive integers for any clamped month), era = yo/400, yoe, floor(yoe/4), floor(yoe/100), day of March-based year round(30.6 mp). True serial of the month start Bt = 146097 era + doe - 37218149 (= -693899 - 250 x 146097). Excel quirk: Bt < 61 subtracts 1 (months before 1900-03 are one day earlier in Excel serials). Valid results: 0 <= res <= 2958465 for DATE, 1 <= res for EDATE and EOMONTH.

**Limits.** |month| beyond 1e6 or |day| beyond 1e8 are clamped; such inputs always give #NUM! except contrived pairs of an extreme month with an opposite extreme day. EDATE and EOMONTH accept a boolean start (Excel gives #VALUE!). 1904 date system not supported (DATE_1904 is ignored).

**Parameters.** 2568 dense parameters, 141 layers.

**Multi-role weights.** The two serial computations share every layer (stacked rows); the phase gates select between them and the pass-through, mutually exclusive by the PC one-hot.

**Tests.** tests/output/func_date/test_dt_date.py.
