# Checklist agent log

## 2026-11-06 Session start

- Read GOAL.md, docs/PARITY.md and docs/STAGES.md. Task: expand PARITY.md into checklist/CHECKLIST.csv (id,category,item,stage,status) plus checklist/README.md.
- Stage mapping chosen from STAGES.md: core formula language, values, errors and calculation go to stage 1; grid, editing, formula bar and basic screen layout to stage 2; math, logical, text, information functions and basic number formats to stage 3; lookup and reference, date and time and full cell formatting to stage 4; statistical, financial, engineering (and statistical compatibility functions) to stage 5; charts, sparklines and conditional formatting to stage 6; data features to stage 7; files to stage 8; VBA to stage 9; dynamic arrays, LAMBDA family, pivot tables, what-if tools, ribbon, dialogs, cube, web, add-in and remaining items to stage 10.

## 2026-11-06 Search 1: Microsoft alphabetical function list

- WebSearch "Excel functions (alphabetical) support.microsoft.com" found the official page (support.microsoft.com/office/excel-functions-alphabetical-b3944572-255d-4efb-bb96-c6d90033e188).
- Direct curl download was refused by the egress proxy (support.microsoft.com not in the allowed host list), so WebFetch was used instead. WebFetch read the full page in two passes (characters 0 to 100000, then the tail, which held only footer links).
- Result: 514 named entries (521 callable functions once paired byte variants are split), counting paired byte variants (FIND/FINDB, LEFT/LEFTB, LEN/LENB, MID/MIDB, REPLACE/REPLACEB, RIGHT/RIGHTB, SEARCH/SEARCHB) as one entry each. In the checklist these pairs are split into separate lines, since each is a distinct callable function.
- Anomalies on the Microsoft page, recorded and corrected in the checklist: VSTACK, WRAPCOLS and WRAPROWS are labeled "Look and reference" (typo, treated as Lookup and reference); NORMINV is labeled Statistical and NORM.INV labeled Compatibility, which is reversed relative to the rest of the reference (NORMINV is the legacy form). Checklist uses NORMINV=Compatibility, NORM.INV=Statistical. AGGREGATE, SEQUENCE, RANDARRAY are listed under Math and trigonometry by Microsoft; dynamic-array behavior puts SEQUENCE and RANDARRAY in stage 10.
- The page was summarized by the WebFetch extraction model, so a small chance of a dropped line exists. Spot checks against known functions (DATEDIF, ISOMITTED, TRIMRANGE, PERCENTOF, REGEX functions, GROUPBY, PIVOTBY, IMAGE) all present.

## 2026-11-06 Search 2: functions not in the alphabetical list

- WebSearch for COPILOT, PY, IMPORTCSV and IMPORTTEXT: COPILOT has its own support.microsoft.com page; IMPORTCSV and IMPORTTEXT appear in a Microsoft 365 Insider blog (techcommunity). PY (Python in Excel) is documented by Microsoft separately. None appear on the alphabetical page fetched today.
- Decision: include them as checklist items flagged in the item text as "not on alphabetical reference page; confirm" with stage 10. COPILOT and PY depend on external services; parity scope for them must be decided later (record in decisions).
- The by-category page was not fetched separately: the alphabetical page already gives a category per function, which is the same data.

## 2026-11-06 Non-function items

- Formula language, values and errors, calculation, formatting, data features, charts, UI, VBA and files were itemized from PARITY.md text plus general knowledge of Excel for Windows (Microsoft 365 current channel). These were not individually verified against Microsoft pages in this session. Ribbon groups and commands follow the default Microsoft 365 ribbon layout as known; command names may need a pass against a live Excel install before freezing. Gaps listed in checklist/README.md.
- No code was written. CSV and README were produced with file-editing tools. Counts in the README were obtained by a read-only shell count over the CSV (grep/cut/sort/uniq), no generated content.
