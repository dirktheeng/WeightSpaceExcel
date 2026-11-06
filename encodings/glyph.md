# Encoding: GLYPH (characters, text, framebuffer and glyph rendering), first plan

Status: first plan, stage 1 for character encoding, stage 2 for rendering. Decision records: log/WORKLOG.md "2026-11-06 Stage 1: shared encodings design", decisions D9 (packed UTF-16 text), D17 (framebuffer layout), D18 (bitmap glyph ROMs). Related: encodings/memory-map.md (text heap, UI_STATE), encodings/primitives.md (ROM, ONEHOT, DISPATCH, UNPACK3), encodings/control.md (ids 128 to 191).

## 1. Character encoding

A character is one **UTF-16 code unit**, an integer 0 to 65535, the same unit Excel uses for text, LEN and MID. Characters outside the Basic Multilingual Plane are two units (a surrogate pair), exactly as Excel counts them. Strings are stored three units per word in the text heap (encodings/memory-map.md section 9) and unpacked with UNPACK3.

Character properties are ROMs over the code (encodings/primitives.md ROM), built per 128-unit page so a ROM only covers pages that matter:

| ROM | Output | Used by |
|---|---|---|
| CLASS | lexer class: 0 other, 1 digit, 2 letter, 3 underscore or backslash, 4 period, 5 operator char, 6 quote, 7 apostrophe, 8 paren or brace, 9 comma or semicolon, 10 space, 11 dollar, 12 hash, 13 exclamation, 14 at, 15 colon, 16 bracket | formula lexer, VBA lexer |
| FOLD | case-folded unit (A to Z to a to z, and Latin-1 and Latin Extended pairs) | case-insensitive comparison (Excel's =, MATCH, VLOOKUP), UPPER, LOWER, PROPER |
| ADV | advance width in pixels for each font variant (section 4) | text layout, alignment, overflow into neighbouring cells, autofit |

Pages planned for stage 2: 0x00 (Basic Latin), 0x01 (Latin-1 Supplement), 0x02 and 0x03 (Latin Extended-A), 0x40 (General Punctuation, for the en and em dash characters, curly quotes and ellipsis that Excel text can contain), 0x41 (currency symbols, for the euro sign). Any other code unit renders as a box (the missing glyph) and has class 2 if it is in a letter block (open question Q-G3).

**Non-interference.** The code unit is a single integer word with one meaning; all properties are derived from it through separate ROMs, so they share the ONEHOT front end (the code's page and position) but write disjoint output words.

## 2. External encodings

Raw bytes from files and raw keyboard events are not characters until a network decodes them. UTF-8 (xlsx XML parts), UTF-16 and Windows-1252 (legacy CSV) decoders and encoders are file-stage networks; the Windows-1252 to UTF-16 map for bytes 0x80 to 0x9F is a 32-entry ROM. Keyboard events carry the produced UTF-16 unit and the virtual key code in one word (encodings/io.md, D19; Q-G4 resolved), so typed text needs no key-to-character network; shortcuts match on VK and MODS.

## 3. Framebuffer layout (D17)

- Size 1280 x 800 pixels, row-major: pixel (x, y) at address 0x100000 + 1280 y + x (exact, R4). 1,024,000 words of the 1,048,576-word region; the remaining 24,576 words are never written. The window size must match the reference screenshots (open question Q-G1: confirm 1280 x 800 with the UI test design).
- Pixel word = R * 65536 + G * 256 + B, each channel 0 to 255. Integer, exact. Excel's default colours: white 0xFFFFFF, gridline 0xE1E1E1 (to be confirmed from reference screenshots), black text 0x000000.
- Networks draw by writing words, one pixel per step, then request io 1 to present the frame. Because every pixel costs one step, rendering is incremental: a dirty rectangle list in UI_STATE records what changed, and only those rectangles are redrawn. A full redraw is about 1 million steps (open question Q-G2: speed of a full frame).

Colour blending (anti-aliased text, selection tint) unpacks channels with MOD2K at 2^8 and 2^16, blends each channel with an R5 row followed by ROUND (a tolerance of one level is acceptable because rendering is compared structurally, docs/ACCEPTANCE.md), and repacks with one R4 row.

## 4. Glyph storage (D18)

Glyphs are hand-designed bitmaps held in weights as ROMs (rule 1: original approximations of each character's look; no font file is read).

- **Glyph cell.** Height H rows (H = 15 for the 11 pt cell font at 100 percent zoom, to be fixed against reference screenshots), width up to 16 pixels. Each glyph row is one integer: bit j set means pixel column j is ink. With 2-bit coverage (planned refinement) a row is 16 two-bit levels, a 32-bit integer; both are exact.
- **Page network.** One network per (font variant, page): a ROM whose input is the code's position in the page (code - 128 page, ONEHOT over 128 values, 256 step units) and the glyph row index y (ONEHOT over H values), producing that row's integer, plus ADV for that code. Weights: about 128 x H entries per variant and page, around 2,000 nonzero values.
- **Variants.** Cell font regular, bold, italic, bold italic; UI font (ribbon, dialogs, headers) regular and bold. Other sizes and zoom levels sample a base variant at scaled coordinates (x' = FLOOR(x s), y' = FLOOR(y s)); quality of this scaling is open question Q-G5.
- **Dispatch.** The text drawing network computes page = FLOOR(code / 128) and routes to the page network by DISPATCH (next = page network base + page slot, with a small ROM mapping supported pages to slots and everything else to the missing-glyph network). The page network returns by the link convention (encodings/control.md section 4).

## 5. Drawing a text run

Inputs: string handle, start position, clip rectangle, origin (x, y), font variant, colour. Loop (one step per memory operation):

1. Read the next heap word when the current one is used up (one read every three characters).
2. For each character: call the page network for each glyph row needed, receiving the row integer and the advance.
3. Within a row, find the next ink pixel in one forward pass (a priority encoder: a GE_K bank on the row integer's bits after MOD2K splitting), write that pixel, clear its bit, repeat. Steps are spent only on ink pixels, about a third of the glyph area for typical text.
4. Advance x by ADV; stop at the clip edge. Background pixels are written by the cell fill pass before text, so the text pass never writes background.

Number formatting, alignment and overflow decide the start position and origin before this loop runs (stage 2 to 4).

## 6. Multi-role words

- **Pixel words** hold one packed colour; channels occupy disjoint bit ranges (0 to 7, 8 to 15, 16 to 23) and are recovered exactly with MOD2K.
- **Glyph row integers** carry 16 one-bit (or two-bit) fields in disjoint ranges; the priority encoder reads them after splitting, and bit clearing subtracts an exact power of two, so fields never mix.
- **The code unit** is shared by the lexer (CLASS), comparison (FOLD) and rendering (glyph ROM, ADV); each use is a separate ROM output, as argued in section 1.
