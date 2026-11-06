"""Black-box driver helpers for output tests (docs/RULES.md rule 2, encodings/io.md).

Encodes input events, boots the manifest through the harness, and decodes raw memory
words by the documented layout. Never opens weight files: manifest paths are passed
to the harness only. Never reads WEIGHT_STAGING or any harness network object.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MANIFEST = os.path.join(ROOT, "weights", "MANIFEST.txt")
CHECKLIST = os.path.join(ROOT, "checklist", "CHECKLIST.csv")
sys.path.insert(0, ROOT)
from harness.harness import Harness  # noqa: E402

# ---- encodings/io.md section 1
KEY_DOWN, KEY_UP = 1, 2
SHIFT, CTRL = 1, 2
VK_ENTER, VK_DELETE, VK_PACKET, VK_G = 0x0D, 0x2E, 0xE7, 0x47
# en-US layout: character -> (VK, shift held)
_PUNCT = {
    " ": (0x20, 0), "0": (0x30, 0), "1": (0x31, 0), "2": (0x32, 0), "3": (0x33, 0),
    "4": (0x34, 0), "5": (0x35, 0), "6": (0x36, 0), "7": (0x37, 0), "8": (0x38, 0),
    "9": (0x39, 0), ")": (0x30, 1), "!": (0x31, 1), "@": (0x32, 1), "#": (0x33, 1),
    "$": (0x34, 1), "%": (0x35, 1), "^": (0x36, 1), "&": (0x37, 1), "*": (0x38, 1),
    "(": (0x39, 1), ";": (0xBA, 0), ":": (0xBA, 1), "=": (0xBB, 0), "+": (0xBB, 1),
    ",": (0xBC, 0), "<": (0xBC, 1), "-": (0xBD, 0), "_": (0xBD, 1), ".": (0xBE, 0),
    ">": (0xBE, 1), "/": (0xBF, 0), "?": (0xBF, 1), "`": (0xC0, 0), "~": (0xC0, 1),
    "[": (0xDB, 0), "{": (0xDB, 1), "\\": (0xDC, 0), "|": (0xDC, 1), "]": (0xDD, 0),
    "}": (0xDD, 1), "'": (0xDE, 0), "\"": (0xDE, 1),
}


def event(kind, mods, unit, vk):
    return float(kind * 2**48 + mods * 2**40 + unit + 2**16 * vk)


def press(vk, mods=0, unit=0):
    return [event(KEY_DOWN, mods, unit, vk), event(KEY_UP, mods, 0, vk)]


def type_text(text):
    out = []
    units = text.encode("utf-16-le")
    for i in range(0, len(units), 2):
        u = units[i] + 256 * units[i + 1]
        c = chr(u)
        if "a" <= c <= "z":
            out += press(ord(c.upper()), 0, u)
        elif "A" <= c <= "Z":
            out += press(u, SHIFT, u)
        elif c in _PUNCT:
            vk, sh = _PUNCT[c]
            out += press(vk, SHIFT * sh, u)
        else:
            out += press(VK_PACKET, 0, u)
    return out


def goto(addr):
    return press(VK_G, CTRL) + type_text(addr) + press(VK_ENTER)


def enter(addr, text):
    if text == "":
        return goto(addr) + press(VK_DELETE)
    return goto(addr) + type_text(text) + press(VK_ENTER)


def script(cells, edits=None):
    ev = []
    for a, t in cells.items():
        ev += enter(a, str(t))
    for e in edits or []:
        for a, t in e.items():
            ev += enter(a, str(t))
    return ev


# ---- running
TRAP_ID = 1  # encodings/control.md section 5
N_FIXED = 512  # hand-written id space; generated ids start here (NET_NEXT)


def manifest_paths():
    """Lines "ID PATH". Builds the id-ordered path list; gaps get the TRAP path.
    Paths only; the listed weight files are never opened here."""
    if not os.path.exists(MANIFEST):
        return None
    by_id = {}
    with open(MANIFEST) as f:
        for n, ln in enumerate(f, 1):
            ln = ln.split("#")[0].strip()
            if not ln:
                continue
            i, path = ln.split(None, 1)
            i = int(i)
            assert i not in by_id, f"MANIFEST.txt line {n}: duplicate id {i}"
            by_id[i] = os.path.join(ROOT, path.strip())
    if not by_id:
        return None
    trap = by_id.get(TRAP_ID) or next((q for q in by_id.values() if q.endswith("/trap.wt")), None)
    assert trap is not None, "MANIFEST.txt has no TRAP network to fill gaps"
    return [by_id.get(i, trap) for i in range(max(N_FIXED, max(by_id) + 1))]


def done_items():
    import csv
    with open(CHECKLIST, newline="") as f:
        return {r["item"] for r in csv.DictReader(f) if r["status"].strip() == "done"}


def boot(events, max_steps=5_000_000):
    h = Harness(manifest_paths(), events=list(events))
    h.run(0, np.zeros(65), max_steps=max_steps)
    return h


# ---- observation (encodings/io.md section 3)
STAGING = (0x3C0000, 0x3F0000)
CELL_BASE = 0x010000
FAULT, CIRC_FLAG, REJECT_COUNT = 0x00, 0x12, 0x14
ERRORS = {1: "#NULL!", 2: "#DIV/0!", 3: "#VALUE!", 4: "#REF!", 5: "#NAME?", 6: "#NUM!",
          7: "#N/A", 8: "#GETTING_DATA", 9: "#SPILL!", 10: "#CONNECT!", 11: "#BLOCKED!",
          12: "#UNKNOWN!", 13: "#FIELD!", 14: "#CALC!"}


def peek(h, addr):
    addr = int(addr)
    assert 0 <= addr < len(h.mem), addr
    assert not STAGING[0] <= addr < STAGING[1], "WEIGHT_STAGING holds networks; never read"
    return float(h.mem[addr])


def parse_a1(a):
    i = 0
    while a[i].isalpha():
        i += 1
    col = 0
    for ch in a[:i].upper():
        col = col * 26 + (ord(ch) - 64)
    return int(a[i:]) - 1, col - 1


def key_of(a, sheet=0):
    r, c = parse_a1(a)
    return sheet * 2**34 + r * 2**14 + c


def slot_of(h, a, sheet=0):
    r, c = parse_a1(a)
    s = (40503 * r + 65599 * c + 1000003 * sheet) % 65536
    want = key_of(a, sheet) + 1
    for _ in range(65536):
        k = peek(h, CELL_BASE + 8 * s)
        if k == want:
            return s
        if k == 0:
            return None
        s = (s + 1) % 65536
    return None


def text_at(h, handle):
    n = int(peek(h, handle))
    units = []
    for i in range((n + 2) // 3):
        w = int(peek(h, handle + 2 + i))
        units += [w % 65536, (w >> 16) % 65536, (w >> 32) % 65536]
    return b"".join(u.to_bytes(2, "little") for u in units[:n]).decode("utf-16-le")


def value(h, a):
    s = slot_of(h, a)
    if s is None:
        return {"blank": True}
    tag, pay = peek(h, CELL_BASE + 8 * s + 1), peek(h, CELL_BASE + 8 * s + 2)
    if tag == 0:
        return {"blank": True}
    if tag == 1:
        return pay
    if tag == 2:
        return text_at(h, int(pay))
    if tag == 3:
        return bool(pay)
    if tag == 4:
        return {"error": ERRORS.get(int(pay), f"#?{pay}")}
    return {"tag": tag, "pay": pay}
