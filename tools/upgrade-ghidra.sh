#!/usr/bin/env bash
#
# Upgrade the Ghidra sources that rz-ghidra compiles -- the decompiler engine
# plus the Sleigh processor specs -- to a newer upstream Ghidra release, while
# keeping the patches that rizinorg/ghidra's "rizin" branch adds on top.
#
# Usage:
#   bash tools/upgrade-ghidra.sh [Ghidra_12.1.3_build]
#
# After it finishes, rebuild with:  tools\build-ghidra.bat
#
# How it works
# ------------
# rz-ghidra compiles two things out of its ghidra submodule:
#   * Ghidra/Features/Decompiler/src/decompile/cpp   (the decompiler engine)
#   * Ghidra/Processors                              (the Sleigh specs: 150 of them)
#
# rizin's fork is upstream Ghidra + a small set of local patches (10 commits,
# 9 files, ~77 lines, all inside decompile/cpp). For every file it touches we do
# a proper 3-way merge:
#
#   base   = upstream as the rizin fork had it        (last upstream commit)
#   ours   = the new upstream release
#   theirs = rizin's fork, i.e. upstream + their patches
#
# so the rizin patches land on the new sources instead of being lost.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${1:-Ghidra_12.1.3_build}"

UP="$ROOT/.tools/ghidra-upstream"
FORK="$ROOT/build-clutter/dist/rz-ghidra-prefix/src/rz-ghidra/ghidra/ghidra"
PATCH="$ROOT/tools/rizin-ghidra.diff"
REL="Ghidra/Features/Decompiler/src/decompile/cpp"

# Last upstream (NSA) commit contained in rizinorg/ghidra's rizin branch; the
# rizin commits start right after it. Found with:
#   git -C $FORK log --format='%h %an %s' -12 origin/rizin
UPSTREAM_BASE_COMMIT="7e89d94e34"

[ -d "$FORK/.git" ] || { echo "[!] rz-ghidra's ghidra submodule not found at $FORK"; echo "    Build Clutter once (build-clutter.bat) so it is cloned."; exit 1; }
[ -f "$PATCH" ]     || { echo "[!] missing rizin patch set: $PATCH"; exit 1; }
command -v git >/dev/null || { echo "[!] git not found"; exit 1; }

echo "[*] Upstream Ghidra: $TAG"

echo "[*] Fetching upstream Ghidra (partial clone, only the two directories we need) ..."
if [ ! -d "$UP/.git" ]; then
    rm -rf "$UP"
    git clone --filter=blob:none --no-checkout --depth 1 --branch "$TAG" \
        https://github.com/NationalSecurityAgency/ghidra.git "$UP"
else
    git -C "$UP" fetch --filter=blob:none --depth 1 origin "refs/tags/$TAG:refs/tags/$TAG" --force
fi
git -C "$UP" sparse-checkout set "$REL" Ghidra/Processors >/dev/null
git -C "$UP" checkout --force "$TAG"
echo "    decompiler sources: $(ls "$UP/$REL" | wc -l) files, specs: $(find "$UP/Ghidra/Processors" -name '*.slaspec' | wc -l) slaspec"

FILES="$(grep '^diff --git' "$PATCH" | sed 's|.* b/||')"
[ -n "$FILES" ] || { echo "[!] no files found in $PATCH"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CONFLICTS=0

echo "[*] Merging rizin's patches onto $TAG ..."
for f in $FILES; do
    n="$(basename "$f")"
    git -C "$UP"  show "HEAD:$f"            > "$TMP/ours_$n"
    git -C "$FORK" show "$UPSTREAM_BASE_COMMIT:$f" > "$TMP/base_$n"
    git -C "$FORK" show "origin/rizin:$f"    > "$TMP/theirs_$n"
    if git merge-file -p --diff3 "$TMP/ours_$n" "$TMP/base_$n" "$TMP/theirs_$n" > "$TMP/m_$n"; then
        echo "    ok         $n"
    else
        echo "    CONFLICT   $n   (resolve the markers in $f)"
        CONFLICTS=$((CONFLICTS + 1))
    fi
    # Commit to the working tree with CRLF, because this clone uses core.autocrlf.
    sed 's/$/\r/' "$TMP/m_$n" > "$FORK/$f"
done

echo "[*] Replacing Ghidra/Processors ..."
rm -rf "$FORK/Ghidra/Processors"
cp -r "$UP/Ghidra/Processors" "$FORK/Ghidra/Processors"

echo
echo "[*] Mode:      $TAG"
echo "[*] Conflicted files: $CONFLICTS"
if [ "$CONFLICTS" -gt 0 ]; then
    echo "[!] Resolve the conflict markers above before building."
    exit 2
fi
echo "[+] Sources updated. Now rebuild the decompiler:"
echo "      tools\\build-ghidra.bat"
