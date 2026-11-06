# dt_fin2 (id 348): DAYS, DAYS360, DATEDIF finish

Hand-written (log/func-date-agent.md; decision FD-3). One step. Inputs as left by dt_pair: y1 m1 d1 n1 in AS AR1 AC1 P0 (gathered by the dense v2), y2 m2 d2 n2 in T1 T2 T3 T8, N1, C, input word 0 = first packed unit word.

**v10 step bank (70 units).** N0 thresholds; C tag; method value nonzero (both signs); d1 = 31, d1 >= 30, d2 = 31, m1 thresholds, d1 >= 28, >= 29; [y = 1900] for both years; m2 thermometer for the month before the end month; lt = [(m2, d2) < (m1, d1)] via 32 m + d; dlt = [d2 < d1]; rev = [n1 > n2]; 18 IS_K pairs for the unit codes Y y M m D d MD md Md mD YM ym Ym yM YD yd Yd yD (c0 + 65536 c1, e.g. "MD" = 77 + 65536 x 68 = 4456525).

**DAYS360.** Leap test z4 - z100 + z400 + [y = 1900] (Excel treats 1900 as leap). lastFeb1 = [m1 = 2] and d1 + (1 - leap) >= 29, as one step unit with weights 2, 1, 1, -1. US: d1 -> 30 when 31 or last of February (d1 - [d1 = 31] + lastFeb1 + [lastFeb1 and d1 = 28]); d2 -> 30 when 31 and the adjusted d1 is 30. European: both min(d, 30). Result 360 dy + 30 dm + d2' - d1'.

**DATEDIF.** Y = dy - lt; M = 12 dy + dm - dlt; D = n2 - n1; YM = M mod 12 (FD-1); MD = d2 - d1 + dlt x (length of the month before the end month), which reproduces Excel's negative MD results; YD = n2 - n1 - 365 (y' - y1) - (Feb 29s between the start and its anniversary in year y'), y' = y2 - lt, with leap counts f(Y) = Y/4 - Y/100 + Y/400 over [y1 + [m1 > 2], y' - [m1 <= 2]] plus Excel's 1900-02-29. Start after end, an unknown unit or a non-text unit give #NUM!; a C error propagates.

**Limits.** DATEDIF units are matched on ASCII letters only and only the first packed word is read (units have at most 2 characters, so a longer string never matches). DAYS360 US end-of-February end dates are not adjusted (Excel's behaviour as I understand it; open point).

**Parameters.** 7097 dense parameters (the wide rows over the 110-word gather dominate), 68 layers. **Tests.** test_dt_pair.py.
