# Acceptance and measurement

## Conformance suite

Tests for each stage are written before the weights for that stage, and are not changed to fit results. Each item in the frozen parity checklist maps to one or more tests.

- **Calculation tests:** workbooks with inputs and expected values taken from Excel, including edge cases and error cases.
- **Rendering and UI tests:** scripted input event sequences paired with reference screenshots from Excel and checks on the expected memory state.
- **Chart tests:** data plus chart definitions, checked against reference renders for layout, scaling and labels.
- **VBA tests:** macros with expected effects on the workbook and expected output.
- **File tests:** round trips of real `.xlsx`, `.xlsm` and `.csv` files, checked for content, formatting and formula preservation.

## Test code

The suite is run by output tests and the repo is checked by compliance tests, both as defined in docs/RULES.md (rule 2). Output tests drive the networks through the harness and check outputs only; they never read weights. Compliance tests run automatically with the suite and fail the run if:

- any conventional code exists outside the frozen harness and the test directories;
- the harness differs from its frozen version without a matching decision record;
- any test code reads, parses or evaluates weight files beyond passing their paths to the harness;
- any test code is imported or called by the harness or networks during normal operation.

## Tolerances

- Integers, text, booleans and error values match exactly.
- Real numbers match to within 1 part in 10^12 relative, or a tighter stated tolerance per function where Excel's own behavior is exact.
- Rendering matches structurally (same cells, text, colors, layout and positions within a stated pixel tolerance). Pixel-identical font rendering is not required, but glyphs must be legible and correctly placed.
- GUI appearance is compared with reference screenshots of Excel at the same window size and zoom. Element positions and sizes (ribbon, formula bar, headers, grid, tabs, status bar, dialogs) match within a few pixels, colors match Excel's default theme within a small stated tolerance, and a side-by-side visual review confirms a close overall match.

## Audits

- **Repo audit:** the repo contains only the frozen harness, permitted test code, test data, documentation and weight files. No code produces, inspects or checks weights. The compliance tests automate this audit, and a manual review confirms the compliance tests themselves stay within their limits.
- **Harness audit:** every line of the harness is checked against docs/HARNESS.md. Every address, memory operation, routing choice, loop, halt, pixel, and interpretation of input or file bytes must come from a network output.
- **Documentation audit:** every weight block has a complete note, and every multi-role weight has its roles and non-interference argument.
- **Crosstalk check:** functions and features that share weights are tested together and in alternation to confirm no interference.

## Metrics

Recorded per function or feature and for the whole suite, at the end of each stage:

- Parameter count (hand-written and generated, reported separately)
- Network count
- Forward-pass steps per operation (per cell evaluation, per frame, per VBA statement and so on)
- Memory used

The aim is to keep these low and to track how they change across stages.

## Progress reporting

At the end of each stage, report the fraction of the parity checklist passing, by category, together with the metrics above and a short summary of what blocked any failing items.
