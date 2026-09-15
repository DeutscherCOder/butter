#!/usr/bin/env python3
"""Measure what an analysis profile actually recovers.

Runs rizin with a profile applied first, then reports numbers that matter for
the decompiler: how many functions were found, how much code they cover, how
many data xrefs resolve, and how much detail the Ghidra decompiler produces for
a fixed anchor function. One rizin process per metric, so nothing has to be
guessed from interleaved output.

Usage:
    python .tools/analysis-bench.py [binary ...]
    python .tools/analysis-bench.py --list
"""
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIZIN = os.environ.get("CLUTTER_RIZIN", os.path.join(ROOT, "clutter-dist", "rizin.exe"))

# What Cutter runs today as the default (InitialOptionsDialog level 1).
BASELINE = ["aaa"]

# Candidate default profile for Clutter.
PROFILE = [
    "e analysis.hasnext=true",
    "e analysis.jmp.indir=true",
    "e analysis.jmp.above=true",
    "e analysis.jmp.cref=true",
    "e analysis.jmp.ref=true",
    "e analysis.jmp.tblmax=2048",
    "e analysis.types.constraint=true",
    "e analysis.refstr=true",
    "e analysis.brokenrefs=true",
    "e analysis.ptrdepth=4",
]

PROFILES = {
    "baseline (aaa)": BASELINE,
    "profile + aaa": PROFILE + ["aaa"],
    "profile + aaa +aav+aap": PROFILE + ["aaa", "aav", "aap"],
}

# Fixed data addresses used as xref anchors, per target.
ANCHORS = {
    "crackme.exe": ["0x140018320", "0x1400184b0"],
}

ESIL_NOISE = re.compile(r"Cannot peek memory without specifying an address")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\r")


def rizin(binary, profile, commands, timeout=900):
    args = [RIZIN, "-q"]
    for cmd in list(profile) + list(commands):
        args += ["-c", cmd]
    args.append(binary)
    started = time.time()
    proc = subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    elapsed = time.time() - started
    out = proc.stdout.decode("utf-8", "replace")
    out = ANSI.sub("", out)
    lines = [ln for ln in out.splitlines() if not ESIL_NOISE.search(ln)]
    return "\n".join(lines), elapsed


def jlist(text):
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def measure(binary, profile, anchors, anchor_func):
    funcs = jlist(rizin(binary, profile, ["aflj"])[0])
    strings = jlist(rizin(binary, profile, ["izj"])[0])
    total_bytes = sum(f.get("size", 0) for f in funcs if isinstance(f, dict))
    xrefs = []
    for addr in anchors:
        xrefs.append(len(jlist(rizin(binary, profile, [f"axtj @ {addr}"])[0])))
    decomp, seconds = rizin(binary, profile, [f"pdg @ {anchor_func}"])
    return {
        "functions": len(funcs),
        "code_bytes": total_bytes,
        "strings": len(strings),
        "xrefs": xrefs,
        "decomp_lines": len([ln for ln in decomp.splitlines() if ln.strip()]),
        "decomp_bytes": len(decomp.strip()),
        "seconds": round(seconds, 1),
    }


def main():
    binaries = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not binaries:
        binaries = [os.path.join(ROOT, "crackme", "crackme.exe"),
                    os.path.join(ROOT, "tools", "testprobe", "probe.exe")]
    if not os.path.isfile(RIZIN):
        print(f"[!] rizin not found at {RIZIN} (set CLUTTER_RIZIN)")
        return 1

    print(f"[*] engine: {RIZIN}")
    print(f"[*] profiles: {', '.join(PROFILES)}\n")
    for binary in binaries:
        if not os.path.isfile(binary):
            print(f"[!] skipping missing {binary}")
            continue
        name = os.path.basename(binary)
        anchors = ANCHORS.get(name, [])
        # Decompile a function that exists in both profiles, so the comparison
        # is about analysis quality and not about a missing symbol.
        anchor_func = "main" if anchors else "entry0"
        print(f"=== {name} ({os.path.getsize(binary):,} bytes)"
              f"{'  xref anchors: ' + ', '.join(anchors) if anchors else ''}"
              f"  decompile anchor: {anchor_func}")
        header = (f"{'profile':24} {'funcs':>6} {'code bytes':>11} {'strings':>8} "
                  f"{'xrefs':>10} {'pdg lines':>10} {'pdg bytes':>10} {'time':>7}")
        print(header)
        print("-" * len(header))
        for label, profile in PROFILES.items():
            row = measure(binary, profile, anchors, anchor_func)
            print(f"{label:24} {row['functions']:>6} {row['code_bytes']:>11} "
                  f"{row['strings']:>8} {str(row['xrefs']):>10} "
                  f"{row['decomp_lines']:>10} {row['decomp_bytes']:>10} "
                  f"{row['seconds']:>6}s")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
