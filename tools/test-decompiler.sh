#!/usr/bin/env bash
#
# Decompiler + Sleigh smoke test.
#
# Run after any Ghidra upgrade (tools/upgrade-ghidra.sh + build-ghidra.bat) to
# check that the rebuilt decompiler and processor specs still work.
#
# Usage:  bash tools/test-decompiler.sh
#
# What it verifies:
#   1. the Sleigh specs are at least Ghidra 12.1.3 -- the 68000:BE:32:CPU32
#      language only exists from 12.1.3 onwards, so it is a version marker
#   2. x86-64 sleigh loads at all
#   3. entry0 of the probe binary still decompiles into sane C
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RIZIN="$ROOT/clutter-dist/rizin.exe"
PROBE="$ROOT/tools/testprobe/probe.exe"

[ -f "$RIZIN" ] || { echo "[!] not found: $RIZIN   (run build-clutter.bat install first)"; exit 1; }
if [ ! -f "$PROBE" ]; then
    echo "[*] building probe binary ..."
    cmd //c "$(cygpath -w "$ROOT/tools/compile-probe.bat")" >/dev/null 2>&1
fi
[ -f "$PROBE" ] || { echo "[!] probe binary missing: $PROBE"; exit 1; }

# Use here-strings rather than `cmd | grep -q` everywhere: under `set -o pipefail`
# grep -q closing the pipe early reports SIGPIPE and every check looks failed.
fail=0
check() {  # check <haystack> <needle> <description>
    if grep -qF -- "$2" <<< "$1"; then
        echo "[ok]   $3"
    else
        echo "[FAIL] $3"
        fail=1
    fi
}
check_re() {  # check_re <haystack> <regex> <description>
    if grep -qE -- "$2" <<< "$1"; then
        echo "[ok]   $3"
    else
        echo "[FAIL] $3"
        fail=1
    fi
}
check_absent() {
    if grep -qE -- "$1" <<< "$2"; then
        echo "[FAIL] $3"
        fail=1
    else
        echo "[ok]   $3"
    fi
}

# rizin colourises output even when it is not a terminal, which would break every
# pattern below, so turn colour off and strip any escape sequences that remain.
plain() { tr -d '\r' | sed -e 's/\x1b\[[0-9;]*m//g'; }

run_rizin() { "$RIZIN" -e scr.color=0 -q "$@" "$PROBE" 2>/dev/null | plain; }

echo "[*] Sleigh languages ..."
LANGS="$(run_rizin -c "pdgs")"
check "$LANGS" "x86:LE:64:default"      "x86-64 sleigh language loads"
check "$LANGS" "68000:BE:32:CPU32"      "specs are Ghidra 12.1.3 or newer (CPU32 exists)"

echo "[*] Decompiling entry0 ..."
CODE="$(run_rizin -A -c "aaa; s entry0; pdg")"
[ -n "$CODE" ] || { echo "[FAIL] decompiler produced no output"; exit 1; }

# A signature line is a type + name + parentheses and no trailing semicolon,
# e.g. `uint64_t entry0(void)` or `code * fcn.140001000(void)`. The function is
# named after the symbol rizin resolved, so don't assert on a specific name.
check_re "$CODE" '^[A-Za-z_].*[A-Za-z0-9_]+\([^;]*\)$' "a function signature is emitted"
check "$CODE"      "{"         "a function body is emitted"
check "$CODE"      "}"         "the function body is closed"
check "$CODE"      ";"         "statements are emitted"
check_absent "\([^,)]*,  " "$CODE" "no double spaces after commas"

if [ "$fail" -eq 0 ]; then
    echo "[+] decompiler smoke test passed"
else
    echo "[!] decompiler smoke test failed"
fi
exit "$fail"
