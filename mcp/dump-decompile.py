#!/usr/bin/env python3
"""Decompile a function through butter_mcp.py and print/save the result.

    python dump-decompile.py <binary> <function-or-address> [outfile]

Example:
    python dump-decompile.py ../crackme/crackme.exe main main.decompiled.c
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_client  # noqa: E402  (local helper module)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    binary, target = os.path.abspath(sys.argv[1]), sys.argv[2]
    outfile = sys.argv[3] if len(sys.argv) > 3 else None

    c = test_client.Client()
    c.send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}})
    c.send("notifications/initialized", notify=True)
    opened = c.call("open", {"path": binary})
    if "error" in opened:
        print("open failed: %s" % opened["error"])
        return 1
    c.call("analyze", {"level": "deep"})
    res = c.call("decompile", {"target": target})
    c.close()

    if "error" in res:
        print("decompile failed: %s" % res["error"])
        return 1
    code = res["code"]
    if outfile:
        with open(outfile, "w") as f:
            f.write(code)
        print("[+] %d chars -> %s" % (len(code), outfile))
    else:
        print(code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
