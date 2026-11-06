# dt_ymd (id 344): serial -> date and time parts

Hand-written (log/func-date-agent.md, 2026-11-06; decision FD-1, FD-2 in log/WORKLOG.md). One step, leaf subroutine.

**Computes.** From A = serial s: Y, M, D (Gregorian with Excel's 1900 quirk), H, MI, SE (time rounded to the nearest second, 24:00:00 wraps to 0), WD (WEEKDAY for return type B), n = floor(s). T0 selects which goes to A: 0 YEAR, 1 MONTH, 2 DAY, 3 HOUR, 4 MINUTE, 5 SECOND, 6 WEEKDAY.

**Registers.** Reads A, B (only for T0 = 6), T0, LR, LP. Writes words 0..7 (next = LR, PC = LP), STATUS = 0, A, T1..T7 = Y M D H MI SE WD, T8 = n. Everything else passes through (B, C, AS..N1, T0, T9, T10, L0..L23), which is what lets dt_pair park date 1 in AS..AR2 and dt_date / dt_wk keep the caller link in T9, T10.

**Derivation by layer group.**
- v5..v7: tag thresholds (IS_K style step banks) for A and B; okA = [tag in {1, 3}], isB8 = [B missing].
- v13..v22: x0 = okA * PA (mul gating, so a text handle never enters arithmetic); validity 0 <= x0 < 2958466 by two exact real compares; s = valid * x0.
- v23..v29: n = FLOOR(s) (ROUND then subtract step(r - s)); f = s - n is exact.
- v31..v35: lt60 = [n < 60], is0 = [n = 0], gt60 = [n > 60]. The day count z = n + 693899 + lt60 converts the Excel serial to days since 0000-03-01 (Hinnant's days-to-civil origin: 1970-01-01 = serial 25569 = 719468 days, so the offset is 719468 - 25569 = 693899); the + lt60 undoes the fictitious leap day for serials below 60.
- v36..v75: Hinnant civil_from_days with FD-1 floors: era = z / 146097, doe, yoe = (doe - doe/1460 + doe/36524 - doe/146096) / 365, doy, mp = (5 doy + 2) / 153, day offset round(30.6 mp) = floor((153 mp + 2)/5) (checked by hand for mp = 0..11). doe/146096 is a single step test (doe = 146096). Constants: 1/146097 = 6.844767517471e-6 (checked by multiplying back: 146097 x 6.8447675 = 999999.997), 1/1460, 1/36524 = 2.73792574747e-5 (multiplied back to 100000.0000), 1/365, 5/153 = 0.032679738562, bias of the era row 693899.5/146097 - 0.5 = 4.249580758.
- Time: sec = ROUND(86400 f), wrap = [sec >= 86400]; h = sec'/3600, total minutes = sec'/60 by FD-1 (the wrap correction is folded in as -24 and -1440 on the wrap input).
- v83: Y = yoe + 400 era + [mp >= 10] + is0; M = mp + 3 - 12 [mp >= 10] - 11 is0; D = doy - e + 1 - 31 is0 + is60 (is60 = 1 - lt60 - gt60). Overrides give serial 0 = 1900-01-00 and serial 60 = 1900-02-29.
- WEEKDAY: w0 = (n + 6) mod 7 (0 = Sunday; serial 1 is Sunday), start-day offset kk from a thermometer over the return type (1, 2, 3, 11..17; truncated toward zero), WD = ((w0 - kk + 7) mod 7) + 1 - [type 3].
- Errors (v96..v113): priority A error, A wrong type (#VALUE!), then for WEEKDAY B error, B wrong type, then #NUM! for an out-of-range serial, then #NUM! for an invalid return type. Result word by MUX_INT (M = 2^23).

**Limits.** Text serials are #VALUE! (no DATEVALUE coercion yet). Time rounding at an exact half second is half-to-even. Date parts use floor of the serial, time parts round to the second (a serial a few microseconds before midnight shows DAY of the earlier date and HOUR 0).

**Parameters.** 1196 dense parameters (weights and biases, zeros included), 124 layers.

**Multi-role weights.** T1..T8 carry results for internal callers and are ignored by the function-level caller; no word holds two meanings at once.

**Tests.** tests/output/func_date/test_dt_ymd.py (63 cases).
