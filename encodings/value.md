# Encoding: VALUE (cell values and their types)

Status: design, stage 1. Decision records: log/WORKLOG.md "2026-11-06 Stage 1: shared encodings design", decisions D1 (state width), D2 (two-word values), D3 (number plan). Related: encodings/address.md, encodings/memory-map.md, encodings/control.md, encodings/primitives.md.

## 1. Words are float64

Every harness word (state word, memory word) is an IEEE 754 double (numpy float64). Two invariants hold for every word every network ever produces, in every layer output that feeds a dense or mul layer:

- **V1 (finite).** No NaN and no infinity. A dense layer computes `0 * inf = NaN` in every row that has a zero weight on that input, so a single infinity would poison every output of the next dense layer. Any operation that can overflow is guarded (encodings/primitives.md, SAFE_MUL, SAFE_ADD); an unguarded possibly infinite intermediate may feed only a `step` layer, whose output is finite.
- **V2 (exact integer domain).** Every word used as an integer (tags, codes, addresses, ids, counters, packed keys, packed characters) is an integer with absolute value below 2^53. Sums of such integers with integer weights are exact in any summation order, so dense rows with many terms are safe for them. Real-valued arithmetic follows the stricter rules in encodings/primitives.md section 1.

## 2. A value is two words: TAG and PAY

A value V is the pair (TAG, PAY). In state registers it occupies two adjacent words (encodings/control.md, registers A, B, C). In memory it occupies two adjacent words of a record (cell record words 1 and 2, operand stack entries, array elements, VBA variables).

| TAG | Type | PAY |
|---|---|---|
| 0 | blank (empty cell, or a reference to one) | 0 |
| 1 | number (includes dates and times as serials) | the double itself |
| 2 | text | handle: address of the string header in the text heap (encodings/memory-map.md); the empty string "" has the fixed handle TEXT_EMPTY |
| 3 | boolean | 0 FALSE, 1 TRUE |
| 4 | error | ERROR.TYPE code (table below) |
| 5 | reference | pointer to a reference record (sheet, r1, c1, r2, c2, sheet2) in the evaluator scratch area; used for function arguments taken by reference (SUM, OFFSET, ROW, INDEX results) |
| 6 | array | pointer to an array record: [rows, cols, then rows*cols values of 2 words each] |
| 7 | lambda | pointer to a lambda record (parameter count, formula record, captured LET environment) |
| 8 | missing argument | 0; an omitted argument such as the second argument in `=IF(A1,,1)`, which Excel treats differently from blank in some functions |
| 9 to 15 | reserved for the cell engine | |
| 16 to 63 | VBA Variant subtypes (encodings/memory-map.md, VBA state); defined in stage 9 | |

Error codes (Excel's ERROR.TYPE numbering, so ERROR.TYPE and ISERR are direct reads of PAY):

| PAY | Error | PAY | Error |
|---|---|---|---|
| 1 | #NULL! | 8 | #GETTING_DATA |
| 2 | #DIV/0! | 9 | #SPILL! |
| 3 | #VALUE! | 10 | #CONNECT! |
| 4 | #REF! | 11 | #BLOCKED! |
| 5 | #NAME? | 12 | #UNKNOWN! |
| 6 | #NUM! | 13 | #FIELD! |
| 7 | #N/A | 14 | #CALC! |

**Why a scalar tag rather than one-hot.** A one-hot tag would cost 9 or more words per value in every register and every memory record, and a memory read moves one word per step, so a one-hot tag would cost 9 reads to load a type. The scalar tag costs one word and one read. A network that needs type indicators derives them inside its forward pass with the ONEHOT primitive (two step units per tag value it cares about, encodings/primitives.md). Most operations need only one or two indicators (for example "is number" and "is error").

**Why tag 1 is number.** The most common test is "is this a number"; tag 1 lets `IS1 = step(TAG - 0.5) - step(TAG - 1.5)`. Blank is 0 so a zeroed memory word reads as blank with no initialisation pass, which is also why an empty cell slot needs no clearing (encodings/memory-map.md).

**Why PAY is never shared across types in arithmetic.** Arithmetic networks use PAY as a double only after gating by the number indicator (or the coercion result). Text handles, error codes and pointers are integers that would otherwise be added as if they were numbers; the gate makes the number role and the handle role mutually exclusive (non-interference by exclusive gating on TAG).

## 3. Type ordering for sort and comparison

Excel orders ascending: numbers < text < FALSE < TRUE, with errors and blanks placed last by sort (blanks always last, in both directions). The comparison key is a pair (class, within-class key) with class 0 number, 1 text, 2 boolean, 3 error, 4 blank. The tag codes are not in this order on purpose (tag codes are chosen for cheap indicators, not ordering); the class is computed from the tag indicators by one dense row: `class = 1*IS2 + 2*IS3 + 3*IS4 + 4*IS0`. Comparison operators (`<`, `=`, ...) between different classes follow Excel's rules (number < text < boolean) and are implemented in the compare networks of stage 1, using this class value.

## 4. Numeric precision plan (Excel 15-digit behavior)

Excel stores numbers as IEEE doubles, so the PAY of a number is exactly the double Excel would hold. The 15-digit behavior lives in four places, each handled by a defined primitive chain:

1. **Entry and formula literals.** Excel keeps the first 15 significant digits typed and replaces later digits with zeros (truncation, not rounding: typing 12345678901234567 stores 12345678901234500). The number lexer accumulates at most 15 significant digits into an exact integer mantissa M (M < 10^15 < 2^53, exact by V2) and counts dropped digits and the decimal point position into a decimal exponent E. The value is M * 10^E.
2. **Decimal to double.** When |E| <= 22, 10^|E| is an exact double, so one IEEE multiply (mul layer) or one correctly rounded divide (DIV primitive) gives the correctly rounded result; this is the classic exact fast path, and with M < 2^53 it covers every number with at most 15 significant digits and magnitude between about 1e-22 and 1e37. Outside that range the value is scaled in two stages (for example M * 10^22 * 10^(E-22)), which can be off by one unit in the last place; that is far inside the 1e-12 tolerance of docs/ACCEPTANCE.md, and is logged as an open question for exact-match tests.
3. **Arithmetic.** +, -, *, / and comparisons are IEEE double operations built so that each produces the IEEE correctly rounded result (encodings/primitives.md section 1: add and subtract as two-term unit-weight dense rows, multiply by mul layer, divide by DIV with exact residual correction). Excel adds one quirk: when the last operation of a formula is + or - and the result is tiny relative to the operands (for example `=0.5-0.4-0.1` shows 0 while `=(0.5-0.4-0.1)*1` shows -2.78E-17), Excel snaps the result to 0. The plan is a CANCEL_SNAP block applied by the evaluator only at the top-level result of a formula whose final RPN token is + or -: if |r| < 2^-49 * max(|a|, |b|) then r = 0. The exact threshold is an open question to pin down with stage 1 tests.
4. **Display and text conversion.** Numbers are shown with at most 15 significant digits. The formatter finds the decimal exponent e by comparing |x| with a table of powers of ten (a step bank with exact or correctly rounded thresholds), scales to an integer in [10^14, 10^15) with one multiply or divide, rounds with ROUND, and extracts digits with DIGITS (encodings/primitives.md). Rounding in the scaling can move the 15th digit by one in rare halfway cases; open question.

Dates and times are numbers (serials). The 1900 leap-year quirk (serial 60 = 1900-02-29) is a property of the date functions and format stage, not of this encoding.

## 5. Booleans, errors and blank in arithmetic

Coercion is a network, not an encoding property, but the encoding is designed for it: TRUE and FALSE coerce to PAY directly (1, 0); blank coerces to 0 or "" and its PAY is already 0; an error propagates by copying (TAG, PAY) unchanged, which is a gated pass-through. Text to number coercion calls the number lexer on the string.

## 6. Multi-role words in this encoding

- **PAY** holds a double (TAG 1), a heap handle (TAG 2), a 0/1 flag (TAG 3), an error code (TAG 4) or a pointer (TAG 5 to 7). Roles are separated by TAG; every consumer gates PAY by the indicator of the tag it expects, so at most one role is live in any computation. Crosstalk tests: stage 1 coercion and propagation cases (tests/output/stage1/cases.yaml, groups coe and err) mix types in one formula.
- **TAG 0 with PAY 0** is both "blank" and "never written memory". This is deliberate: the two meanings agree for cells (an unwritten cell is blank). For other records that use the value layout (operand stack) the stack pointer, not the contents, decides validity, so a zero word is never read as meaningful there.
