# Parity checklist (itemized)

CHECKLIST.csv is the itemized form of docs/PARITY.md. Columns: id, category, item, stage, status. Every item starts as `todo`. Once frozen, items may be added but never removed. Stages follow docs/STAGES.md. Built 2026-11-06; the build log is in log/checklist-agent.md.

Total items: 1220.

## Counts by category

| Category | Items |
|---|---|
| Functions (all subcategories) | 532 |
| Formula language | 65 |
| Values and errors | 29 |
| Calculation | 25 |
| Formatting | 80 |
| Data features | 91 |
| Charts and sparklines | 74 |
| User interface (all subcategories) | 186 |
| VBA (language, editor, events, general) | 67 |
| VBA object model | 33 |
| Files | 38 |

Function subcategories: Statistical 111, Math and trigonometry 80, Text 57 (50 functions plus 7 TEXT format code items), Financial 55, Engineering 54, Lookup and reference 40, Compatibility 40, Date and time 25, Information 22, Logical 19, Database 12, Cube 7, Add-in and Automation 3, Web 3, Unconfirmed 4.

UI subcategories: Ribbon group 50, Dialog 43, Layout 16, Ribbon tab 15, Status bar 13, Grid 11, Visual style 9, Keyboard 9, Screen behavior 7, Print 6, Context menu 5, Objects 2.

## Counts by stage

| Stage | Items |
|---|---|
| 1 Core engine | 76 |
| 2 Minimal UI | 55 |
| 3 Math, logical, text, basic formats | 176 |
| 4 Lookup, date, full formatting | 113 |
| 5 Statistical, financial, engineering | 258 |
| 6 Charts and conditional formatting | 90 |
| 7 Data features | 89 |
| 8 File I/O | 37 |
| 9 VBA | 102 |
| 10 Long tail | 224 |

## Sources and caveats

- Functions: 521 come from Microsoft's "Excel functions (alphabetical)" page as read on 2026-11-06 (514 entries; FIND/FINDB and the six other byte-variant pairs are split into separate items). Two labeling slips on that page were corrected (VSTACK, WRAPCOLS and WRAPROWS shown as "Look and reference"; NORMINV and NORM.INV categories swapped).
- Four functions (COPILOT, PY, IMPORTCSV, IMPORTTEXT) are not on the alphabetical page and are filed as "Function: Unconfirmed" pending a scope decision.
- Dynamic array functions, LAMBDA and its helpers, cube, web and add-in functions, GETPIVOTDATA, IMAGE and the database functions are placed in stage 10.
- Non-function items were itemized from PARITY.md and general knowledge of Excel for Windows (Microsoft 365). They were not each verified against a Microsoft page. Ribbon commands are grouped one line per group; a later pass against a live Excel may split groups into individual commands (adding items, as the freeze rule allows).
- Items marked "scope to decide" (xlsb, xls, encryption, Declare APIs, COPILOT, PY) need a decision record before freezing.
