# Stage 1 tests agent log

## 2026-11-06

- Read GOAL.md, docs/RULES.md, docs/ACCEPTANCE.md, docs/STAGES.md. harness/ is empty, so the runner assumes `harness.run_workbook(cells, edits=None) -> dict` and must be matched to the real API once it exists.
- Decision: YAML case format. Values: YAML number, bool, quoted text, `{error: "#X"}`, `{blank: true}`. Extra keys `circular`, `rejected`, `edits`, `requires`, `confidence`. Settings assumed: en-US, automatic calc, iteration off.
- Wrote 287 cases in tests/output/stage1/cases.yaml by hand from Excel documented behavior (operator precedence table: `:` space `,`, negation, %, ^, * /, + -, &, comparisons). No code computed any expected value.
- Self-correction while writing: pre25 (`=-2^2%`) first drafted with a numeric value; corrected to #NUM! because negation and % both bind before ^, giving (-2)^0.02.
- Range cases that need SUM are tagged `requires: [SUM]` since functions are Stage 3. Intersection cases (rng09 to rng11) need no function.
- Wrote tests/output/test_stage1.py: loads cases, calls harness, compares with rel tol 1e-12 and exact match for text, bools, errors. Never touches weights/. All tests xfail while harness lacks run_workbook. Ran it: 287 xfailed.
- 28 cases marked medium or low confidence; not confirmed by web search in this pass. Candidates for confirmation in real Excel: ref12, ari15, cat17, coe20, coe22, cir10, cir12 (low).
