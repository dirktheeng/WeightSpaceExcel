"""Compliance tests (docs/RULES.md rule 2, docs/ACCEPTANCE.md). Never read weights/."""
import ast
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE_EXT = {".py", ".sh", ".js", ".ts", ".c", ".cpp", ".h", ".rs", ".go", ".java", ".jl",
            ".rb", ".pl", ".lua", ".r", ".m", ".ps1", ".bat", ".ipynb", ".xlsm", ".vba", ".bas"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}


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


# ---- output tests: may read test data under tests/, never anything under weights/
# Static paths are resolved from the AST: __file__, os.path.dirname/abspath/join,
# Path(...), .parent and the / operator over module-level names and string constants.
# Every file-reading call must target a path that resolves statically to a file under
# tests/, or exactly weights/MANIFEST.txt (a list of paths, passed only to the harness)
# or checklist/CHECKLIST.csv (which functions are done).
OPEN_CALLS = {"open", "loadtxt", "genfromtxt", "fromfile", "load", "read_csv", "memmap"}
PATH_METHODS = {"read_text", "read_bytes", "open"}
DIR_CALLS = {"listdir", "walk", "scandir", "glob", "iglob", "rglob", "iterdir"}
BANNED_NAMES = {"load" + "_file", "load" + "_memory", "_build", "Network", "nets", "layers"}
BANNED_MODULES = {"subprocess", "shutil", "mmap", "pickle", "glob", "importlib", "ctypes"}
MANIFEST_REL = ("weights", "MANIFEST.txt")
CHECKLIST_REL = ("checklist", "CHECKLIST.csv")  # status column only, no weights


def _resolve(node, env, path):
    """Path as a tuple of segments relative to ROOT, or None if not statically known."""
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return tuple(os.path.relpath(path, ROOT).split(os.sep))
        return env.get(node.id)
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        v = _resolve(node.value, env, path)
        return v[:-1] if v else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        v = _resolve(node.left, env, path)
        r = node.right
        if v is not None and isinstance(r, ast.Constant) and isinstance(r.value, str):
            return v + tuple(r.value.split("/"))
        return None
    if isinstance(node, ast.Call):
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        args = node.args
        if name in ("dirname",) and len(args) == 1:
            v = _resolve(args[0], env, path)
            return v[:-1] if v else None
        if name in ("abspath", "realpath", "normpath", "Path") and len(args) == 1:
            return _resolve(args[0], env, path)
        if name == "resolve" and isinstance(fn, ast.Attribute) and not args:
            return _resolve(fn.value, env, path)
        if name == "join" and args:
            v = _resolve(args[0], env, path)
            for a in args[1:]:
                if v is None or not (isinstance(a, ast.Constant) and isinstance(a.value, str)):
                    return None
                v = v + tuple(a.value.split("/"))
            return v
    return None


def _norm(segs):
    out = []
    for s in segs:
        if s in ("", "."):
            continue
        if s == "..":
            if not out:
                return None
            out.pop()
        else:
            out.append(s)
    return tuple(out)


def output_test_violations(path):
    with open(path) as f:
        tree = ast.parse(f.read())
    env, bad = {}, []
    for node in tree.body:  # module-level path constants
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            v = _resolve(node.value, env, path)
            if v is not None:
                env[node.targets[0].id] = _norm(v)

    def allowed(target):
        v = _resolve(target, env, path)
        v = _norm(v) if v is not None else None
        return v is not None and (v in (MANIFEST_REL, CHECKLIST_REL) or (v[:1] == ("tests",) and len(v) > 1))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            names = [a.name for a in node.names]
            for m in mods:
                if m.split(".")[0] in BANNED_MODULES:
                    bad.append(f"line {node.lineno}: imports {m}")
            for n in names:
                if n in BANNED_NAMES:
                    bad.append(f"line {node.lineno}: imports {n}")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            bad.append(f"line {node.lineno}: uses {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_NAMES:
            bad.append(f"line {node.lineno}: uses .{node.attr}")
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        if name in DIR_CALLS:
            bad.append(f"line {node.lineno}: directory listing {name}")
        elif isinstance(fn, ast.Attribute) and name in PATH_METHODS and not node.args \
                and _resolve(fn.value, env, path) is not None:
            if not allowed(fn.value):
                bad.append(f"line {node.lineno}: {name} on a path outside tests/")
        elif name in OPEN_CALLS:
            if name == "load" and isinstance(fn, ast.Attribute) and getattr(fn.value, "id", "") in ("json", "yaml"):
                continue  # parses an already opened handle
            if not node.args or not allowed(node.args[0]):
                bad.append(f"line {node.lineno}: {name} target not a static path under tests/")
    return bad


def test_output_tests_do_not_read_files():
    for p in py_files(os.path.join("tests", "output")):
        bad = output_test_violations(p)
        assert not bad, f"{p} may read weights or unknown files: {bad}"


def test_output_test_checker_is_strict():
    """The checker itself must reject weight reads and accept test data reads."""
    import tempfile
    probes = {
        "W = os.path.join(ROOT, 'weights', 'smoke', 'add.wt')\nopen(W)\n": False,
        "W = os.path.join(ROOT, 'weights', 'x')\nopen(W)\n": False,
        "open(p)\n": False,
        "from harness.harness import load" + "_file\n": False,
        "h.nets[0]\n": False,
        "os.listdir(ROOT)\n": False,
        "D = os.path.join(ROOT, 'tests', '..', 'weights', 'a')\nopen(D)\n": False,
        "M = os.path.join(ROOT, 'weights', 'MANIFEST.txt')\nopen(M)\n": True,
        "C = os.path.join(ROOT, 'tests', 'output', 'stage1', 'cases.yaml')\nopen(C)\n": True,
    }
    head = "import os\nROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
    d = os.path.join(ROOT, "tests", "output")
    for src, ok in probes.items():
        with tempfile.NamedTemporaryFile("w", suffix=".py", dir=d, delete=False) as f:
            f.write(head + src)
        try:
            assert (not output_test_violations(f.name)) == ok, src
        finally:
            os.unlink(f.name)


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
