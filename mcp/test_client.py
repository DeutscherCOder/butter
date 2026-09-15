#!/usr/bin/env python3
"""Minimal MCP client, used to prove butter_mcp.py works end to end.

Speaks the same JSON-RPC-over-stdio protocol an AI client does, so it exercises
exactly the path an agent takes.

    python test_client.py [binary]      default: ../crackme/crackme.exe
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "butter_mcp.py")
REPO = os.path.dirname(HERE)


class Client:
    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, SERVER],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1,
        )
        self.next_id = 1

    def send(self, method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            msg["id"] = self.next_id
            self.next_id += 1
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        if notify:
            return None
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("server closed the connection")
            reply = json.loads(line)
            if reply.get("id") == msg.get("id"):
                return reply.get("result", reply.get("error"))

    def call(self, name, args=None):
        res = self.send("tools/call", {"name": name, "arguments": args or {}})
        if isinstance(res, dict) and "content" in res:
            text = res["content"][0]["text"]
            if res.get("isError"):
                return {"error": text}
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
        return res

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.wait(timeout=10)


def show(step, payload, limit=1400):
    text = json.dumps(payload, indent=2, default=str)
    if len(text) > limit:
        text = text[:limit] + "\n  ... (%d more chars)" % (len(text) - limit)
    print("\n=== %s ===\n%s" % (step, text))


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "crackme", "crackme.exe")
    target = os.path.abspath(target)

    c = Client()
    init = c.send("initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "butter-test-client", "version": "1.0"},
    })
    show("initialize", init)
    c.send("notifications/initialized", notify=True)

    tools = c.send("tools/list")
    show("tools/list", {"count": len(tools["tools"]),
                        "names": [t["name"] for t in tools["tools"]]})

    show("open", c.call("open", {"path": target}))
    show("analyze", c.call("analyze", {"level": "deep"}))
    show("functions", c.call("functions", {"filter": "", "limit": 8}))
    show("strings(filter=BUTTER)", c.call("strings", {"filter": "BUTTER", "min_len": 6}))
    show("search(hidden magic 'CKR1')", c.call("search", {"pattern": "CKR1"}))

    funcs = c.call("functions", {"filter": "main", "limit": 5}).get("functions", [])
    if funcs:
        show("decompile(main)", c.call("decompile", {"target": funcs[0]["name"]}), limit=1800)
        show("xrefs_to(main)", c.call("xrefs_to", {"target": funcs[0]["name"]}), limit=600)
        show("xrefs_from(main)", c.call("xrefs_from", {"target": funcs[0]["name"]}), limit=600)

    show("callgraph_json", c.call("callgraph_json", {"max_funcs": 300}), limit=600)
    show("callpaths(main -> fcn.140001000)",
         c.call("callpaths", {"from": "main", "to": "fcn.140001000", "limit": 2}),
         limit=600)
    show("types_load(inline)", c.call("types_load", {
        "content": "typedef unsigned int ButterBenchBool;\n"}))
    show("pdb_load(no sidecar)", c.call("pdb_load", {}))
    show("signatures_scan", c.call("signatures_scan", {}), limit=600)
    show("entrypoints", c.call("entrypoints", {}))
    show("imports(filter=Debugger)", c.call("imports", {"filter": "Debugger"}))
    show("sections", c.call("sections", {}), limit=800)
    show("hexdump(.rdata region)", c.call("hexdump", {"addr": "0x1400184b0", "size": 32}))
    show("disassemble_range", c.call("disassemble_range", {"addr": "0x140001010", "count": 4}),
         limit=700)

    show("run_command(afl~?)", c.call("run_command", {"command": "afl~?"}))
    show("session", c.call("session", {}))
    c.close()
    print("\n[+] MCP round trip complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
