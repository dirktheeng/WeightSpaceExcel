# Stages

Each stage has deliverables and exit criteria. A stage ends when its exit criteria pass and its progress report (docs/ACCEPTANCE.md) is written. Earlier stages' tests must keep passing in every later stage.

## Stage 0: Foundations

- Deliverables: itemized and frozen parity checklist; harness written to docs/HARNESS.md and frozen; work log and documentation structure set up; first test sets written.
- Exit: harness audit passes; a trivial hand-written network (for example, add two numbers and halt) runs end to end.

## Stage 1: Core engine

- Deliverables: memory layout, latent encodings for values, types and addresses; formula lexer and parser; references and ranges; arithmetic and comparison; error values; dependency tracking and recalculation; circular reference detection.
- Exit: calculation tests for the core formula language pass.

## Stage 2: Minimal UI

- Deliverables: framebuffer layout, glyph encoding and rendering, grid drawing, scrolling, selection, cell editing, formula bar.
- Exit: a user can type values and formulas into cells and see results drawn on screen.

## Stage 3: Math, logical, text functions and basic number formats

- Exit: all functions in these categories pass; common built-in number formats display correctly.

## Stage 4: Lookup and reference, date and time, full cell formatting

- Exit: functions in these categories pass; custom number formats, fonts, fills, borders and alignment render correctly.

## Stage 5: Statistical, financial and engineering functions

- Exit: functions in these categories pass within tolerance, including iterative solvers and distribution functions.

## Stage 6: Charts and conditional formatting

- Exit: all chart types and conditional formatting rules pass their rendering tests and update live.

## Stage 7: Data features

- Exit: sort, filter, tables, validation, find and replace, autofill, copy and paste, undo and redo, insert and delete pass.

## Stage 8: File I/O

- Exit: CSV import and export, then `.xlsx` and `.xlsm` read and write, pass round-trip tests.

## Stage 9: VBA

- Exit: VBA language tests, object model tests, events and UDFs pass.

## Stage 10: Long tail

- Deliverables: dynamic arrays and spilling, `LAMBDA` and helpers, pivot tables, what-if tools, ribbon, dialogs, remaining UI, remaining functions and features.
- Exit: the full parity checklist passes.

## Ordering notes

Stages may overlap or be reordered when a shared component makes it sensible, with the reason recorded in the work log. The minimal UI comes early so every later stage can be checked visually, and its rendering networks are reused by formatting, charts and dialogs.
