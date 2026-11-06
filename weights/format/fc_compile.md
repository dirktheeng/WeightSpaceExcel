# Weight block notes: format code compiler (ids 220..225)

Hand-written. Not generated. Log: log/format-agent.md "compiler and the full engine"; decisions F3, F4.

Compiles a format code string into the record of README.md. Runs once per format id (fx_tab calls it when the table entry has no record) and returns to fx_main.

**Registers.** C.TAG CH (unit handed to fc_br), C.PAY CR, AS SH (section header), AR1 SEC, AC1/AR2/AC2 BK/BV/BD (bracket state), AS2 POS (unit in the current word; 3 = read the next word), P0 SRC, P1 OUT (next token address), N0 LEFT, N1 W (rest of the current word), T0 PT (pending token, 0 none), T1 TH, T2 SCALE, T3 NEXP, T4 KIND, T5 MODE, T6 NINT, T7 K, T8 PH (0 integer part, 1 after '.', 2 exponent), T9 PCm (pending commas), T10 COLOR. A, B, LR, LP and locals are untouched.

| Id | File | Step | Params |
|---|---|---|---|
| 223 | fc_start | SRC = H + 2; reads COMPILE_TOP | 18 |
| 224 | fc_start2 | CR = COMPILE_TOP (0xCA00 when 0); reads the length | 38 |
| 225 | fc_start3 | initial state (POS 3, SH = CR + 9, OUT = CR + 18); FMT_TABLE[F].compiled = CR | 120 |
| 220 | fc_char | one unit per step, or one word read (PC 1 marks x0 as the new word) | 6960 |
| 221 | fc_br | one unit inside [ ]; ']' sets the color or writes the condition (2-word block write); [$...] literals (1-word block write) | 3286 |
| 222 | fc_send | section end in 6 phases (pending token, header block write, section pointer, text section pointer, nsec, COMPILE_TOP) | 3391 |

**fc_char.** Unit c = W - 65536 floor(W / 65536) (W 2^-16 exact, floor by ROUND(y - 0.499995)). 17 character classes and 8 modes are one-hots built as [v >= k][v <= k] with mul layers; 33 gates combine them with the phase and flags (each an AND as step(sum - (n - 0.5))). Normal mode: '0' '#' '?' make INT (jl = NINT), FRAC (j = K + 1) or EXPD (jl = NEXP) by phase; a pending comma before an integer placeholder sets TH, at '.', 'E+' or the end it becomes scale -3 each; '.' starts the fraction (a second '.' is literal); '%' is a literal and scale + 2; 'E'/'e' wait for '+' or '-' (otherwise 'E' is a literal and the unit is reprocessed without being consumed); '"', '\', '_', '*', '[' change mode; '@' makes TEXT and kind 2; ';' and the end go to fc_send (the end sets MODE 9); anything else is a literal. Tokens are written one behind so each carries its successor's code: the step that produces token t writes token t - 1 with nc = code(t) at OUT (or code(t) at SH + 8 for the first token). Products with gates are MUX_INT pairs (B = 2^17 to 2^25) or mul layers (W).
**fc_br.** BD: 0 new, 1 name, 2 condition, 3 other, 6 condition with '-'. Names accumulate BK = 32 BK + letter (a = 1, case folded) and digits in BV; the 9 keys black 2491499, blue 78501, cyan 123950, green 7935150, magenta 13999716993, red 18596, white 24389253, yellow 844509687, color 3650034 (hand-computed) are matched at ']'. Conditions: '<' '=' '>' start op 1, 3, 5; '=' after 1 or 5 gives 2 or 4, '>' after 1 gives 6; digits accumulate BV; '-' sets the sign. Decimal values (session 3 tail v100..v142): '.' adds 8 to BK and each later digit 8 more, so BK = op + 8 (1 + k); at ']' op = BK - 8 sum [BK >= 8 j] and value = BV 10^-k with one correction q' = q - (q 10^k - BV) 10^-k (fl(0.3) for "0.3"). Currency (tail v47..v99): BD 0 + '$' -> BD 4; in BD 4 '-' -> BD 3 (skip) and any other unit but ']' is emitted as a LIT token by fc_br itself through the pending-token protocol (PT > 0: mem[OUT] = PT + 2^20, OUT + 1; PT = 0: mem[SH + 8] = 1; PT' = 65536 + c), MUX_INT B = 2^22. Both tails were appended after the old output, so no earlier layer moved.
**fc_send.** Always block mode (72 outputs, N = 0, 1 or 8) so its state is always forwarded as 64 words. The END word after each section is left as fresh 0.

**Limits.** No dates, fractions, or "General" inside a code (README limits). Strings longer than the FMT_BUF are not checked. Multi-role words: BK is a name key or a condition op by BD type; MODE 9 marks the end only between fc_char and fc_send. Tests: test_compile_number, test_compile (8), test_compile_text_section, test_custom (23), test_brackets (33), test_compiled_once_and_reused, test_text_value_shown_as_is.
