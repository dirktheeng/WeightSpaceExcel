"""Output tests for deflate (ids 498..506, weights/files/deflate.md). Black box. Expected streams are the
hand-derived ones of test_inflate.py; other checks are round trips through inflate."""
from zipnets import deflate, inflate


def test_stored():
    assert deflate(b"hi", 0)[:2] == (bytes([1, 2, 0, 0xFD, 0xFF, 0x68, 0x69]), 0)


def test_fixed_hand_values():
    assert deflate(b"a")[:2] == (bytes([0x4B, 0x04, 0x00]), 0)
    assert deflate(b"abcabcabc")[:2] == (bytes([0x4B, 0x4C, 0x4A, 0x86, 0x20, 0x00]), 0)


def test_round_trips():
    for t in [b"", b"a" * 278, bytes(range(256)), b'<c r="A1"><v>12</v></c>' * 20, b"xy" * 300 + b"z"]:
        for mode in (0, 1):
            c, s, _ = deflate(t, mode)
            assert s == 0
            assert inflate(c)[:2] == (t, 0)


def test_compresses_repeats():
    c, _, _ = deflate(b"a" * 278)
    assert len(c) < 12
