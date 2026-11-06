# Weight block note: lg_sheet (id 303)

Hand-written. Not generated. Log: log/func-logic-agent.md.

**Computes.** SHEET (T2 480) and SHEETS (T2 481). PC 0: SHEETS() reads SHEET_COUNT (zero page 0x0F) and goes to PC 1; SHEETS(tag 9 or 5) = 1; SHEET() = 1; SHEET(tag 9) = FLOOR(K 2^-34) + 1 (the SHEET field of the packed key, encodings/address.md section 3; the scaling is an exact power of two); SHEET(tag 5) reads reference record word 0 and goes to PC 1 with T0 = 1; an error argument is returned; any other argument gives #N/A for SHEET and #REF! for SHEETS. PC 1: A = (1, read word + T0). Gates are steps of sums of phase, function, argument-present and tag bits; four gated values in one mul.

**Limits.** SHEET() assumes the formula is on sheet 0 (the evaluator has no sheet register yet). Sheet names as text are not looked up. 3D references count as one sheet. Results for non-reference, non-text arguments are unverified. **Parameters.** 424. **Steps.** 1 or 2, + FN_RET. **Tests.** test_sheet.py (8).
