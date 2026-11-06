# Weight block note: xml_tok (id 460)

Hand-written. Not generated. Log: log/files-agent.md 2026-11-06. Tests: tests/output/files/test_xml_tok.py (4 pass).

**Computes.** A byte-level XML tokenizer for .xlsx parts. Input bytes at P0 .. N0 - 1, one byte per word (the planned inflate output layout in FILE_SCRATCH). Output tokens at P1: a byte of text, tag name, attribute name or value; -1000 - b start tag whose name starts with byte b; -2000 - b attribute whose name starts with b; -3 attribute value starts; -4 `>`; -5 `/>`; -6 end tag `</` (name bytes follow); -9 end of input. Folding the first name byte into the marker keeps one token write per input byte at most.

**Calling convention.** next = 460, PC = 0, LR, LP, P0, N0, P1. Returns to (LR, LP), STATUS 0, P1 after the -9 token. Clobbers P0, T0. No locals.

**States (T0).** 0 text, 1 after `<`, 2 tag name, 3 inside a tag, 4 attribute name, 5 after `=`, 6 value in `"`, 7 value in `'`, 8 end tag name, 9 after `/` in a tag, 10 skipping `<? ... >` or `<! ... >`. Classes: `< > / = " ' ? !`, white space (space, tab, LF, CR), other. 27 AND units, one per (state, class group), listed in the .wt comments with their token and next state.

**Derivation.** Same template as csv_scan.md: IS_K pairs, AND units gated by phase 2 and not end, big-M relu muxes for addresses and the gated byte (M = 256 for bytes, 2^23 for addresses and state), integer output rows (exact, R4). Phases: 0 (T0 = 0, read P0), 2 (process), 3 (read P0).

**Parameters.** 2,758 dense (v8 371, v10 1,296, v11 775, v16 360, v19 588; counted by hand from the layer shapes). **Steps.** 1 + 2 per byte that makes a token + 1 per byte that makes none + 1.

**Limits.** Entities (`&amp;`, `&lt;`, `&#...;`) are passed as bytes, not decoded. CDATA is not recognised. A `>` inside a comment ends the skip early. Namespaces are not split (prefix bytes are part of the name). UTF-8 bytes are passed unchanged. **Multi-role weights.** None.
