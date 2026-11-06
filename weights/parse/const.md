# Note: weights/parse/const.wt (id 76)
Hand-written. Not generated. Shared conventions, register map and limits: weights/parse/README.md. Log: log/parse-agent.md 2026-11-06; decisions P1 to P5 in log/WORKLOG.md.

**Phases.** PC 1 prefix, 2 suffix, 3 numconv returned, 5 plain text, 6 apostrophe text returned from lstr. RDOK 0 in PC 1 or 2 fetches char I.
**Gates (v26, ANDs over class and phase thresholds).** Prefix: G2 space or '+' (skip), G3 '-' (NEG), G4 '(' (NEG and PAR), G5 '$' (skip), G6 digit -> lnum PC 1, G7 '.' -> lnum PC 2, G8 anything else -> ckey 77 from char 0 (I = 0 via MUX_INT R0). Suffix: G9 '%' once, G10 ')' when PAR, G11 space, G12 end with PAR closed -> numconv (X2 = FRAC += 2 PCT through G20, X6 = 76, X7 = 3), b_txt (anything else) -> PC 5. PC 3: G14 number, A = (1, +-TV) with the sign chosen by mul gates gpos and gneg (NEGb = [NEG >= 1]); G15 TK 11 -> text. PC 5 (G16): A = (2, HS), the kernel's own string. PC 6 (G17): write HEAP_TOP = HT, A = (2, TV). PC 3, 5, 6 -> restore.
**Clears.** X0..X5 and TK are zeroed on G6, G7, G8 (mul keep gates 1 - G6 - G7 - G8), so stale values are never read by lnum or ckey.
**Limits.** Lenient: several signs or '$' in any order are accepted ("--5" reads -5); currency only '$'; no dates, times, fractions or other locale forms. 2,136 parameters. **Multi-role weights.** NEG, PCT, PAR in B and C words (README).
