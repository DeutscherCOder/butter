#!/usr/bin/env python3
"""Report how far Butter's Ghidra decompiler is behind upstream.

Butter's decompiler is the Ghidra decompiler engine plus Ghidra's Sleigh processor
specs, taken from a pinned upstream tag and patched with rizinorg/ghidra's `rizin`
branch. This script answers "what could I upgrade?" with numbers instead of guesses:

  * what version the tree currently contains (from the submodule checkout),
  * which upstream release tags exist and which is newest,
  * how many commits since that release touch the decompiler engine
    (`Ghidra/Features/Decompiler/src/decompile/cpp`) and the processor specs
    (`Ghidra/Processors`), on the release branch *and* on master,
  * the newest commits themselves, so the value of each upgrade is visible.

Usage:
    python .tools/ghidra-delta.py [--tree PATH] [--limit N]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

API = "https://api.github.com/repos/NationalSecurityAgency/ghidra"
DEFAULT_TREE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "build-butter", "dist", "rz-ghidra-prefix",
                            "src", "rz-ghidra", "ghidra", "ghidra")
WATCH = [
    ("decompiler engine", "Ghidra/Features/Decompiler/src/decompile/cpp"),
    ("sleigh processors", "Ghidra/Processors"),
]


def api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "butter-ghidra-delta",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def local_version(tree):
    if not os.path.isdir(tree):
        return None, None
    try:
        commit = subprocess.run(["git", "-C", tree, "rev-parse", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
        described = subprocess.run(["git", "-C", tree, "describe", "--tags", "HEAD"],
                                   capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
        return None, None
    return commit or None, described or None


def tag_date(tag, tags):
    for t in tags:
        if t["name"] == tag:
            return t["commit"]["sha"]
    return None


def commits_since(path, since, branch="master", limit=100):
    url = ("%s/commits?sha=%s&since=%s&per_page=%d&path=%s"
           % (API, branch, since, limit, path))
    try:
        return api(url)
    except Exception as e:  # noqa: BLE001
        return [{"commit": {"message": "ERROR: %s" % e}, "sha": "0" * 9}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", default=DEFAULT_TREE, help="Ghidra source tree")
    parser.add_argument("--limit", type=int, default=8, help="commits to show per path")
    parser.add_argument("--since", help="ISO date; default is the newest release date")
    args = parser.parse_args()

    commit, described = local_version(args.tree)
    print("== local tree ==")
    print("  path      : %s" % args.tree)
    print("  commit    : %s" % (commit or "<not found>"))
    print("  described : %s" % (described or "<unknown>"))

    releases = [t for t in api("%s/tags?per_page=30" % API)
                if re.match(r"^Ghidra_\d", t["name"])]
    print("  tags seen : %s" % ", ".join(t["name"] for t in releases[:6]))

    latest = api("%s/releases/latest" % API)
    newest_tag = latest["tag_name"]
    since = args.since or latest["published_at"]
    print("  newest release: %s (%s)" % (newest_tag, latest["published_at"]))
    sha = tag_date(newest_tag, releases)
    print("  release commit: %s" % (sha or "?"))

    ours = re.sub(r"[^0-9.]", "", (described or "").split("-")[0])
    if ours and ours not in newest_tag:
        print("  NOTE: the tree is on %s but %s exists -> a release upgrade is available"
              % (ours, newest_tag))
    elif ours:
        print("  tree matches the newest release family (%s)" % ours)

    print("\n== commits upstream since %s ==" % since)
    for label, path in WATCH:
        for branch in ("master", "Ghidra_12.2"):
            rows = commits_since(path, since, branch, max(args.limit, 100))
            if rows and "ERROR" in rows[0].get("commit", {}).get("message", ""):
                continue
            print("  %-18s %-12s %3d commits" % (label, branch, len(rows)))
            for c in rows[:args.limit]:
                print("      %s  %s" % (c["sha"][:9],
                                        c["commit"]["message"].splitlines()[0][:88]))
        print()


if __name__ == "__main__":
    sys.exit(main())
