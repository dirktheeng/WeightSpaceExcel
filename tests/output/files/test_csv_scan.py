"""Output tests for csv_scan (id 448, weights/files/csv_scan.md).

Black box (docs/RULES.md rule 2): the scanner is loaded by path at id 448, every other
id is HALT_OK so the return to LR = 3 halts. Fixture bytes are hand-written CSV text
placed in the file transfer region exactly as io 2 leaves it (word 0 count, then one
byte per word). Expected token streams are stated by hand from RFC 4180 and Excel's
documented CSV behaviour: byte values, -1 field end, -2 row end, -3 end of data.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402

SCAN = os.path.join(ROOT, "weights", "files", "csv_scan.wt")
HALT = os.path.join(ROOT, "weights", "kernel", "halt_ok.wt")
XFER = 0x201000
OUTBUF = 0x0B0000
FE, RE, END = -1, -2, -3


def scan(data, garbage_after=0):
    h = Harness([HALT] * 448 + [SCAN])
    h.mem[XFER] = len(data)
    h.mem[XFER + 1:XFER + 1 + len(data)] = list(data)
    if garbage_after:  # stale bytes from an earlier, longer file must be ignored
        h.mem[XFER + 1 + len(data):XFER + 1 + len(data) + 4] = [65, 44, 34, 10]
    x = [0.0] * 65
    x[8] = 0          # PC 0 (entry)
    x[9] = 3          # LR = HALT_OK
    x[10] = 0         # LP
    x[11] = 0x100     # RSP, must pass through
    x[27] = OUTBUF    # P1 = token buffer
    x[30] = 77        # T0 garbage, scanner must reset it
    x[50] = 1234.5    # a local, must pass through
    trace = []
    h.trace = trace
    out = h.run(448, x, max_steps=10000)
    toks = []
    a = OUTBUF
    while True:
        toks.append(int(h.mem[a]))
        if h.mem[a] == END:
            break
        a += 1
    steps = sum(1 for t in trace if t.startswith("step"))
    return toks, h, steps


def b(s):
    return list(s.encode("ascii"))


def test_simple_rows():
    toks, h, steps = scan(b"a,b\r\n1,2\r\n")
    assert toks == [97, FE, 98, RE, 49, FE, 50, RE, END]


def test_lf_only_and_no_final_newline():
    toks, _, _ = scan(b"x,y\nz")
    assert toks == [120, FE, 121, RE, 122, END]


def test_quoted_comma_newline_and_doubled_quote():
    # "a,b","he said ""hi""","l1<CRLF>l2"
    toks, _, _ = scan(b'"a,b","he said ""hi""","l1\r\nl2"\r\n')
    expect = [97, 44, 98, FE] + b('he said "hi"') + [FE, 108, 49, 13, 10, 108, 50, RE, END]
    assert toks == expect


def test_empty_fields_and_empty_quoted():
    toks, _, _ = scan(b',"",\n')
    # three empty fields: two separators, then the row end
    assert toks == [FE, FE, RE, END]


def test_quote_inside_unquoted_field_is_literal():
    # Excel keeps a quote that is not at the start of a field
    toks, _, _ = scan(b'ab"c,d\n')
    assert toks == [97, 98, 34, 99, FE, 100, RE, END]


def test_text_after_closing_quote_is_appended():
    # Excel reads "ab"cd as abcd
    toks, _, _ = scan(b'"ab"cd,e\n')
    assert toks == [97, 98, 99, 100, FE, 101, RE, END]


def test_lone_cr_ends_row_and_blank_line():
    toks, _, _ = scan(b"a\rb\r\n\r\nc")
    assert toks == [97, RE, 98, RE, RE, 99, END]


def test_empty_file_and_stale_bytes():
    toks, _, _ = scan(b"", garbage_after=1)
    assert toks == [END]
    toks, _, _ = scan(b"q", garbage_after=1)
    assert toks == [113, END]


def test_registers_and_return():
    data = b"ab,c\n"
    toks, h, steps = scan(data)
    assert toks == [97, 98, FE, 99, RE, END]


def test_return_state():
    h = Harness([HALT] * 448 + [SCAN])
    data = b"1,2\n"
    h.mem[XFER] = len(data)
    h.mem[XFER + 1:XFER + 1 + len(data)] = list(data)
    x = [0.0] * 65
    x[9], x[10], x[11], x[27], x[50] = 3, 0, 0x100, OUTBUF, 1234.5
    trace = []
    h.trace = trace
    h.run(448, x, max_steps=1000)
    # the step whose next is 3 is the scanner's last step: inspect its output words
    last = [t for t in trace if t.startswith("step") and " net 448 " in t][-1]
    import numpy as np
    words = eval(last.split(" out ")[1], {"np": np})
    assert words[0] == 3 and words[7] == 0          # next = LR, PC = LP
    assert words[10] == 0x100 and words[49] == 1234.5  # RSP and L9 unchanged
    assert words[12] == 0                            # STATUS ok
    assert words[26] == OUTBUF + 5                   # P1 past 1 FE 2 RE END (5 tokens)
    # steps: entry 2, then per byte 1 (no emit) or 2 (emit); 4 emitting bytes, then 1 for end
    assert sum(1 for t in trace if t.startswith("step")) == 2 + 4 * 2 + 1 + 1
