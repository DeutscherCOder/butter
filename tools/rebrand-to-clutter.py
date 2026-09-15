#!/usr/bin/env python3
"""Rebrand the Cutter fork in place: Cutter -> Clutter.

Rewrites identifiers/strings and renames files and directories inside the fork,
while *preserving* the names that belong to third parties or to the out-of-tree
plugin ABI (upstream repo/website, the dependency bundle, the cache variable and
target options that external plugin CMakeLists read, and the plugin file names
produced by those external trees).

Usage:  python .tools/rebrand-to-clutter.py <path-to-cutter-fork> [--check]
"""
import os
import sys

# Tokens that must survive untouched, because something outside this repo
# depends on their exact spelling. Replaced by placeholders during the rename
# and restored afterwards.
PROTECT = [
    # upstream project + drop-in dependency bundle (we keep pulling from it)
    "rizinorg/cutter-deps",
    "rizinorg/cutter",
    "cutter-deps",
    "cutter.re",
    "cutter_re",
    # out-of-tree plugin ABI: these names are read/written by the CMakeLists of
    # rz-ghidra, jsdec, rz-libyara and rz-frida, which link against us.
    "BUILD_CUTTER_PLUGIN",
    "CUTTER_INSTALL_PLUGDIR",
    "CUTTER_DEPS",
    "build_type=cutter",
    "plugin/cutter",
    "cutter-plugin",
    # plugin binaries produced by those external trees
    "jsdec_cutter.dll",
    "cutter_yara_plugin.dll",
    "cutter_frida_plugin.dll",
]

PLACEHOLDER = "<<<KEEP%d>>>"

# Longest first, so "rizinorg/cutter-deps" wins over "rizinorg/cutter".
PROTECT.sort(key=len, reverse=True)

REPLACE = [
    ("Cutter", "Clutter"),
    ("CUTTER", "CLUTTER"),
    ("cutter", "clutter"),
]

SKIP_DIRS = {"build-clutter", "cutter-deps", "rizin", ".git"}
ROOT_FILES = [
    "CMakeLists.txt",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".appveyor.yml",
    ".gitignore",
    ".clang-format",
]


def iter_targets(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if dirpath == root:
            for name in ROOT_FILES:
                path = os.path.join(root, name)
                if os.path.isfile(path):
                    yield path
        for name in filenames:
            yield os.path.join(dirpath, name)


def is_binary(path):
    try:
        with open(path, "rb") as fh:
            return b"\0" in fh.read(8192)
    except OSError:
        return True


def protect(text):
    for i, token in enumerate(PROTECT):
        text = text.replace(token, PLACEHOLDER % i)
    return text


def restore(text):
    for i, token in enumerate(PROTECT):
        text = text.replace(PLACEHOLDER % i, token)
    return text


def rewrite(text):
    for old, new in REPLACE:
        text = text.replace(old, new)
    return text


def rebrand_contents(root, check):
    changed = []
    for path in iter_targets(root):
        if is_binary(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                original = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        updated = restore(rewrite(protect(original)))
        if updated != original:
            changed.append(path)
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(updated)
    return changed


def protected_name(name):
    lowered = name.lower()
    if lowered == "cutter-deps":
        return True
    return False


def rebrand_names(root, check):
    # Directories first (deepest first), then files.
    moved = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        parts = os.path.relpath(dirpath, root).split(os.sep)
        if any(p in SKIP_DIRS for p in parts):
            continue
        for name in filenames + dirnames:
            if "cutter" not in name.lower() or protected_name(name):
                continue
            new_name = rewrite(name)
            if new_name == name:
                continue
            src = os.path.join(dirpath, name)
            dst = os.path.join(dirpath, new_name)
            moved.append((src, dst))
            if not check:
                os.rename(src, dst)
    return moved


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = os.path.abspath(sys.argv[1])
    check = "--check" in sys.argv
    if not os.path.isdir(os.path.join(root, "src")):
        print(f"[!] {root} does not look like the Cutter fork")
        return 2

    contents = rebrand_contents(root, check)
    names = rebrand_names(root, check)

    verb = "would change" if check else "changed"
    print(f"[$] {verb} {len(contents)} files")
    print(f"[$] {verb} {len(names)} paths")
    if check:
        for path in contents[:20]:
            print("    " + os.path.relpath(path, root))
        for src, dst in names[:20]:
            print("    " + os.path.relpath(src, root) + " -> " + os.path.basename(dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
