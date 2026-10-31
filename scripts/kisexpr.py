"""Minimal lossless S-expression reader/writer for KiCad files.

Quoted strings are kept as QStr (raw, still escaped) so a parse -> dump round trip
does not change any token. Used to pull symbols out of the official libraries and
to write schematics in the current KiCad format.
"""
import os
import re
import uuid as _uuid

KICAD_SHARE = r"C:\Program Files\KiCad\10.0\share\kicad"
_TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


class QStr(str):
    """A quoted string token (content stored escaped, without the quotes)."""


def q(text):
    """Make a QStr from plain text, escaping as KiCad expects."""
    return QStr(str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n"))


def parse(text):
    stack = [[]]
    for tok in _TOKEN.findall(text):
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        elif tok[0] == '"':
            stack[-1].append(QStr(tok[1:-1]))
        else:
            stack[-1].append(tok)
    return stack[0][0]


def num(x):
    """Format a number the way KiCad does (no trailing zeros)."""
    s = f"{round(float(x), 4):.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _atom(a):
    if isinstance(a, QStr):
        return f'"{a}"'
    if isinstance(a, (int, float)):
        return num(a)
    return str(a)


def dump(node, indent=0):
    tabs = "\t" * indent
    if not isinstance(node, list):
        return tabs + _atom(node)
    head = []
    rest = []
    for item in node:
        (rest if isinstance(item, list) or rest else head).append(item)
    line = tabs + "(" + " ".join(_atom(a) for a in head)
    if not rest:
        return line + ")"
    # Short coordinate lists stay on one line, like KiCad writes them
    if all(isinstance(r, list) and r and r[0] == "xy" for r in rest):
        return line + "\n" + tabs + "\t" + " ".join(dump(r) for r in rest) + "\n" + tabs + ")"
    return line + "\n" + "\n".join(dump(r, indent + 1) for r in rest) + "\n" + tabs + ")"


def find(node, key):
    """First direct child list whose head is `key`."""
    for item in node:
        if isinstance(item, list) and item and item[0] == key:
            return item
    return None


def find_all(node, key):
    return [i for i in node if isinstance(i, list) and i and i[0] == key]


def new_uuid():
    return QStr(str(_uuid.uuid4()))


# ------------------------------------------------------------------ libraries
_lib_cache = {}


def load_lib(path):
    if path not in _lib_cache:
        with open(path, encoding="utf-8") as f:
            tree = parse(f.read())
        _lib_cache[path] = {str(s[1]): s for s in find_all(tree, "symbol")}
    return _lib_cache[path]


def _rename_units(node, old, new):
    out = []
    for item in node:
        if isinstance(item, list) and item and item[0] == "symbol" and str(item[1]).startswith(old + "_"):
            item = ["symbol", QStr(new + str(item[1])[len(old):])] + item[2:]
        out.append(item)
    return out


def flat_symbol(lib_path, name, lib_nick):
    """Return a schematic-ready (flattened, lib-prefixed) copy of a library symbol."""
    syms = load_lib(lib_path)
    sym = syms[name]
    ext = find(sym, "extends")
    if ext is None:
        body = [i for i in sym[2:]]
        return ["symbol", QStr(f"{lib_nick}:{name}")] + _rename_units(body, name, name)
    parent = flat_symbol(lib_path, str(ext[1]), lib_nick)
    parent_name = str(ext[1])
    child_props = find_all(sym, "property")
    child_keys = {str(p[1]) for p in child_props}
    flags, props, units = [], [], []
    for item in parent[2:]:
        if isinstance(item, list) and item[0] == "property":
            if str(item[1]) not in child_keys:
                props.append(item)
        elif isinstance(item, list) and item[0] == "symbol":
            units.append(item)
        else:
            flags.append(item)
    # Child-level flags (pin_names, exclude_from_sim, ...) override the parent's
    for item in sym[2:]:
        if isinstance(item, list) and item[0] not in ("property", "extends", "symbol"):
            flags = [f for f in flags if not (isinstance(f, list) and f[0] == item[0])] + [item]
    units = _rename_units(units, parent_name, name)
    return ["symbol", QStr(f"{lib_nick}:{name}")] + flags + child_props + props + units


def official_lib(nick):
    return os.path.join(KICAD_SHARE, "symbols", f"{nick}.kicad_sym")


def symbol_pins(flat):
    """{number: dict(name, x, y, angle, length, type)} for unit 1 (or common unit 0), body style 1."""
    pins = {}
    for unit in find_all(flat, "symbol"):
        parts = str(unit[1]).rsplit("_", 2)
        if parts[1] not in ("0", "1") or parts[2] not in ("0", "1"):
            continue
        for p in find_all(unit, "pin"):
            at = find(p, "at")
            pins[str(find(p, "number")[1])] = dict(
                name=str(find(p, "name")[1]), x=float(at[1]), y=float(at[2]),
                angle=float(at[3]) if len(at) > 3 else 0.0,
                length=float(find(p, "length")[1]), type=str(p[1]))
    return pins
