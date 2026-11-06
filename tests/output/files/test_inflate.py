"""Output tests for inflate (ids 464..488, weights/files/inflate.md). Black box.
Fixtures are DEFLATE streams worked out by hand bit by bit (log/files-agent.md session 2); expected outputs are
the stated plain texts. One test feeds streams that zlib made from a hand-written text: zlib only makes the
input, the expected output is the stated text."""
import zlib

from zipnets import inflate


def test_stored():
    assert inflate(bytes([1, 2, 0, 0xFD, 0xFF, 0x68, 0x69]))[:2] == (b"hi", 0)


def test_stored_two_blocks():
    assert inflate(bytes([0, 1, 0, 0xFE, 0xFF, 0x41, 1, 0, 0, 0xFF, 0xFF]))[:2] == (b"A", 0)


def test_fixed_literal():
    assert inflate(bytes([0x4B, 0x04, 0x00]))[:2] == (b"a", 0)


def test_fixed_match():
    # header 1,1,0; a b c as 8-bit codes 0x30 + c; length 6 = symbol 260 (0000100); distance 3 = code 2 (00010)
    assert inflate(bytes([0x4B, 0x4C, 0x4A, 0x86, 0x20, 0x00]))[:2] == (b"abcabcabc", 0)


def test_dynamic_hand_built():
    # HLIT 257, HDIST 1, HCLEN 18; code length codes 1 and 18 have length 1; lengths 18+86, 1, 18+127, 18+9, 1, 1
    data = bytes([0x05, 0xC0, 0x81, 0, 0, 0, 0, 0, 0x90, 0x56, 0xFF, 0x13, 0x40])
    assert inflate(data)[:2] == (b"aaaa", 0)


def test_bad_block_type():
    assert inflate(bytes([0x07]))[1] == 2  # BTYPE 3


TEXT = (b'<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>42</v></c></row>'
        b'<row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>43</v></c></row>') * 3


def test_zlib_made_streams():
    for level in (1, 9):
        c = zlib.compressobj(level, zlib.DEFLATED, -15)
        d = c.compress(TEXT) + c.flush()
        out, status, steps = inflate(d, trace=True)
        assert (out, status) == (TEXT, 0)
        assert steps < 4500
