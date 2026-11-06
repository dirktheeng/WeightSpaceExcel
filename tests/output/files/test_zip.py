"""Output tests for the ZIP reader (489..493, 495, 497) and writer (494, 496, 507..511), weights/files/zip.md.
Black box. The hand-built ZIP is packed by struct from hand-stated field values; its CRC fields are published
check values (CRC-32 of "123456789" = 0xCBF43926, of "a" = 0xE8B7BE43). Writer tests are round trips through
the reader plus hand-stated header bytes."""
import struct

from zipnets import harness, run, state, zip_read, zip_write


def lh(method, crc, cs, us, name):
    return b"PK\x03\x04" + struct.pack("<HHHHHIIIHH", 20, 0, method, 0, 0x21, crc, cs, us, len(name), 0) + name


def cd(method, crc, cs, us, name, off):
    return (b"PK\x01\x02" + struct.pack("<HHHHHHIIIHHHHHII", 20, 20, 0, method, 0, 0x21, crc, cs, us,
                                        len(name), 0, 0, 0, 0, 0, off) + name)


def eocd(n, size, off, comment=b""):
    return b"PK\x05\x06" + struct.pack("<HHHHIIH", 0, 0, n, n, size, off, len(comment)) + comment


def hand_zip(comment=b"hey", crc2=0xE8B7BE43):
    e1 = lh(0, 0xCBF43926, 9, 9, b"x/1") + b"123456789"
    e2 = lh(8, crc2, 3, 1, b"xl/a") + bytes([0x4B, 4, 0])
    c = cd(0, 0xCBF43926, 9, 9, b"x/1", 0) + cd(8, crc2, 3, 1, b"xl/a", len(e1))
    return e1 + e2 + c + eocd(2, len(c), len(e1) + len(e2), comment)


def ready():
    h = harness()
    run(h, 463, state())
    return h


def test_read_stored_and_deflated_parts():
    z = hand_zip()
    assert zip_read(ready(), z, b"x/1")[:2] == (b"123456789", 0)
    assert zip_read(ready(), z, b"xl/a")[:2] == (b"a", 0)


def test_read_without_comment():
    assert zip_read(ready(), hand_zip(b""), b"xl/a")[:2] == (b"a", 0)


def test_not_found_and_crc_mismatch():
    z = hand_zip()
    assert zip_read(ready(), z, b"xl/b")[1] == 1
    assert zip_read(ready(), z, b"x/12")[1] == 1
    assert zip_read(ready(), hand_zip(crc2=0xE8B7BE42), b"xl/a")[1] == 3


def test_not_a_zip():
    assert zip_read(ready(), b"\x00" * 40, b"a")[1] == 2


SHEET = b'<worksheet><sheetData><row r="1"><c r="A1"><v>1</v></c></row></sheetData></worksheet>'


def test_write_then_read():
    h = ready()
    parts = [(b"[Content_Types].xml", b"<Types/>"), (b"xl/worksheets/sheet1.xml", SHEET * 3)]
    z, o, _ = zip_write(h, parts)
    assert (o[12], o[10]) == (0, 0x100)  # STATUS 0, RSP balanced
    assert z[:4] == b"PK\x03\x04" and z[8] == 8  # local header, method 8
    assert z[-22:-18] == b"PK\x05\x06" and z[-14] == 2 and z[-12] == 2  # EOCD, 2 entries
    for name, data in parts:
        assert zip_read(ready(), z, name)[:2] == (data, 0)


def test_write_locals_restored():
    h = ready()
    x = state(P0=0, N0=1)
    for i in range(40, 48):
        x[i + 1] = 1000 + i
    from zipnets import FS, TABLE, put
    put(h, FS + 0x2000, b"a.txt" + b"hello")
    h.mem[TABLE:TABLE + 8] = [FS + 0x2000, 5, FS + 0x2005, 5, 0, 0, 0, 0]
    x[26], x[27], x[28], x[29], x[11] = TABLE, 0x201001, 1, FS + 0x8000, 0x100
    o, _ = run(h, 507, x)
    assert [o[i] for i in range(40, 48)] == [1000 + i for i in range(40, 48)]
