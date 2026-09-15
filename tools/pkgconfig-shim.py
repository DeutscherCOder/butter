#!/usr/bin/env python3
"""Minimal pkg-config implementation, used only by this project's build.

Why it exists: Butter's optional plugin bundling scripts (rz-frida's Butter
plugin, and anything else that runs `pkg_check_modules`) require a `pkg-config`
binary. This machine has none and installing one system-wide is exactly what
this project avoids. The build only needs to read the `.pc` files that the
bundled rizin installs into `butter-dist/lib/pkgconfig`, so a small
stdlib-only reader is enough.

Supported: --version, --exists, --modversion, --cflags, --libs, --variable,
--print-errors, --silence-errors, --static, --short-errors, --list-all,
--define-variable, --with-path, `mod`, `mod >= 1.2` version constraints and
`Requires:` recursion. Anything else exits 1 rather than lying about success.

Search order follows pkg-config: PKG_CONFIG_PATH (path-list), then --with-path,
then PKG_CONFIG_LIBDIR, then a couple of build-relative defaults.
"""
import os
import re
import sys

SHIM_VERSION = "1.8.0"


def log(msg):
    sys.stderr.write("pkg-config: %s\n" % msg)


class Pc:
    def __init__(self, path):
        self.path = path
        self.vars = {}
        self.fields = {}
        section = None
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                m = re.match(r"^([A-Za-z0-9_.]+)\s*:\s*(.*)$", line)
                if m and not line.startswith((" ", "\t")):
                    key, value = m.group(1), m.group(2)
                    if key in ("Name", "Description", "Version", "Requires",
                               "Requires.private", "Conflicts", "Libs", "Libs.private",
                               "Cflags", "Cflags.private", "URL"):
                        section = key
                        self.fields[key] = value.strip()
                    else:
                        section = None
                    continue
                m = re.match(r"^([A-Za-z0-9_.]+)\s*=\s*(.*)$", line)
                if m and section is None:
                    self.vars[m.group(1)] = m.group(2).strip()
                    continue
                if section:
                    self.fields[section] = (self.fields[section] + " " + line.strip()).strip()

    def expand(self, text, depth=0):
        if depth > 10:
            return text

        def sub(m):
            name = m.group(1)
            if name in self.vars:
                return self.expand(self.vars[name], depth + 1)
            return m.group(0)

        return re.sub(r"\$\{([A-Za-z0-9_.]+)\}", sub, text)

    def get(self, field):
        """Field value, or variable value (--variable=NAME reads either)."""
        if field in self.fields:
            return self.expand(self.fields[field]).strip()
        return self.expand(self.vars.get(field, "")).strip()

    @property
    def name(self):
        return self.get("Name")

    @property
    def version(self):
        return self.get("Version")


def default_paths():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return [
        os.path.join(here, "butter-dist", "lib", "pkgconfig"),
        os.path.join(here, "butter", "build-butter", "lib", "pkgconfig"),
    ]


def search_dirs(with_paths):
    dirs = []
    env = os.environ.get("PKG_CONFIG_PATH")
    if env:
        dirs += [d for d in re.split(r"[;:]", env) if d]
    dirs += with_paths
    libdir = os.environ.get("PKG_CONFIG_LIBDIR")
    if libdir:
        dirs += [d for d in re.split(r"[;:]", libdir) if d]
    if not dirs:
        dirs = default_paths()
    seen, out = set(), []
    for d in dirs:
        d = os.path.normpath(d)
        if d not in seen and os.path.isdir(d):
            seen.add(d)
            out.append(d)
    return out


def load_module(name, dirs, cache, overrides):
    if name in cache:
        return cache[name]
    for d in dirs:
        path = os.path.join(d, name + ".pc")
        if os.path.isfile(path):
            pc = Pc(path)
            for k, v in overrides.items():
                pc.vars[k] = v
            cache[name] = pc
            return pc
    cache[name] = None
    return None


def version_ok(have, op, want):
    def parts(v):
        return [int(x) if x.isdigit() else 0 for x in re.split(r"[^0-9]+", v) if x != ""]

    a, b = parts(have), parts(want)
    a += [0] * (len(b) - len(a))
    b += [0] * (len(a) - len(b))
    return {"=": a == b, "==": a == b, ">": a > b, "<": a < b,
            ">=": a >= b, "<=": a <= b, "!=": a != b}.get(op, a == b)


def collect(mods, dirs, cache, overrides, flag, static, seen=None):
    """Depth-first Requires: resolution, deduplicated."""
    if seen is None:
        seen = set()
    flags = []
    for name, op, want in mods:
        if name in seen:
            continue
        seen.add(name)
        pc = load_module(name, dirs, cache, overrides)
        if pc is None:
            continue
        req = pc.get("Requires") + (" " + pc.get("Requires.private") if static else "")
        if req:
            nested = parse_modules(req)
            flags += collect(nested, dirs, cache, overrides, flag, static, seen)
        value = pc.get(flag)
        if flag == "Cflags" and not value:
            value = pc.get("Cflags")
        flags += value.split()
    return flags


def parse_modules(text):
    out = []
    for part in re.split(r",|\s{2,}", text.strip()):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^([A-Za-z0-9_.+\-]+)\s*(>=|<=|==|!=|>|<|=)?\s*([0-9][^ ]*)?$", part)
        if m:
            out.append((m.group(1), m.group(2) or None, m.group(3) or None))
    return out


def main(argv):
    want_cflags = want_libs = want_modversion = want_exists = False
    print_errors = False
    static = False
    variable = None
    with_paths = []
    overrides = {}
    mods = []
    tokens = []
    pending = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--version":
            print(SHIM_VERSION + " (butter shim)")
            return 0
        elif a == "--cflags" or a == "--cflags-only-I" or a == "--cflags-only-other":
            want_cflags = True
        elif a == "--libs" or a == "--libs-only-l" or a == "--libs-only-L":
            want_libs = True
        elif a == "--modversion":
            want_modversion = True
        elif a == "--exists":
            want_exists = True
        elif a.startswith(("--atleast-version=", "--exact-version=", "--max-version=")):
            want_exists = True
            op = {"--atleast-version=": ">=", "--exact-version=": "==",
                  "--max-version=": "<="}[a.split("=", 1)[0] + "="]
            pending = (op, a.split("=", 1)[1])
        elif a == "--print-errors":
            print_errors = True
        elif a == "--silence-errors" or a == "--short-errors":
            pass
        elif a == "--static":
            static = True
        elif a == "--list-all":
            for d in search_dirs(with_paths):
                for f in sorted(os.listdir(d)):
                    if f.endswith(".pc"):
                        pc = Pc(os.path.join(d, f))
                        print("%-20s %s" % (f[:-3], pc.get("Description")))
            return 0
        elif a.startswith("--variable="):
            variable = a.split("=", 1)[1]
        elif a.startswith("--define-variable="):
            k, _, v = a.split("=", 1)[1].partition("=")
            overrides[k] = v
        elif a == "--with-path":
            with_paths.append(argv[i + 1])
            i += 1
        elif a.startswith("--"):
            log("unsupported option %s" % a)
            return 1
        else:
            # A module spec may arrive as one argv entry ("foo >= 1.2") or as
            # three (foo, >=, 1.2), so flatten everything before parsing.
            tokens.extend(a.split())
            if pending:
                mods.append((tokens[-1] if a.split() else a, pending[0], pending[1]))
                pending = None
                continue
        i += 1

    if pending:
        log("version option %r was given without a module" % (pending,))
        return 1

    idx = 0
    while idx < len(tokens):
        name = tokens[idx]
        if idx + 2 < len(tokens) and re.fullmatch(r">=|<=|==|!=|>|<|=", tokens[idx + 1]):
            mods.append((name, tokens[idx + 1], tokens[idx + 2]))
            idx += 3
        else:
            mods.append((name, None, None))
            idx += 1

    dirs = search_dirs(with_paths)
    cache = {}

    for name, op, want in mods:
        if not name:
            continue
        pc = load_module(name, dirs, cache, overrides)
        if pc is None:
            if print_errors:
                log("Package %s was not found in the pkg-config search path." % name)
            return 1
        if op and want and not version_ok(pc.version, op, want):
            if print_errors:
                log("Package %s has version %s, but %s was required."
                    % (name, pc.version, want))
            return 1

    if want_exists and not (want_cflags or want_libs or want_modversion or variable):
        return 0

    out = []
    if variable and mods:
        pc = load_module(mods[0][0], dirs, cache, overrides)
        if pc is not None:
            print(pc.get(variable))
        return 0
    if want_modversion:
        for name, _op, _want in mods:
            pc = load_module(name, dirs, cache, overrides)
            if pc is not None:
                print(pc.version)
        return 0
    if want_cflags:
        out += collect(mods, dirs, cache, overrides, "Cflags", static)
    if want_libs:
        out += collect(mods, dirs, cache, overrides, "Libs", static)
        if static:
            out += collect(mods, dirs, cache, overrides, "Libs.private", static)

    seen, deduped = set(), []
    for f in out:
        if f not in seen:
            seen.add(f)
            deduped.append(f)
    if deduped:
        print(" ".join(deduped))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
