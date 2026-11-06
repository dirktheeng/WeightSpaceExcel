"""Output tests for xml_tok (id 460, weights/files/xml_tok.md). Black box, loaded by path at id 460,
every other id HALT_OK. Fixture bytes are hand-written XML; expected tokens stated by hand:
byte, -1000 - b start tag (first name byte b), -2000 - b attribute, -3 value start, -4 '>',
-5 '/>', -6 end tag open, -9 end.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402

TOK = os.path.join(ROOT, "weights", "files", "xml_tok.wt")
HALT = os.path.join(ROOT, "weights", "kernel", "halt_ok.wt")
SRC, OUT = 0x3B0000, 0x3B8000


def tok(data):
    h = Harness([HALT] * 460 + [TOK])
    h.mem[SRC:SRC + len(data)] = list(data)
    x = [0.0] * 65
    x[9], x[11], x[26], x[27], x[28], x[30] = 3, 0x100, SRC, OUT, SRC + len(data), 55
    h.run(460, x, max_steps=10000)
    toks, a = [], OUT
    while True:
        toks.append(int(h.mem[a]))
        if h.mem[a] == -9:
            return toks
        a += 1


def b(s):
    return list(s.encode())


def test_element_with_attributes_and_text():
    t = tok(b'<c r="A1" t=\'s\'><v>12</v></c>')
    assert t == ([-1000 - 99, -2000 - 114, -3] + b("A1") + [-2000 - 116, -3, 115, -4]
                 + [-1000 - 118, -4] + b("12") + [-6, 118, -4, -6, 99, -4, -9])


def test_declaration_skipped_and_empty_tag():
    t = tok(b'<?xml version="1.0"?>\n<row r = "1"/>')
    assert t == [10, -1000 - 114, 111, 119, -2000 - 114, -3, 49, -5, -9]


def test_comment_and_whitespace_in_end_tag():
    t = tok(b"a<!-- x --><b></b >")
    assert t == [97, -1000 - 98, -4, -6, 98, -4, -9]


def test_empty_input():
    assert tok(b"") == [-9]
