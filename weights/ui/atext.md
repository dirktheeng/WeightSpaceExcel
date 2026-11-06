# Weight block notes: weights/ui/atx0.wt, atx1.wt (ids 138, 139, aligned text)

Hand-written. Log: log/ui-agent.md; decision U3.
**Computes.** Draws the buffer AS2 inside a box: atx0 calls glyph in measure mode (pen 0, so the returned T0 is the width w). atx1 sets pen = X (align 0), X + relu(Wb - w) (align 1), or X + floor(relu(Wb - w)/2) (align 2), then calls glyph to draw and return directly to (N0, N1).
**Args.** B.TAG X, B.PAY Wb, C.TAG align, C.PAY top, AR2 colour, AC2 clip, AS2 buffer, N0/N1 return link. These words are not touched by glyph, so they survive the measure call.
**Derivation.** floor(D/2) = ROUND(D/2 - 1/4) for integer D. The align one-hot is [al >= 1] - [al >= 2] and [al >= 2]. MUX_INT M = 2^20.
**Parameters.** atx0 31, atx1 175. **Steps.** 2 + measure (chars + 2) + draw. **Tests.** test_cell_text_alignment, test_headers.
