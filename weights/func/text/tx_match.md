# Matching and unpacked buffers (ids 330 to 334, 339 to 343): tx_unp, tx_unw, tx_fs, tx_fm, tx_sb, tx_bc, tx_bw, tx_pk, tx_pkw, tx_sl

Hand-written, not generated. Log: log/func-text-agent.md session 2; WORKLOG decision T7.

Strings to be searched are first unpacked to one UTF-16 unit per word in EVAL_SCRATCH above SCR (a private frame, functions.md section 2; SCR is not advanced), so the matcher reads any unit with one read and no division.

- **tx_unp / tx_unw (330, 331)**: one read per packed word, one block write of up to 3 units (N = min(3, N1)); fold flag T7 upper-cases a..z and U+00E0..U+00FE (not U+00F7) for SEARCH. 2 steps per 3 units. Params 89 + 322.
- **tx_fs (332)**: FIND / SEARCH set-up: lengths, start check (s < 1 or s > Lw: #VALUE!), unpack both strings, matcher state. Params 1455.
- **tx_fm (333)**: prefix matcher with backtracking to the last '*' (the classic single-star glob algorithm; matching a prefix of text[p:] is a full match of the pattern followed by an implicit '*', which is why success is "pattern exhausted"). SEARCH tokens: '?' any unit, '*' any run, '~' escapes '?', '*' and '~' (a '~' before anything else is a literal '~'). A mismatch with no star to extend advances the start p; p reaching Lw is #VALUE!. One read per step; about 2 steps per compared unit. Exits go to (LR, LP), so FIND returns through tx_fin and SUBSTITUTE re-enters its loop. Params 3324.
- **tx_sb (334)** and **tx_sl (343)**: SUBSTITUTE. tx_sb validates instance (TRUNC, < 1: #VALUE!), returns the text unchanged for an empty old_text, unpacks old, text and new into F, W, NW, and enters the matcher. tx_sl: each match at m counts; it is replaced when instance is 0 (all) or equals the count: block copy W[last : m], block copy NW, last = m + Lo, continue at last (non-overlapping, left to right, as Excel). Not replaced: continue at m + Lo. At the end the tail W[last : Lt] is copied and the output buffer is packed. Params 1976 + 1404.
- **tx_bc / tx_bw (339, 340)**: block copy of unpacked words, 16 per round in 2 steps (block read, block write of N = min(16, N1)). Params 81 + 59.
- **tx_pk / tx_pkw (341, 342)**: pack an unpacked buffer into a heap string at HT: block read of 3 units, one packed write (units past the end masked by N1 >= 2, N1 >= 3), then one block write of the header. 2 steps per 3 units. Params 195 + 153.

Limits: SEARCH folds only ASCII and Latin-1 letters; FIND / SEARCH start > Lw is #VALUE! even for an empty find_text (Excel's answer for FIND("", "") is not verified); cost is O(Lw Lf) steps in the worst case.
