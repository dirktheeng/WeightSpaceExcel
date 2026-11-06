# Parity checklist

Parity means matching the behavior of current Microsoft Excel for Windows, as documented by Microsoft. At the start of the project this checklist is expanded into an itemized file (one line per function, feature and command) and frozen. Items are only added after that, never removed.

## 1. Functions

Every function in Microsoft's published Excel function reference, about 500 in total:

- Math and trigonometry
- Statistical (including distribution functions and their inverses)
- Text (including the `TEXT` function's format codes)
- Logical (`IF`, `IFS`, `SWITCH`, `AND`, `OR`, `XOR` and the rest)
- Lookup and reference (`VLOOKUP`, `XLOOKUP`, `INDEX`, `MATCH`, `OFFSET`, `INDIRECT` and the rest)
- Date and time
- Financial (including `IRR`, `XIRR`, `RATE` and other iterative solvers)
- Engineering (including complex numbers and base conversions)
- Information, database, cube (where applicable without external data), web and compatibility functions
- Dynamic array functions (`FILTER`, `SORT`, `UNIQUE`, `SEQUENCE` and the rest)
- `LAMBDA`, `LET` and the lambda helper functions (`MAP`, `REDUCE`, `SCAN` and the rest)

## 2. Formula language

Operators and precedence, unary minus and percent, absolute, relative and mixed references, A1 and R1C1 styles, ranges, intersection and union, named ranges and named formulas, cross-sheet and 3D references, structured table references, array constants, legacy array formulas, dynamic-array spilling and `#` spill references, implicit intersection (`@`), and Excel's type coercion rules.

## 3. Values and errors

Numbers (with Excel's 15-digit precision behavior), text, booleans, dates and times as serial numbers (including the 1900 leap-year quirk), blanks, and all error values (`#DIV/0!`, `#N/A`, `#VALUE!`, `#REF!`, `#NAME?`, `#NUM!`, `#NULL!`, `#SPILL!`, `#CALC!`, `#GETTING_DATA`) with Excel's propagation rules.

## 4. Workbook calculation

Multiple sheets, dependency-ordered recalculation, automatic and manual calculation modes, circular reference detection, iterative calculation with its settings, and volatile functions.

## 5. Formatting

Built-in and custom number format codes (sections, conditions, colors, dates, fractions, scientific), fonts, sizes, bold, italic, underline, strikethrough, colors, fills and patterns, borders, alignment, indent, rotation, wrapping, shrink to fit, merged cells, row heights and column widths, hide and unhide, freeze panes, cell styles, themes, and conditional formatting (all rule types, color scales, data bars, icon sets).

## 6. Data features

Sort (multi-key, custom lists), AutoFilter and advanced filter, tables, data validation (including drop-downs), find and replace, fill handle and autofill series, Flash Fill, copy, cut and paste, paste special, undo and redo, insert and delete of rows, columns and cells with reference adjustment, named range management, comments and notes, hyperlinks, pivot tables (create, layout, aggregation, refresh, grouping), Goal Seek, Data Tables, Scenario Manager and Solver.

## 7. Charts

All Excel chart types (column, bar, line, pie, doughnut, area, scatter, bubble, stock, surface, radar, combo, histogram, box and whisker, waterfall, treemap, sunburst, funnel), with axes, scaling, gridlines, titles, legends, data labels, trendlines, error bars, series and point formatting, and live updates when data changes. Sparklines (line, column, win/loss).

## 8. User interface

Parity for the interface includes appearance, not just function. The application should closely match the visual design and layout of Excel's GUI:

- **Layout:** the same arrangement and proportions of the title bar, Quick Access Toolbar, ribbon tabs and groups, name box, formula bar, column and row headers, grid, sheet tabs, scroll bars and status bar.
- **Visual style:** Excel's default theme colors, the Calibri/Aptos default font and sizes, gridline color, header shading, selection highlight and border, the fill handle, the active cell outline, and hover and pressed states.
- **Ribbon and controls:** the same command names, grouping, ordering, icon placement and sizes, drop-downs, galleries and split buttons, with icons drawn as original approximations of each command's look.
- **Dialogs and menus:** the same layout, tabs, fields, labels and button placement as Excel's dialogs (Format Cells, Insert Function and the rest) and context menus.
- **Behavior on screen:** matching cursor shapes, edit-mode appearance, marching ants for copy, spill range outlines, error indicators and comment markers.

Beyond this, the functional checklist covers grid drawing with scrolling, zoom and selection (single, range, multiple ranges), cell editing and edit mode, the formula bar and name box, autocomplete for functions, sheet tabs (add, rename, move, color), the ribbon with all tabs and commands, context menus, dialogs (Format Cells and the rest), keyboard shortcuts, the status bar with aggregates, and printing layout preview. Everything is drawn by networks into the framebuffer.

## 9. VBA

The VBA language (lexer, parser, interpreter, variable types, arrays, control flow, procedures and functions, classes, error handling with `On Error`), the VBA editor, the Excel object model (`Application`, `Workbook`, `Worksheet`, `Range`, `Cells`, `Chart` and the rest), events, user-defined functions callable from cells, UserForms, and macro recording.

## 10. Files

Read and write `.xlsx` and `.xlsm` (including ZIP decompression and compression, and parsing and writing the XML parts), `.csv` and `.txt` with import options, and preservation of everything above on round trip. All parsing and writing is done by networks on raw bytes.
