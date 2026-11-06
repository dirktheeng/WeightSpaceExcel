"""Compliance tests (docs/RULES.md rule 2, docs/ACCEPTANCE.md). Never read weights/."""
import ast
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE_EXT = {".py", ".sh", ".js", ".ts", ".c", ".cpp", ".h", ".rs", ".go", ".java", ".jl",
            ".rb", ".pl", ".lua", ".r", ".m", ".ps1", ".bat", ".ipynb", ".xlsm", ".vba", ".bas"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
FILE_READ_NAMES = {"open", "loadtxt", "genfromtxt", "fromfile", "read_text", "read_bytes",
                   "readlines", "load", "listdir", "walk", "scandir", "glob"}


def files_under(top, skip_weights=True):
    for d, dirs, names in os.walk(top):
        rel = os.path.relpath(d, ROOT)
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS
                   and not (skip_weights and rel == "." and x == "weights")]
        for n in names:
            yield os.path.join(d, n)


def is_code(path):
    with open(path, "rb") as f:
        head = f.read(2)
    return os.path.splitext(path)[1].lower() in CODE_EXT or head == b"#!"


def test_no_code_outside_harness_and_tests():
    bad = []
    for p in files_under(ROOT, skip_weights=False):
        top = os.path.relpath(p, ROOT).split(os.sep)[0]
        if top in ("harness", "tests"):
            continue
        if top == "weights":  # check by name and shebang bytes only; values are never read
            if os.path.splitext(p)[1].lower() in CODE_EXT:
                bad.append(p)
            continue
        if is_code(p):
            bad.append(p)
    assert not bad, f"conventional code outside harness/ and tests/: {bad}"


def harness_digest():
    h = hashlib.sha256()
    d = os.path.join(ROOT, "harness")
    for p in sorted(files_under(d)):
        if os.path.basename(p) == "FROZEN.sha256":
            continue
        h.update(os.path.relpath(p, d).encode() + b"\0")
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def test_harness_frozen():
    with open(os.path.join(ROOT, "harness", "FROZEN.sha256")) as f:
        frozen = f.read().split()[0]
    assert harness_digest() == frozen, "harness changed; needs a decision record and re-freeze"


def py_files(sub):
    return [p for p in files_under(os.path.join(ROOT, sub)) if p.endswith(".py")]


def called_names(path):
    with open(path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            yield fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)


def test_output_tests_do_not_read_files():
    for p in py_files(os.path.join("tests", "output")):
        used = set(called_names(p)) & FILE_READ_NAMES
        assert not used, f"{p} calls file readers {used}; pass paths to the harness only"


def test_compliance_tests_skip_weights():
    for p in py_files(os.path.join("tests", "compliance")):
        with open(p) as f:
            src = f.read()
        banned = ["load" + "_file", "load" + "_memory"]
        assert not any(b in src for b in banned), p
        assert "skip_weights" in src  # weights/ excluded from content scans


def test_harness_and_networks_do_not_import_tests():
    for p in py_files("harness"):
        with open(p) as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            else:
                continue
            assert not any(m.split(".")[0] in ("tests", "pytest", "conftest") for m in mods), p
