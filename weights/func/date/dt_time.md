# dt_time (id 346): TIME

Hand-written (log/func-date-agent.md; decision FD-4). One step.

**Computes.** h, m, s truncated toward zero (after clamping to +-1e6); any argument > 32767 or a total 3600 h + 60 m + s < 0 gives #NUM!; secs = total mod 86400 by FD-1 (c = 1/86400 folded into 1/24, 1/1440, 1/86400 weights); result secs / 86400.

**Correct rounding (FD-4).** secs/86400 = (secs/675) / 128 and the /128 is exact. q0 = secs fl(1/675); k = ROUND(q0 2^26), hi = k 2^-26, lo = q0 - hi (exact); 675 hi and 675 lo are exact (at most 43 and 45 significant bits), so r = secs - 675 hi - 675 lo is the exact residual secs - 675 q0; q = q0 + r fl(1/675) is the correctly rounded quotient (8:00 gives the double nearest 1/3).

**Limits.** Exact ties cannot occur (675 is odd and secs < 2^17). Errors in order A, B, C, then #NUM!.

**Parameters.** 923 dense parameters, 82 layers. **Tests.** tests/output/func_date/test_dt_time.py.
