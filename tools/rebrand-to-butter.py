#!/usr/bin/env python3
"""Rebrand the Butter tree in place: Butter -> Butter.

Second-stage rebrand. Rewrites identifiers/strings and renames files and
directories, while *preserving* everything that belongs to third parties or
to the out-of-tree plugin ABI:

  * upstream project/website/dependency bundle names (rizinorg/cutter, cutter-deps ...)
  * the plugin ABI names external CMakeLists read (CUTTER_DEPS, BUILD_CUTTER_PLUGIN, ...)
  * the plugin DLL names produced by those external trees (jsdec_cutter.dll, ...)
  * the compatibility shim filenames themselves (ButterPlugin.h, Butter.h, ButterCompat.h):
    they exist so plugins written against upstream Butter keep compiling
  * the Qt interface IID *string value* -- changing it would break every existing
    plugin that matches against the old IID

Usage:  python tools/rebrand-to-butter.py <path-to-tree> [--check]
"""
import os
import sys

# NOTE: this script rewrites every file it walks -- including potentially its own
# source if it lives inside the tree. Run it from a copy outside the target, or
# verify tools/rebrand-to-butter.py afterwards (REPLACE table and rebrand_names
# must still mention "clutter"/"cutter" as the *search* terms).

PROTECT = [
    # upstream project + drop-in dependency bundle (we keep pulling from it)
    "rizinorg/cutter-deps",
    "rizinorg/cutter",
    "cutter-deps",
    "cutter.re",
    "cutter_re",
    # Qt plugin interface IID string value: plugins compare against this exact
    # string; renaming it would orphan every existing upstream plugin.
    "org.rizinorg.cutter",
    # out-of-tree plugin ABI: read/written by the CMakeLists of rz-ghidra, jsdec,
    # rz-libyara and rz-frida, which link against us.
    "BUILD_CUTTER_PLUGIN",
    "CUTTER_INSTALL_PLUGDIR",
    "CUTTER_DEPS",
    "build_type=cutter",
    "plugin/cutter",
    "cutter-plugin",
    # the loader-side upstream-compat literal in PluginManager.cpp
    "create_cutter_plugin",
    # plugin binaries produced by those external trees
    "jsdec_cutter.dll",
    "cutter_yara_plugin.dll",
    "cutter_frida_plugin.dll",
]

PLACEHOLDER = "<<<KEEP%d>>>"

PROTECT.sort(key=len, reverse=True)

# Longest-first per case family so multi-word tokens win.
REPLACE = [
    ("Clutter", "Butter"),
    ("CLUTTER", "BUTTER"),
    ("clutter", "butter"),
    ("Cutter", "Butter"),
    ("CUTTER", "BUTTER"),
    ("cutter", "butter"),
]

# Filenames that must NOT be renamed: the compatibility shims that give
# upstream-Butter plugins the old names back.
PROTECTED_FILENAMES = {
    "cutterplugin.h",
    "cutter.h",
    "cuttercompat.h",
    "cutter.py",
    "cutterlayout.h",
    "cuttersearchable.h",
    "cutterseekable.h",
    "cutterdockwidget.h",
    "cuttergraphview.h",
    "cuttertreeview.h",
    "cuttercore.h",
    "cutterjson.h",
    "cuttercommon.h",
    "cutterdescriptions.h",
    "cutterapplication.cpp",
    "cutterapplication.h",
    "cutterconfig.h.in",
    "cutter-theme.css",
}

SKIP_DIRS = {"build-butter", "build-clutter", "cutter-deps", "butter-deps", "rizin", ".git"}

# Files whose *contents* legitimately mention Cutter (the compatibility shims
# themselves). They are protected from renames and from content rewrites, so
# re-running this script can never mangle the facade it exists to keep.
PROTECTED_CONTENT = {
    os.path.join("src", "compat", "core", "Cutter.h"),
    os.path.join("src", "compat", "core", "CutterCompat.h"),
    os.path.join("src", "compat", "plugins", "CutterPlugin.h"),
    os.path.join("src", "python", "cutter.py"),
    # files carrying intentionally-legacy literals (the shipped crackme's
    # embedded password/flags, the decoy-string YARA rule, prose about
    # upstream Cutter)
    os.path.join("crackme", "gen_blob.py"),
    os.path.join("crackme", "README.md"),
    os.path.join("tools", "yara", "butter-test.yar"),
    os.path.join("docs", "IDA-vs-BUTTER.md"),
}
PROTECTED_CONTENT = {p.lower() for p in PROTECTED_CONTENT}
# The script must never rewrite itself: it lives inside the tree it rebrands.
PROTECTED_CONTENT.add(os.path.join("tools", "rebrand-to-butter.py"))

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
        rel = os.path.relpath(dirpath, root)
        if rel == ".":
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
        rel = os.path.normpath(os.path.relpath(path, root)).lower()
        if rel in PROTECTED_CONTENT:
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
    return name.lower() in PROTECTED_FILENAMES


def rebrand_names(root, check):
    moved = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        parts = os.path.relpath(dirpath, root).split(os.sep)
        if any(p in SKIP_DIRS for p in parts):
            continue
        for name in filenames + dirnames:
            lowered = name.lower()
            if "clutter" not in lowered and "cutter" not in lowered:
                continue
            if protected_name(name):
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
        print(f"[!] {root} does not look like the fork tree")
        return 2

    contents = rebrand_contents(root, check)
    names = rebrand_names(root, check)

    verb = "would change" if check else "changed"
    print(f"[$] {verb} {len(contents)} files")
    print(f"[$] {verb} {len(names)} paths")
    if check:
        for path in contents[:25]:
            print("    " + os.path.relpath(path, root))
        for src, dst in names[:25]:
            print("    " + os.path.relpath(src, root) + " -> " + os.path.basename(dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
