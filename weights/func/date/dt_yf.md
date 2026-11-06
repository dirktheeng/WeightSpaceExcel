# dt_yf (id 353): YEARFRAC finish

Hand-written (log/func-date-agent.md; decisions FD-3, FD-5). One step, reached from dt_pair with N1 = 3.

**Computes.** Swaps the dates so date 1 <= date 2 (mul gating of the differences). Basis from C (truncated; missing or blank 0; outside [0, 5) #NUM!). Numerator and divisor: basis 0 Excel US 30/360 count (rules in the order: both 31; d1 = 31; d1 = 30 and d2 = 31; both last of February; d1 last of February) over 360; basis 1 actual days over 365 or 366 when the span is within a year (366 when the same leap year, or a Feb 29 lies inside), otherwise days x years / (J(y2 + 1) - J(y1)); basis 2 days / 360; basis 3 days / 365; basis 4 European 30/360 over 360.

**Division (FD-5).** y = 1/Dv by Newton y <- y (2 - Dv y), 6 steps, from y0 = 2^-j where 2^(j-1) <= Dv < 2^j (a 13-unit thermometer; Dv y0 in [0.5, 1) so the error squares from 1/2 down below 2^-64). q0 = Nm y, then the split residual of dt_time: r = Nm - Dv hi - Dv lo, q = q0 + r y. Correctly rounded for the constant divisors 360, 365, 366 (their products with hi and lo are exact); within an ulp or two for the multi-year average divisor.

**Limits.** Basis 0 and 1 follow the published reconstruction of Excel's rules; untested corner: start date Feb 29 1900. Text dates not accepted.

**Parameters.** 3452 dense parameters, 132 layers. **Tests.** test_dt_yf.py.
