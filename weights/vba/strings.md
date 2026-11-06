# Weight block notes: VBA strings (ids 432, 439, 440, 443, 444, 445)

Hand-written. Not generated. VSTR records: encodings/vba.md section 2 (one unit per word). Log: log/vba-agent.md; decisions VB2, VB7.

| Id | File | Computes |
|---|---|---|
| 439 | vs_rd | copy loop, read side: CNT > 0: block read 8 at SRC; else return to (LR, LP) |
| 440 | vs_wr | block write the 8 units at DST, DST += min(8, CNT) (CNT - relu(CNT - 8)), SRC += 8, CNT -= 8. Up to 7 words past the end are overwritten; destinations are always at a buffer or heap top, so that space is free |
| 443 | vc_cstr | CStr subroutine: string unchanged, Empty -> VSTR_EMPTY, Boolean -> new record, number -> ev_totext then unpack (UXIT 445) |
| 444 | vc_cnum | after ev_totext: read the packed length -> vu_wr |
| 445 | vc_fin | header length, VHT, A = (24, record), return to the saved link (SLR, SLP) |
| 432 | vi_cat | a & b in 7 phases (two CStr calls, two copies, header, result tag and payload); every output is cur + sum of phase-gated products from one 19-product mul layer |

**Cost.** "x = " & 5: about 60 steps (CStr of 5 dominates). **Limits.** Strings are never freed. **Multi-role weights.** L58..L63 hold b, ha, hb and S0 only inside vi_cat; SLR, SLP, VS0 only inside a CStr call. **Tests.** test_strings_concat_msgbox.
