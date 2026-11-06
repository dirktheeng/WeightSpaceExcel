# tests-345-agent progress log

## 2026-11-06
- Read AGENT_BRIEF.md, Stage 1 suite (tests/output/stage1/cases.yaml, tests/output/test_stage1.py), blackbox.py, CHECKLIST.csv.
- Scope: CHECKLIST items with stage 3 (176), 4 (113), 5 (258). Functions only get function cases; TEXT format codes and built-in/custom number formats get display cases (formats.yaml). Non-number formatting items (fonts, fills, borders, dialogs) are out of scope for this agent (no display observation in blackbox.py yet).
- support.microsoft.com is blocked to curl via proxy but WebFetch works. Fetched the alphabetical function index to get canonical page URLs: pattern https://support.microsoft.com/en-us/excel/functions/<name, dots as dashes>-function (IS functions share /excel/is-functions; FORECAST.* share /excel/forecasting-functions-reference). Each case group cites its page in a YAML comment.
- Decision: per-case `tol` (relative) because Microsoft examples print rounded results (often 7 to 10 digits). Default stays 1e-12 per ACCEPTANCE.md.
- Decision: zero-arity functions (PI, TRUE, FALSE, NA, RAND, NOW, TODAY) get their error case as an entry rejected for too many arguments.
- Decision: volatile functions are tested by properties (=AND(RAND()>=0,RAND()<1)), and require AND.
- Expected values are typed by hand from documented examples and documented rules; none computed by code. Cases I recalled but could not re-confirm on the page this session carry confidence: medium; doubtful behaviors carry confidence: low.
- 21:23 Wrote stage3 cases_math/text/logic_info + formats, stage4 cases_date/lookup + formats, stage5 cases_stat. Hand-check fixes: TEXTAFTER instance cases need match_mode 1 (only one lowercase red); LINEST const=FALSE slope is 67/29; ETS.STAT type 8 is step size.
- Wrote stage5 cases_fin, cases_eng, cases_compat. Re-read live pages for DISC (result 0.001038, not my first recollection) and ODDFYIELD (7.72%).
- Hand fixes: ACCRINTM basis 0 is 74/360 (30/360 count 4/1 to 6/15), not 75.
- YAML gotcha: requires: [TRUE] parsed as boolean; quoted as "TRUE"/"FALSE".
- Validation (bookkeeping script, no expected values): all files load, no duplicate ids, every stage 3/4/5 function has >= 3 cases. pytest: 1938 collected, all skipped (no checklist item done yet).
- Totals: stage3 692 function cases + 62 format cases; stage4 240 + 72; stage5 871. Low confidence: 28 cases (listed in report).
- 21:40 Compliance fix: removed glob/os/open from stage3/runner_common.py (now merge() of parsed docs); test_stage3/4/5.py open each YAML via module-level static path constants. Added blackbox settings_events/format_events/width_events/display (DISPLAY_TABLE None until a display-string location is documented). WebFetch re-verification blocked: permission requests unanswered (PROVENANCE_REQUIRED); no expected values changed.
