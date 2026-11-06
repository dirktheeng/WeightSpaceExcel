# weights/format: number format engine (ids 192..231 used of 192..255)

Hand-written. Not generated. Log: log/format-agent.md; decisions F1..F6 in log/WORKLOG.md ("2026-11-06 Stage 3 to 4: number format engine"). Notes: fx_dec.md (192), fx_rnd.md (193), fx_emit.md (194, 200..209), fx_general.md (196, 197, 199), fx_fin.md (212..215), fc_compile.md (220..225), built-in strings in fx_general.md (226..230), stage runner tests/output/format/test_stage_formats.py; fx_main, fx_tab, fx_sel, fx_sec, fx_go are described here.

## Calling the engine (until encodings/functions.md exists)

Call fx_main (198) by the link convention (encodings/control.md section 4).

| In | Meaning |
|---|---|
| A (13, 14) | value (encodings/value.md); numbers and text are formatted |
| B.TAG (15) | format id F: 0 = General, otherwise FMT_TABLE[F] |
| B.PAY (16) | W = column width in characters (0 = no limit and no fill, as for TEXT; General then uses 11) |
| LR, LP | return link |

| Out | Meaning |
|---|---|
| A | (2, h): display string in the text heap (HEAP_TOP advanced). Text with no text section, blank, boolean and error values come back unchanged with STATUS = 1 (the caller shows them as their own text) |
| C.TAG | color: 0 automatic, 1 Black, 2 Blue, 3 Cyan, 4 Green, 5 Magenta, 6 Red, 7 White, 8 Yellow, 9 + N for [ColorN] |
| C.PAY | alignment for General horizontal alignment: 1 left (text), 2 centre, 3 right (numbers) |

Clobbers A, B.TAG is kept, C, AS..AS2, P0, P1, N0, N1, T0..T10. Locals L0..L23 are not touched. fx_init (199) must run once at boot (writes the General token records); it is a leaf that returns to (LR, LP).

Renderer use: F = style word 0 mapped to a format id (see FMT_TABLE), W = column width in characters, then copy the heap string (weights/ui hcopy) and draw it with the returned alignment and color. TEXT(value, code): the text agent writes the code string, puts its handle in a free FMT_TABLE entry (or a reserved scratch id) and calls with W = 0.

## Memory used (proposed carve of FORMAT_STORE, see "Changes needed elsewhere")

| Range | Use |
|---|---|
| 0xC000..0xC7FF | FMT_TABLE: 512 entries of 4 words [code string handle, compiled record address (0 = not compiled yet), 0, 0], entry F at 0xC000 + 4 F. 0xC003 (entry 0, word 3) is COMPILE_TOP (0 = never used, base 0xCA00) |
| 0xC800..0xC8FF | FMT_BUF: emitted units (one per word) before packing; a fill marker is 65536 + unit |
| 0xC900..0xC91F | General token records (fixed at 0xC900, scientific at 0xC910), written by fx_init |
| 0xCA00..0xFFFF | compiled records, bump allocated from COMPILE_TOP |

**Compiled record** at CR: [nsec, c1op, c1val, c2op, c2val, s0, s1, s2, st] (st = text section, the 4th section or a single section containing '@'; 0 = none), then per section a 9-word header [kind (0 number, 2 text), color, k (fraction digits), nint (integer placeholders), TH (thousands separator), scale (2 per '%', -3 per scaling comma), sci, nexp, NC0 (code of the first token)] followed by its tokens and a 0 END word. Condition ops: 1 <, 2 <=, 3 =, 4 >=, 5 >, 6 <>.

**Token word** = arg + 65536 code + 2^20 nc (nc = code of the next token, so fx_fetch can route straight to its executor). Codes: 0 END, 1 LIT (arg = unit), 2 INT (arg = 4 jl + type), 3 POINT (arg 1 = General's conditional point), 5 FRAC (arg = 4 j + type, j = 1..k), 6 EXP (arg bit 0 'E-', bit 1 'e'), 7 EXPD (4 jl + type), 8 TEXT '@', 9 FILL (arg = unit). type 0 '0', 1 '#', 2 '?'; jl counts placeholders from the left.

## Register use during formatting (caller-saved words only)

AS s (sign), AR1 e, AC1 m then M (digit stream, next digit = floor(M / 1e14)), AR2 R (integer digits left in the stream), AC2 k, AS2 X (exponent shown), P0 TP (token pointer), P1 BP (buffer pointer), N0 nint, N1 sci (2 after a fill was emitted), T0 CUR (token kept while an executor stays), T1 TH, T2 scale (then the string handle in fx_pack), T3 nexp, T4 kind, T5 SUB (comma or sign pending), T6 XR (exponent digits left), T7 minus wanted, T8 NC, T9 and T10 continuations (fx_rnd's and fx_dec's next). Compiler registers: fc_compile.md.

## Small networks described here

| Id | File | Step | Params |
|---|---|---|---|
| 198 | fx_main | entry (above): General, table read, or immediate return | 286 |
| 216 | fx_tab | compiled? block read of the record header into fx_sel : read the code handle and compile | 59 |
| 217 | fx_sel | block consumer: section choice (sign, zero, conditions, text), minus flag, block read of the section header into fx_sec | 2685 |
| 218 | fx_sec | block consumer: loads k, nint, TH, scale, sci, nexp, NC0, color, alignment; number -> fx_dec, text -> fx_go; a number in a text section ("@") -> General | 323 |
| 219 | fx_go | writes '-' when T7, then fx_fetch | 29 |
| 231 | fx_eng | between fx_dec and fx_rnd: T0 = u + 1, u = e mod n (n = nint, 1..6), so scientific exponents are multiples of nint; note fx_rnd.md | 217 |

fx_sel: a section chosen by a true condition (cond1, or cond2) adds no minus sign; a default section does (stage case cfc03, decision F8). Comparisons x < v and x > v are R2 sign tests (exact); x = v is their complement. Section rules are in the header comment of fx_sel.wt. All selections are MUX_INT on addresses (< 2^23).

## Totals and cost

36 networks, 27,136 dense parameters (zeros included; session 3 added fx_eng 217, fc_br tails 772, fx_rnd 2). Every number format call now takes one more step (fx_eng); the step counts below are from session 2. Steps (harness steps, measured in tests): General 1/3 -> "0.333333333" 49, 123456789012 -> "1.23457E+11" 56, 42 -> 38; "#,##0.00" 1234567.891 -> "1,234,567.89" 72 including the one-time compile, 5 -> "5.00" 33 once compiled. Each displayed unit costs 2 steps (token read and write) plus about 1 step per unit to pack.

## Limits (open items)

- Dates and times (y m d h s AM/PM, [h] [m] [s]) are not interpreted: date letters are literals and the value is formatted as a number. Fractions (# ?/?) are not interpreted ('/' is a literal). Designs: log/format-agent.md, session 3 hand-off.
- Engineering exponents: every scientific section with nint > 1 uses exponents that are multiples of nint (F7). A carry there ("##0.0E+0" of 999.96) shows "100.0E+1" instead of "1.0E+3".
- Brackets: colors, [ColorN], conditions (integer or decimal values, negative allowed; decimal values are BV 10^-k with one correction step, F8) and [$...] (the text after '$' up to '-' or ']' is shown as literals) are done. [h] [m] [s] and other brackets are skipped.
- General's width is in characters (W, max 11); Excel fits by pixels (open question). Values below 1e-304 display as 0.
- Booleans and errors are returned unformatted (STATUS = 1, C.PAY = 2 centre), which is Excel's behaviour: no number format section applies to them (TEXT(TRUE, "0") is "TRUE").

## Changes needed elsewhere (not made: files not mine)

1. encodings/memory-map.md section 2 and 7: FORMAT_STORE 0x8000..0xFFFF holds 2048 style records; this engine uses 0xC000..0xFFFF. Proposed: style records 0..1023 at 0x8000..0xBFFF, number format region 0xC000..0xFFFF as above, and a note that style word 0 holds a format id F (FMT_TABLE index) rather than a string handle (0 still means General).
2. weights/kernel/boot.wt: call fx_init (199) once (leaf call, returns to LR/LP).
3. weights/ui cell renderer: call fx_main (198) with F = the cell style's format id and W = column width in characters (64 px column = 8.43 chars; until pixel fitting exists use W = 10 for the default column) instead of ui/fnum (131), then copy the heap string.
4. Text agent (TEXT function): see "Calling the engine". Built-in ids 1..22 and 37..49 are loaded at boot by fx_init (fx_general.md); the file loader maps an xlsx numFmtId below 50 straight to F and custom numFmts to free ids 50..511.
5. Boot (weights/kernel): set HEAP_TOP before calling fx_init; fx_init now takes about 1,900 steps (once).
6. encodings/memory-map.md change 1 above is applied (authorized 2026-11-06).
