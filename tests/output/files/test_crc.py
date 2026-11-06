"""Output tests for x32 (462), crc (461) and crcg (463); weights/files/crc.md, x32.md.
Black box. Expected values stated by hand: XORs of simple bit patterns, published CRC-32 table entries
(T[1] 0x77073096, T[2] 0xEE0E612C, T[3] 0x990951BA, T[255] 0x2D02EF8D) and published check values
(CRC-32 of "123456789" is 0xCBF43926, of "a" 0xE8B7BE43, of the empty string 0)."""
from zipnets import FS, harness, run, state


def x32(u, v, t2=0):
    h = harness()
    x = state(T1=v, T2=t2, P0=100)
    x[0] = u
    o, _ = run(h, 462, x)
    return o[30]


def test_x32():
    assert x32(5, 3) == 6
    assert x32(255, 15) == 240
    assert x32(0, 4294967295) == 4294967295
    assert x32(2**31, 2**31 + 1) == 1
    assert x32(0xAAAAAAAA, 0x55555555) == 0xFFFFFFFF
    assert x32(0, 7, t2=7) == 0  # U = x0 + T2


def table():
    h = harness(trace=True)
    o, steps = run(h, 463, state(T3=777, T4=-5))
    return h, steps


def test_table_entries_and_steps():
    h, steps = table()
    t = 0x3BFF00
    assert [h.mem[t + i] for i in (0, 1, 2, 3, 255)] == [0, 0x77073096, 0xEE0E612C, 0x990951BA, 0x2D02EF8D]
    assert steps == 3 * 255 + 2


def crc(h, data, start=0):
    h.mem[FS:FS + len(data)] = list(data)
    h.trace = []
    o, steps = run(h, 461, state(P0=FS, N0=FS + len(data), A=start, T1=12345))
    return int(o[14]), int(o[12]), steps


def test_check_values():
    h, _ = table()
    assert crc(h, b"123456789")[:2] == (0xCBF43926, 0)
    assert crc(h, b"a")[0] == 0xE8B7BE43
    assert crc(h, b"")[0] == 0


def test_chunked_and_steps():
    h, _ = table()
    a = crc(h, b"1234")[0]
    h.mem[FS:FS + 5] = list(b"56789")
    o, _ = run(h, 461, state(P0=FS, N0=FS + 5, A=a))
    assert int(o[14]) == 0xCBF43926
    _, _, steps = crc(h, b"123456789")
    assert steps == 2 * 9 + 2  # 2 steps per byte
