#!/usr/bin/env python3
"""butter-mcp -- Model Context Protocol server for Butter / rizin.

Gives an MCP-speaking AI agent the whole Butter backend: analyse a binary, decompile
with the bundled Ghidra decompiler, disassemble, follow xrefs, inspect sections /
imports / exports / symbols / relocations / strings, search bytes and code, read and
write memory, define types, drive FLIRT + YARA signatures, run the Windows debugger,
diff two binaries, and fall back to raw rizin for anything else.

Standard library only. It drives the `rizin.exe` that ships next to Butter, so no GUI
and no plugin are needed.

Design notes
------------
* **One persistent rizin process.** Analysis state lives in that process, so `aaa` is
  paid once instead of on every tool call. A fresh `aaa` on a mid-size binary costs
  ~3s; reusing the session makes later calls nearly free. Output is delimited with
  `echo <marker>` (rizin's `?e`/`?v` refuse to run over a pipe), read on a background
  thread, and every command has a timeout after which the session is restarted.
* **Escape hatches.** `run_command` / `run_commands` reach anything not wrapped, so the
  tool list is a convenience layer rather than a cage.
* **Honest errors.** When rizin rejects a command the tool returns what rizin said,
  instead of silently reporting success.

Transports: stdio (default) and streamable HTTP (`--http 127.0.0.1:8765`).
"""
import argparse
import bisect
import hashlib
import json
import tempfile
from collections import deque
import os
import re
import shutil
import subprocess
import sys
import threading
import time

SERVER_NAME = "butter-mcp"
SERVER_VERSION = "0.3.0"

# Tuned discovery profile, measured in tools/analysis-bench.py: +45..232% more
# functions discovered for +0.1..3.4s on our three targets. Applied once per
# session before the aa/aaa/aaaa pass (and again after a session restart).
ANALYSIS_PROFILE = (
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
)

# Protocol revisions this server knows how to speak; the client's choice wins when
# it is in this list, otherwise the newest is offered.
PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]
PROTOCOL_FALLBACK = PROTOCOL_VERSIONS[0]

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TIMEOUT = 60.0
ANALYSIS_TIMEOUT = 900.0
DECOMPILE_TIMEOUT = 180.0
# Safety net for what finally reaches the model. Internal command output is never
# truncated: cutting a 650KB `aflj` in half would only break JSON parsing, so the
# cap is applied after tools have projected the fields they actually return.
MAX_OUTPUT = 2_000_000

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
NOISE = ("ERROR: Cannot peek memory", "WARNING: core: analysis propagation")

LOG_LEVEL = os.environ.get("BUTTER_MCP_LOG", "1") != "0"


def log(msg):
    if LOG_LEVEL:
        sys.stderr.write("[butter-mcp] %s\n" % msg)
        sys.stderr.flush()


def clean(text):
    """Strip ANSI escapes and rizin's esil spam, which is never useful to an agent."""
    text = ANSI.sub("", text)
    lines = [l for l in text.splitlines() if not l.lstrip().startswith(NOISE)]
    return "\n".join(lines).strip()


def truncate(text, limit=MAX_OUTPUT):
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [truncated: %d more characters]" % (len(text) - limit)


class ToolError(Exception):
    """Raised for problems the agent can fix (bad argument, no file open, ...)."""


# --------------------------------------------------------------- session

class RizinSession:
    """A long-lived rizin process driven line by line over pipes."""

    def __init__(self, exe):
        self.exe = exe
        self.proc = None
        self.path = None
        self.debug = False
        self.extras = []
        self._buf = bytearray()
        self._cv = threading.Condition()
        self._alive = False
        self._reader = None

    # -- lifecycle ------------------------------------------------------

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None and self._alive

    def start(self, path, debug=False, write=False, arch=None, bits=None,
              endian=None, flags=(), analysis=None):
        self.stop()
        args = [self.exe, "-e", "scr.color=0", "-e", "scr.utf8=0",
                "-e", "scr.interactive=false", "-e", "scr.prompt=false",
                "-e", "scr.html=false", "-e", "scr.null=false",
                "-e", "cfg.fortunes=false", "-q"]
        if debug:
            args.append("-d")
        if write:
            args.append("-w")
        if arch:
            args += ["-a", str(arch)]
        if bits:
            args += ["-b", str(bits)]
        if endian:
            args += ["-e", "cfg.bigendian=%s" % ("true" if endian == "big" else "false")]
        args += list(flags)
        args.append(path)

        self.proc = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0)
        self.path = path
        self.debug = debug
        self.extras = list(flags)
        self._buf = bytearray()
        self._alive = True
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

        # Probe, so a broken spawn surfaces immediately rather than as a later timeout.
        self.cmd("echo __butter_ready__", timeout=30)
        for evar in ANALYSIS_PROFILE:
            self.cmd(evar, timeout=30)
        if analysis:
            self.cmd({"basic": "aa", "deep": "aaa", "max": "aaaa"}[analysis],
                     timeout=ANALYSIS_TIMEOUT)
        return self

    def _read_loop(self):
        fd = self.proc.stdout.fileno()
        while True:
            try:
                chunk = os.read(fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            with self._cv:
                self._buf.extend(chunk)
                self._cv.notify_all()
        with self._cv:
            self._alive = False
            self._cv.notify_all()

    def stop(self):
        proc = self.proc
        self.proc = None
        self._alive = False
        if proc is None:
            return
        try:
            if proc.poll() is None:
                proc.stdin.write(b"q!\n")
                proc.stdin.flush()
                proc.wait(timeout=5)
        except Exception:
            pass
        if proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
        for stream in (proc.stdin, proc.stdout):
            try:
                stream.close()
            except Exception:
                pass

    # -- command execution ----------------------------------------------

    def cmd(self, command, timeout=DEFAULT_TIMEOUT, drop_output=False, limit=None):
        """Run one rizin command and return its output (marker delimited)."""
        if not self.running:
            raise ToolError("rizin session is not running (reopen the file)")

        marker = "__BUTTER_MARK_%d__" % time.time_ns()
        with self._cv:
            self._buf.clear()
        # `echo` is the only reliable marker: rizin refuses to run the `?e`/`?v`
        # evaluator commands when commands arrive on a pipe.
        payload = ("%s\necho %s\n" % (command, marker)).encode("utf-8", "replace")
        try:
            self.proc.stdin.write(payload)
            self.proc.stdin.flush()
        except (OSError, ValueError) as e:
            raise ToolError("rizin session died while sending a command: %s" % e)

        deadline = time.time() + timeout
        with self._cv:
            while marker.encode() not in self._buf:
                if not self._alive:
                    tail = clean(bytes(self._buf).decode("utf-8", "replace"))
                    raise ToolError("rizin exited unexpectedly. Tail: %s" % tail[-400:])
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError(
                        "timed out after %.0fs waiting for: %.60s" % (timeout, command))
                self._cv.wait(min(0.5, remaining))
            text = bytes(self._buf).decode("utf-8", "replace")
        head, _, rest = text.partition(marker)
        with self._cv:
            if rest.strip():
                self._buf.extend(rest.encode("utf-8", "replace"))
        if drop_output:
            return ""
        out = clean(head)
        return truncate(out, limit) if limit else out

    def cmd_json(self, command, timeout=DEFAULT_TIMEOUT, default=None):
        out = self.cmd(command, timeout=timeout)
        if not out:
            return default if default is not None else {"error": "empty output",
                                                       "command": command}
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {"raw": out, "command": command}


def find_rizin(explicit=None):
    for cand in (explicit, os.environ.get("BUTTER_RIZIN"),
                 os.path.join(REPO, "butter-dist", "rizin.exe"),
                 os.path.join(REPO, "butter-dist", "bin", "rizin.exe"),
                 os.path.join(REPO, "butter-dist", "rizin"),
                 shutil.which("rizin")):
        if cand and os.path.exists(cand):
            return cand
    return None


STATE = {
    "rizin": None,           # path to the rizin binary
    "session": None,         # RizinSession for static analysis
    "debug": None,           # RizinSession for debugging
    "file": None,            # currently open path
    "analysis": None,        # "basic" | "deep" | "max" | None
    "log_level": "info",
}
_lock = threading.RLock()


def session():
    s = STATE["session"]
    if s is None or not s.running:
        raise ToolError("no file open. Call `open` first.")
    return s


def debug_session():
    s = STATE["debug"]
    if s is None or not s.running:
        raise ToolError("no debug session. Call `debug_open` first.")
    return s


def ensure_analysis(level="deep"):
    """Run auto-analysis once per open file; reuse it afterwards."""
    cur = STATE["analysis"]
    if cur is None and level:
        pass
    elif cur is not None:
        order = {None: 0, "basic": 1, "deep": 2, "max": 3}
        if order.get(cur, 0) >= order.get(level or "deep", 2):
            return cur
    s = session()
    for evar in ANALYSIS_PROFILE:
        s.cmd(evar, timeout=30)
    cmd = {"basic": "aa", "deep": "aaa", "max": "aaaa"}[level or "deep"]
    s.cmd(cmd, timeout=ANALYSIS_TIMEOUT)
    STATE["analysis"] = level or "deep"
    return STATE["analysis"]


def restart_with_same_file(reason):
    """Recover from a hang or crash without silently losing the session."""
    path, debug, analysis = STATE["file"], False, STATE["analysis"]
    if not path:
        return
    log("restarting rizin session (%s)" % reason)
    try:
        STATE["session"] = RizinSession(STATE["rizin"]).start(path, analysis=analysis)
    except Exception as e:  # noqa: BLE001
        STATE["session"] = None
        log("restart failed: %r" % e)


def run(command, timeout=DEFAULT_TIMEOUT, auto_analyze=True, level="deep", limit=None):
    """Command against the session, with one automatic restart after a failure."""
    s = session()
    if auto_analyze:
        ensure_analysis(level)
    try:
        return s.cmd(command, timeout=timeout, limit=limit)
    except TimeoutError:
        restart_with_same_file("timeout on: %.60s" % command)
        raise ToolError("command timed out and the session was restarted: %.80s" % command)


def run_json(command, timeout=DEFAULT_TIMEOUT, auto_analyze=True, default=None):
    out = run(command, timeout=timeout, auto_analyze=auto_analyze)
    if not out:
        return default if default is not None else {"error": "empty output",
                                                    "command": command}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"raw": out, "command": command}


def target(args, key="target"):
    t = (args.get(key) or "").strip()
    if not t:
        raise ToolError("`%s` is required (function name or 0x address)" % key)
    if re.search(r"[\n\r]", t):
        raise ToolError("`%s` may not contain newlines" % key)
    return t


def safe_name(value, what="name"):
    if not re.fullmatch(r"[A-Za-z0-9_.$:]+", value or ""):
        raise ToolError("`%s` must be a plain identifier" % what)
    return value


def require_file():
    if not STATE["file"]:
        raise ToolError("no file open. Call `open` first.")
    return STATE["file"]


# --------------------------------------------------------------- tools

def t_open(a):
    path = os.path.abspath(os.path.expanduser(a["path"]))
    if not os.path.isfile(path):
        raise ToolError("no such file: %s" % path)
    if STATE["rizin"] is None:
        raise ToolError("rizin not found. Set BUTTER_RIZIN or build Butter first.")
    with _lock:
        STATE["session"] = RizinSession(STATE["rizin"]).start(
            path, write=bool(a.get("write")), arch=a.get("arch"), bits=a.get("bits"),
            endian=a.get("endian"), flags=(a.get("flags") or []))
        STATE["file"] = path
        STATE["analysis"] = None
        STATE["debug"] = None
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    info = run_json("ij", auto_analyze=False)
    keep = {}
    for key in ("arch", "bits", "endian", "os", "machine", "bintype", "class",
                "stripped", "compiler", "lang", "format", "size", "type"):
        if isinstance(info, dict):
            src = info.get("info", info) or {}
            if key in src:
                keep[key] = src[key]
    return {
        "path": path,
        "size": os.path.getsize(path),
        "sha256": digest,
        "file_info": keep or info,
        "session": "persistent rizin process (analysis is kept between tool calls)",
        "next": "call `analyze` (level=deep) before decompiling",
    }


def t_close(a):
    with _lock:
        for key in ("session", "debug"):
            if STATE[key]:
                STATE[key].stop()
                STATE[key] = None
        STATE["file"] = None
        STATE["analysis"] = None
    return {"closed": True}


def t_session(a):
    s = STATE["session"]
    return {
        "file": STATE["file"],
        "analysis": STATE["analysis"],
        "rizin": STATE["rizin"],
        "static_session_alive": bool(s and s.running),
        "debug_session_alive": bool(STATE["debug"] and STATE["debug"].running),
        "server": "%s %s" % (SERVER_NAME, SERVER_VERSION),
    }


def t_info(a):
    if a.get("full"):
        return run_json("ij", auto_analyze=False)
    info = run_json("ij", auto_analyze=False)
    if not isinstance(info, dict):
        return {"info": info}
    core = info.get("core", {})
    binf = info.get("bin", {})
    return {"core": core, "bin": binf, "size": core.get("size"),
            "format": binf.get("bintype"), "arch": binf.get("arch"),
            "bits": binf.get("bits"), "stripped": binf.get("stripped"),
            "os": binf.get("os"), "compiler": binf.get("compiler")}


def t_hashes(a):
    path = require_file()
    algos = [a["algorithm"]] if a.get("algorithm") else \
        ["md5", "sha1", "sha256", "sha512"]
    out = {}
    with open(path, "rb") as f:
        data = f.read()
    for algo in algos:
        try:
            out[algo] = hashlib.new(algo, data).hexdigest()
        except ValueError:
            raise ToolError("unknown hash algorithm: %s" % algo)
    return {"file": path, "size": len(data), "hashes": out}


def t_analyze(a):
    level = (a.get("level") or "deep").lower()
    if level not in ("basic", "deep", "max"):
        raise ToolError("level must be one of: basic, deep, max")
    t0 = time.perf_counter()
    ensure_analysis(level)
    n = run("afl~?", auto_analyze=False)
    extra = a.get("extra") or []
    for cmd in extra:
        run(cmd)
    return {"level": level, "functions": n, "extra": extra,
            "seconds": round(time.perf_counter() - t0, 2)}


def t_functions(a):
    out = run_json("aflj")
    if not isinstance(out, list):
        return {"functions": out}
    pattern = (a.get("filter") or "").lower()
    if pattern:
        out = [f for f in out if pattern in (f.get("name") or "").lower()]
    if a.get("sort") == "size":
        out = sorted(out, key=lambda f: f.get("size") or 0, reverse=True)
    limit = int(a.get("limit", 100))
    return {"count": len(out), "truncated": len(out) > limit,
            "functions": [{"name": f.get("name"), "addr": hex(f.get("offset", 0)),
                           "size": f.get("size"), "nbbs": f.get("nbbs"),
                           "cc": f.get("cc"), "noreturn": f.get("noreturn")}
                          for f in out[:limit]]}


def t_function_info(a):
    t = target(a)
    return {"target": t, "function": run_json("afij @ %s" % t)}


def t_define_function(a):
    t = target(a)
    run("af @ %s" % t)
    return {"target": t, "function": run_json("afij @ %s" % t)}


def t_undefine_function(a):
    t = target(a)
    return {"target": t, "result": run("af- @ %s" % t, auto_analyze=False) or "removed"}


def t_basic_blocks(a):
    t = target(a)
    out = run_json("afbj @ %s" % t)
    if isinstance(out, list):
        for b in out:
            b["addr"] = hex(b.get("addr", 0))
            if "jump" in b:
                b["jump"] = hex(b["jump"])
            if "fail" in b:
                b["fail"] = hex(b["fail"])
    return {"target": t, "blocks": out}


def t_cfg(a):
    t = target(a)
    out = run_json("agfj @ %s" % t)
    if a.get("format") == "dot":
        return {"target": t, "dot": run("agf @ %s" % t)}
    return {"target": t, "graph": out}


def t_callgraph(a):
    if a.get("target"):
        return {"target": a["target"],
                "callgraph": run("agC @ %s" % target(a))}
    out = run("agC")
    if not out.strip():
        # `agC` renders nothing in current rizin builds; fall back to the
        # edge graph recovered from per-function refs.
        _f, edges = _call_edges()
        lines = ["digraph callgraph {", "  rankdir=LR;"]
        lines += ['  "%s" -> "%s";' % (c, e) for c, e in edges]
        lines.append("}")
        out = "\n".join(lines)
    return {"callgraph": out}


def _cmd_path(path):
    """Quote a path for use inside a rizin command when it contains spaces."""
    return '"%s"' % path if any(c.isspace() for c in path) else path


def _call_edges(max_funcs=1000):
    """(caller, callee) call edges recovered from function disassembly.

    `agCj` returns nothing in current rizin builds and `axfj` stays empty
    without a call-xref pass, but call targets are visible in the instruction
    stream (`pdfj`), which is how t_xrefs_from already works. Only the
    max_funcs largest functions are swept to bound the cost.
    """
    funcs = run_json("aflj")
    if not isinstance(funcs, list):
        return [], []
    funcs = sorted((f for f in funcs if isinstance(f, dict)
                    and isinstance(f.get("offset"), int)),
                   key=lambda f: -int(f.get("size", 0) or 0))[:max_funcs]
    known = {f["offset"]: f.get("name") or ("0x%x" % f["offset"]) for f in funcs}
    call_types = ("call", "rcall", "ucall", "rjmp", "ujmp")  # calls + tail calls
    edges = set()
    for f in funcs:
        insns = run_json("pdj @ 0x%x" % f["offset"])
        if not isinstance(insns, list):
            continue
        caller = known[f["offset"]]
        for ins in insns:
            if not isinstance(ins, dict) or ins.get("type") not in call_types:
                continue
            to = ins.get("jump")
            if not isinstance(to, int):
                continue
            edges.add((caller, known.get(to) or ("0x%x" % to)))
    return funcs, sorted(edges)


def t_callgraph_json(a):
    """Whole-binary call graph. `agCj` is empty in current rizin builds, so the
    graph is built from `aflj` + per-function `axfj` instead."""
    max_funcs = max(10, min(int(a.get("max_funcs", 400)), 2000))
    funcs, edges = _call_edges(max_funcs)
    nodes = [{"name": f.get("name"), "addr": hex(f.get("offset", 0)),
              "size": f.get("size")} for f in funcs]
    return {"nodes": nodes, "edges": [{"from": c, "to": e} for c, e in edges],
            "edge_count": len(edges), "swept_functions": len(funcs)}


def t_callpaths(a):
    """Backward BFS over on-demand `axtj` call refs: which call chains reach
    `to` starting at `from`?

    This build has no working `agCj` and callers of `main` are often not even
    analysed functions, so the search walks *backwards* from the callee with
    per-address `axtj` (the one xref query that always answers here) and maps
    each caller instruction back to its containing function via `aflj`.
    """
    require_file()
    src_s, dst_s = target(a, "from"), target(a, "to")
    max_len = max(1, min(int(a.get("max_length", 6)), 10))
    limit = max(1, min(int(a.get("limit", 10)), 50))
    max_queries = max(50, min(int(a.get("max_queries", 1500)), 6000))

    funcs = run_json("aflj")
    by_name, starts = {}, []
    if isinstance(funcs, list):
        for f in funcs:
            if isinstance(f, dict) and isinstance(f.get("offset"), int):
                name = f.get("name") or ("0x%x" % f["offset"])
                by_name[name] = f["offset"]
                starts.append((f["offset"], int(f.get("size", 0) or 0), name))
    starts.sort()
    start_addrs = [s[0] for s in starts]

    def func_of(addr):
        """(name, start) of the analysed function containing addr, else (None, None)."""
        i = bisect.bisect_right(start_addrs, addr) - 1
        if i >= 0:
            off, size, name = starts[i]
            if addr < off + size:
                return name, off
        return None, None

    def addr_of(t):
        if t in by_name:
            return by_name[t]
        try:
            return int(t, 16) if t.lower().startswith("0x") else int(t)
        except ValueError:
            return None

    dst, src = addr_of(dst_s), addr_of(src_s)
    if dst is None:
        return {"from": src_s, "to": dst_s, "count": 0, "paths": [],
                "error": "unknown target %r; use a function name (see `functions`) "
                         "or a 0x address" % dst_s}
    if src is None:
        return {"from": src_s, "to": dst_s, "count": 0, "paths": [],
                "error": "unknown source %r; use a function name (see `functions`) "
                         "or a 0x address" % src_s}

    labels = {}
    start_names = {off: name for off, _size, name in starts}

    def label(off):
        """Best name for a node: the function name when it is an analysed
        function start, then an exact-address flag, else the raw address
        (fd happily reports a section name for an address that merely sits
        inside it, which reads as a wrong hop)."""
        if off not in labels:
            if off in start_names:
                labels[off] = start_names[off]
            else:
                info = run_json("fdj @ 0x%x" % off, auto_analyze=False,
                                default=None)
                name, addr = None, None
                if isinstance(info, dict):
                    name = info.get("name")
                    addr = info.get("address") or info.get("offset")
                try:
                    exact = int(str(addr), 0) == off
                except (TypeError, ValueError):
                    exact = False
                labels[off] = name if (exact and name) else ("0x%x" % off)
        return labels[off]

    if src == dst:
        return {"from": label(src), "to": label(dst), "count": 1,
                "paths": [label(src)]}

    # queue holds (node_addr, backward_chain). Nodes are function starts when
    # the caller is analysed, otherwise the raw caller instruction address.
    paths, queries = [], 0
    seen = {dst}
    q = deque([(dst, [dst])])
    while q and len(paths) < limit and queries < max_queries:
        callee, chain = q.popleft()
        if len(chain) >= max_len:
            continue
        refs = run_json("axtj @ 0x%x" % callee)
        queries += 1
        if not isinstance(refs, list):
            continue
        callers = sorted({r["from"] for r in refs
                          if isinstance(r, dict) and isinstance(r.get("from"), int)
                          and str(r.get("type", "")).lower() == "call"})
        for caddr in callers:
            cname, cstart = func_of(caddr)
            node = cstart if cstart is not None else caddr
            if node in chain or node in seen:
                continue
            new_chain = [node] + chain
            if node == src:
                paths.append(new_chain)
                if len(paths) >= limit:
                    break
                continue
            seen.add(node)
            q.append((node, new_chain))

    out = [" -> ".join(label(n) for n in chain) for chain in paths]
    return {"from": label(src), "to": label(dst), "count": len(out),
            "paths": out, "axtj_queries": queries}


def _sigdb_candidates(a):
    """Candidate .sig files: an explicit `sig` path, or the bundled sigdb
    subset matching this binary's format/arch/bits."""
    explicit = (a.get("sig") or "").strip()
    if explicit:
        p = os.path.abspath(os.path.expanduser(explicit))
        if os.path.isfile(p):
            return [p]
        if os.path.isdir(p):
            found = []
            for root, _dirs, files in os.walk(p):
                found += [os.path.join(root, f) for f in files if f.endswith(".sig")]
            return sorted(found)
        raise ToolError("no such sig file or directory: %s" % p)
    exe = STATE.get("rizin") or ""
    root = None
    for rel in (os.path.join("share", "sigdb"),
                os.path.join("..", "share", "sigdb")):
        cand = os.path.normpath(os.path.join(os.path.dirname(exe), rel))
        if os.path.isdir(cand):
            root = cand
            break
    if not root:
        return []
    info = run_json("ij", auto_analyze=False) or {}
    core = info.get("core", {}) if isinstance(info, dict) else {}
    bin_ = info.get("bin", {}) if isinstance(info, dict) else {}
    fmt = (core.get("format") or "").lower()
    arch = (bin_.get("arch") or core.get("arch") or "").lower()
    bits = bin_.get("bits") or core.get("bits")
    keys = {k for k in (fmt, fmt[:3], arch, str(bits) if bits else None) if k}
    out = []
    for dpath, _dirs, files in os.walk(root):
        parts = {p.lower() for p in dpath[len(root):].split(os.sep) if p}
        if keys and keys.isdisjoint(parts):
            continue
        out += [os.path.join(dpath, f) for f in files if f.endswith(".sig")]
    return sorted(out)


def t_signatures_scan(a):
    """Match FLIRT signatures against the binary. Requires a rizin build with
    the zignature plugin; the bundled build currently lacks it, so the tool
    reports that condition instead of failing silently."""
    require_file()
    cands = _sigdb_candidates(a)
    if not cands:
        return {"matches": [], "count": 0,
                "note": "no matching sigdb files found for this binary"}
    probe = run("z?", timeout=20)
    if "does not exist" in probe or "Error while executing" in probe:
        return {"matches": [], "count": 0,
                "sig_files_considered": len(cands),
                "sig_files": [os.path.basename(c) for c in cands[:20]],
                "blocked": "this rizin build lacks the zignature plugin (`z` "
                           "commands unavailable); FLIRT matching needs rizin "
                           "built with signatures enabled"}
    per = int(a.get("timeout_per_sig", 60))
    matches = []
    for path in cands[:40]:
        out = run("z /f %s" % _cmd_path(path), timeout=per)
        if out and "does not exist" not in out:
            matches.append({"sig": os.path.basename(path), "output": out.strip()[:400]})
    return {"count": len(matches), "matches": matches,
            "sig_files_considered": len(cands)}


def t_types_load(a):
    """Load types from a C header file (or inline `content`) with `to`.
    Types are what actually change decompiled output: struct/typedef names
    instead of undefined8."""
    require_file()
    src = (a.get("path") or a.get("header") or "").strip()
    content = a.get("content")
    timeout = int(a.get("timeout", 120))
    if src and content:
        raise ToolError("pass either `path`/`header` or `content`, not both")
    if not src and not content:
        raise ToolError("`path`/`header` or `content` is required")
    tmp_path = None
    if content:
        fd, tmp_path = tempfile.mkstemp(suffix=".h", prefix="butter-types-")
        with os.fdopen(fd, "w", encoding="utf-8", errors="replace") as fh:
            fh.write(content)
        src = tmp_path
    src = os.path.abspath(os.path.expanduser(src))
    if not os.path.isfile(src):
        raise ToolError("no such header file: %s" % src)
    try:
        out = run("to %s" % _cmd_path(src), timeout=timeout)
        types = run_json("tj", auto_analyze=False)
        count = len(types) if isinstance(types, list) else None
        return {"loaded": src, "types_now": count,
                "output": (out or "").strip() or None}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def t_pdb_load(a):
    """Load Microsoft PDB symbols (`idp`): from `path`, or the sidecar sitting
    next to the opened binary."""
    require_file()
    pdb = (a.get("path") or "").strip()
    if not pdb:
        base = os.path.splitext(STATE["file"])[0]
        cand = base + ".pdb"
        if os.path.isfile(cand):
            pdb = cand
        else:
            return {"loaded": False,
                    "note": "no .pdb given and no sidecar next to the binary (%s)" % cand}
    pdb = os.path.abspath(os.path.expanduser(pdb))
    if not os.path.isfile(pdb):
        raise ToolError("no such pdb: %s" % pdb)
    out = run("idp %s" % _cmd_path(pdb), timeout=int(a.get("timeout", 120)))
    syms = run_json("isj", auto_analyze=False)
    count = len(syms) if isinstance(syms, list) else None
    return {"loaded": pdb, "symbols_now": count, "output": (out or "").strip() or None}


def t_variables(a):
    t = target(a)
    return {"target": t, "variables": run_json("afvj @ %s" % t)}


def t_decompile(a):
    t = target(a)
    code = run("pdg @ %s" % t, timeout=DECOMPILE_TIMEOUT)
    return {"target": t, "decompiler": "ghidra (rz-ghidra)",
            "code": code or "no decompilation produced"}


def t_decompile_json(a):
    t = target(a)
    return {"target": t, "result": run_json("pdgj @ %s" % t, timeout=DECOMPILE_TIMEOUT)}


def t_decompile_many(a):
    targets = a.get("targets") or []
    if not isinstance(targets, list) or not targets:
        raise ToolError("`targets` must be a non-empty list")
    limit = int(a.get("limit", 25))
    out = {}
    for tgt in targets[:limit]:
        try:
            out[tgt] = run("pdg @ %s" % tgt, timeout=DECOMPILE_TIMEOUT)
        except Exception as e:  # noqa: BLE001
            out[tgt] = "failed: %s" % e
    return {"count": len(out), "decompiled": out}


def t_decompile_all(a):
    """Decompile every analysed function (`pdg` with @@f), capped."""
    limit = int(a.get("limit", 400))
    out = run("pdg @@f", timeout=DECOMPILE_TIMEOUT * 2)
    return {"note": "pdg over all functions; use decompile_many for control",
            "limit": limit, "code": out}


def t_disassemble(a):
    t = target(a)
    return {"target": t, "disassembly": run("pdf @ %s" % t)}


def t_disassemble_range(a):
    addr = a["addr"]
    count = int(a.get("count", 16))
    return {"addr": addr, "count": count,
            "disassembly": run("pd %d @ %s" % (count, addr))}


def t_disassemble_json(a):
    t = target(a)
    out = run_json("pdfj @ %s" % t)
    return {"target": t, "instructions": out}


def t_xrefs_to(a):
    t = target(a)
    out = run_json("axtj @ %s" % t)
    if isinstance(out, list):
        return {"target": t, "count": len(out), "refs": out}
    return {"target": t, "refs": out}


BRANCH_TYPES = ("call", "rcall", "ucall", "rjmp", "ujmp", "cjmp")


def t_xrefs_from(a):
    """Outgoing edges, read from the instruction stream.

    rizin's `axf` needs extra call analysis and returns nothing on a fresh database,
    so the edges are taken from the disassembly instead.
    """
    t = target(a)
    insns = run_json("pdj @ %s" % t)
    if not isinstance(insns, list):
        return {"target": t, "refs": insns}
    refs = []
    for ins in insns:
        if ins.get("type") not in BRANCH_TYPES:
            continue
        to = ins.get("jump")
        refs.append({"from": hex(ins.get("offset", 0)), "kind": ins.get("type"),
                     "to": hex(to) if isinstance(to, int) else None,
                     "instruction": ins.get("opcode")})
    return {"target": t, "count": len(refs), "refs": refs}


def t_entrypoints(a):
    return {"entrypoints": run_json("iej", auto_analyze=False)}


def t_sections(a):
    out = run_json("iSj", auto_analyze=False)
    if not isinstance(out, list):
        return {"sections": out}
    return {"sections": [dict(s, vaddr=hex(s.get("vaddr", 0)),
                              paddr=hex(s.get("paddr", 0))) for s in out]}


def t_segments(a):
    return {"segments": run_json("iSSj", auto_analyze=False)}


def t_imports(a):
    out = run_json("iij", auto_analyze=False)
    if not isinstance(out, list):
        return {"imports": out}
    pattern = (a.get("filter") or "").lower()
    if pattern:
        out = [i for i in out if pattern in (i.get("name") or "").lower()
               or pattern in (i.get("libname") or "").lower()]
    limit = int(a.get("limit", 300))
    return {"count": len(out), "imports": out[:limit], "truncated": len(out) > limit}


def t_exports(a):
    out = run_json("iEj", auto_analyze=False)
    limit = int(a.get("limit", 300))
    if isinstance(out, list):
        return {"count": len(out), "exports": out[:limit]}
    return {"exports": out}


def t_symbols(a):
    out = run_json("isj", auto_analyze=False)
    if not isinstance(out, list):
        return {"symbols": out}
    pattern = (a.get("filter") or "").lower()
    if pattern:
        out = [s for s in out if pattern in (s.get("name") or "").lower()]
    limit = int(a.get("limit", 300))
    return {"count": len(out), "symbols": out[:limit], "truncated": len(out) > limit}


def t_relocs(a):
    return {"relocations": run_json("irj", auto_analyze=False)}


def t_libraries(a):
    return {"libraries": run_json("ilj", auto_analyze=False)}


def t_resources(a):
    return {"resources": run_json("iRj", auto_analyze=False)}


def t_types_list(a):
    out = run_json("tj")
    if not isinstance(out, list):
        return {"types": out}
    pattern = (a.get("filter") or "").lower()
    if pattern:
        out = [t for t in out if pattern in json.dumps(t).lower()]
    limit = int(a.get("limit", 200))
    return {"count": len(out), "types": out[:limit], "truncated": len(out) > limit}


def t_type_apply(a):
    addr = a["addr"]
    type_name = a["type"]
    return {"addr": addr, "type": type_name,
            "result": run("t %s @ %s" % (safe_name(type_name, "type"), addr))
                      or "applied"}


def t_flags(a):
    out = run_json("fj")
    if not isinstance(out, list):
        return {"flags": out}
    pattern = (a.get("filter") or "").lower()
    if pattern:
        out = [f for f in out if pattern in (f.get("name") or "").lower()]
    limit = int(a.get("limit", 200))
    return {"count": len(out), "flags": out[:limit], "truncated": len(out) > limit}


def t_add_flag(a):
    name = safe_name(a["name"])
    addr = a.get("addr", "$$")
    return {"name": name, "addr": addr, "result": run("f %s @ %s" % (name, addr))
                                                   or "flag added"}


def t_remove_flag(a):
    name = safe_name(a["name"])
    return {"name": name, "result": run("f-%s" % name) or "flag removed"}


def t_strings(a):
    min_len = int(a.get("min_len", 5))
    pattern = (a.get("filter") or "").lower()
    out = run_json("izzj")
    if not isinstance(out, list):
        return {"strings": out}
    rows = []
    for s in out:
        text = s.get("string") or ""
        if len(text) < min_len or (pattern and pattern not in text.lower()):
            continue
        rows.append({"addr": hex(s.get("vaddr", 0)), "len": s.get("length"),
                     "type": s.get("type"), "string": text})
    limit = int(a.get("limit", 200))
    return {"count": len(rows), "strings": rows[:limit],
            "truncated": len(rows) > limit}


SEARCH_KINDS = {"bytes": "/x", "string": "/z", "asm": "/a", "value": "/v",
                "regex": "/A", "wide": "/w", "rop": "/R", "refs": "/r",
                "crypto": "/c", "xor": "/x"}


def t_search(a):
    pattern = (a.get("pattern") or "").strip()
    if not pattern:
        raise ToolError("`pattern` is required")
    kind = (a.get("kind") or "").lower()
    if not kind:
        kind = "bytes" if re.fullmatch(r"(?:[0-9a-fA-F]{2})+", pattern) else "string"
    if kind not in SEARCH_KINDS:
        raise ToolError("kind must be one of: %s" % ", ".join(sorted(SEARCH_KINDS)))
    prefix = SEARCH_KINDS[kind]
    if kind == "regex":
        cmd = "%s %s" % (prefix, pattern)
    else:
        cmd = "%s %s" % (prefix, pattern.replace('"', ""))
    hits = run(cmd)
    addresses = re.findall(r"0x[0-9a-fA-F]{4,}", hits)
    return {"pattern": pattern, "kind": kind, "command": cmd,
            "hit_count": len(addresses), "hits": hits or "no hits"}


def t_read_bytes(a):
    addr = a["addr"]
    size = int(a.get("size", 64))
    data = run("p8 %d @ %s" % (size, addr))
    raw = re.sub(r"\s+", "", data)
    try:
        blob = bytes.fromhex(raw)
    except (ValueError, TypeError):
        return {"addr": addr, "size": size, "hex": raw, "note": "not hex output"}
    return {"addr": addr, "size": len(blob), "hex": raw,
            "ascii": "".join(chr(b) if 32 <= b < 127 else "." for b in blob)}


def t_write_bytes(a):
    addr = a["addr"]
    hex_bytes = re.sub(r"\s+", "", a["hex"])
    if not re.fullmatch(r"(?:[0-9a-fA-F]{2})+", hex_bytes or ""):
        raise ToolError("`hex` must be an even-length hex string")
    return {"addr": addr, "bytes": hex_bytes,
            "result": run("wx %s @ %s" % (hex_bytes, addr)) or "patched",
            "note": "in-memory unless the file was opened with write=true"}


def t_write_asm(a):
    addr = a["addr"]
    asm = a["asm"].replace("\n", " ")
    return {"addr": addr, "asm": asm,
            "result": run("'wa %s' @ %s" % (asm, addr), auto_analyze=False)
                      or "assembled and written"}


def t_hexdump(a):
    addr = a["addr"]
    size = int(a.get("size", 64))
    mode = a.get("mode") or "hex"
    cmd = {"hex": "px", "words": "pxw", "quadwords": "pxq",
           "disasm": "pdi", "string": "ps"}.get(mode, "px")
    return {"addr": addr, "size": size, "mode": mode,
            "dump": run("%s %d @ %s" % (cmd, size, addr))}


def t_config_list(a):
    pattern = a.get("filter") or ""
    out = run("e~%s" % pattern if pattern else "e", auto_analyze=False)
    return {"config": out}


def t_config_get(a):
    key = a["key"]
    return {"key": key, "value": run("e %s" % key, auto_analyze=False)}


def t_config_set(a):
    key, value = a["key"], a["value"]
    if re.search(r"[;&|]", key + value):
        raise ToolError("config key/value may not contain command separators")
    return {"key": key, "value": value,
            "result": run("e %s=%s" % (key, value), auto_analyze=False) or "set"}


def t_comment(a):
    t = target(a)
    text = a["text"].replace('"', "'")
    return {"target": t, "result": run("CC %s @ %s" % (text, t)) or "comment set"}


def t_rename(a):
    t = target(a)
    name = safe_name(a["name"])
    return {"target": t, "name": name,
            "result": run("afn %s @ %s" % (name, t)) or "renamed"}


def t_rename_flag(a):
    return {"old": a["old"], "new": safe_name(a["new"], "new"),
            "result": run("fr %s %s" % (safe_name(a["old"], "old"), safe_name(a["new"], "new")))
                      or "renamed"}


def t_library_functions(a):
    """Functions identified as library code, mostly by FLIRT signatures.

    rizin names them `flirt.*` during analysis; they are the parts of a binary a
    reverse engineer can usually skip, and knowing them sharpens `functions`.
    """
    out = run_json("aflj")
    if not isinstance(out, list):
        return {"library_functions": out}
    libs = [f for f in out if (f.get("name") or "").startswith("flirt.")]
    limit = int(a.get("limit", 200))
    return {"count": len(libs), "total_functions": len(out),
            "flirt_ratio": round(len(libs) / max(1, len(out)), 3),
            "note": "rizin has no zignature commands in this build; FLIRT naming "
                    "happens during analysis",
            "functions": [{"name": f.get("name"), "addr": hex(f.get("offset", 0)),
                           "size": f.get("size")} for f in libs[:limit]]}


def t_yara_scan(a):
    path = os.path.abspath(os.path.expanduser(a["rules"]))
    if not os.path.isfile(path):
        raise ToolError("no such YARA rules file: %s" % path)
    run("yaral %s" % path)
    return {"rules": path, "matches": run_json("yaraMj", auto_analyze=False)}


def t_yara_folder(a):
    folder = os.path.abspath(os.path.expanduser(a["folder"]))
    if not os.path.isdir(folder):
        raise ToolError("no such folder: %s" % folder)
    run("yarad %s" % folder)
    return {"folder": folder, "matches": run_json("yaraMj", auto_analyze=False)}


def t_yara_matches(a):
    return {"matches": run_json("yaraMj", auto_analyze=False)}


def t_rop(a):
    limit = int(a.get("limit", 200))
    out = run("/R %d" % limit)
    return {"gadgets": out}


def t_emulate(a):
    """ESIL emulation -- experimental.

    rizin's esil engine is incomplete on PE files (no Windows API emulation) and can
    spin; the call is time-boxed and a timeout restarts the session.
    """
    steps = int(a.get("steps", 8))
    if steps < 1 or steps > 2000:
        raise ToolError("`steps` must be between 1 and 2000")
    addr = a.get("addr")
    prefix = ""
    if addr:
        prefix = "s %s; " % addr
    out = run("%saei; aeim; aeip; %d*aes; aer" % (prefix, steps), timeout=20)
    return {"experimental": True, "steps": steps, "state": out,
            "note": "esil cannot emulate Windows APIs; treat results as best effort"}


def t_run_command(a):
    cmd = a["command"]
    return {"command": cmd, "output": run(cmd, timeout=float(a.get("timeout") or DEFAULT_TIMEOUT))}


def t_run_commands(a):
    cmds = a["commands"]
    if isinstance(cmds, str):
        cmds = [cmds]
    outputs = []
    for c in cmds:
        try:
            outputs.append({"command": c, "output": run(c)})
        except Exception as e:  # noqa: BLE001
            outputs.append({"command": c, "error": str(e)})
    return {"outputs": outputs}


def t_project_save(a):
    path = os.path.abspath(os.path.expanduser(a["path"]))
    return {"path": path, "result": run("Ps %s" % path) or "saved"}


def t_project_open(a):
    path = os.path.abspath(os.path.expanduser(a["path"]))
    if not os.path.isfile(path):
        raise ToolError("no such project: %s" % path)
    out = run("Po %s" % path)
    STATE["analysis"] = "basic"
    return {"path": path, "result": out or "loaded",
            "note": "analysis level is unknown after a project load"}


def t_diff_binaries(a):
    """Compare two binaries with the bundled rz-diff."""
    exe = os.path.join(os.path.dirname(STATE["rizin"] or ""), "rz-diff.exe")
    if not os.path.isfile(exe):
        raise ToolError("rz-diff.exe not found next to rizin")
    left = os.path.abspath(os.path.expanduser(a["left"]))
    right = os.path.abspath(os.path.expanduser(a["right"]))
    proc = subprocess.run([exe, "-j", "code", left, right],
                          capture_output=True, text=True)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"raw": clean(proc.stdout or proc.stderr)}
    return {"left": left, "right": right, "diff": data}


# ---- debugging ---------------------------------------------------------

def t_debug_open(a):
    path = os.path.abspath(os.path.expanduser(a["path"]))
    if not os.path.isfile(path):
        raise ToolError("no such file: %s" % path)
    if STATE["rizin"] is None:
        raise ToolError("rizin not found")
    with _lock:
        STATE["debug"] = RizinSession(STATE["rizin"]).start(
            path, debug=True, analysis=a.get("analysis") or "basic")
    listed = run("dp", auto_analyze=False)
    wanted = os.path.basename(path).lower()
    lines = listed.splitlines()
    mine = [l for l in lines if l.strip().startswith("*")]
    if not mine:
        mine = [l for l in lines if wanted in l.lower()]
    return {
        "path": path,
        "target_process": mine[0].strip() if mine else lines[:3],
        "note": "Windows debugging works for stepping, registers, memory and "
                "backtraces. Software breakpoints at absolute addresses can fail "
                "under ASLR because rizin's Windows module list is incomplete; "
                "step to the address instead.",
    }


def t_debug_status(a):
    s = STATE["debug"]
    if s is None:
        return {"debug_session": None}
    return {"debug_session": {"file": s.path, "alive": s.running,
                              "process": s.cmd("dp", timeout=30) if s.running else None}}


def t_debug_step(a):
    n = int(a.get("n", 1))
    s = debug_session()
    for _ in range(max(1, min(n, 500))):
        s.cmd("ds", timeout=30)
    return {"registers": s.cmd("dr", timeout=30),
            "disassembly": s.cmd("pd 3", timeout=30)}


def t_debug_continue(a):
    s = debug_session()
    return {"note": "this blocks until the target stops",
            "state": s.cmd("dc", timeout=float(a.get("timeout") or 60))}


def t_debug_registers(a):
    s = debug_session()
    reg = a.get("register")
    return {"registers": s.cmd("dr %s" % reg if reg else "dr", timeout=30)}


def t_debug_backtrace(a):
    s = debug_session()
    return {"backtrace": s.cmd("dbt", timeout=30)}


def t_debug_maps(a):
    s = debug_session()
    return {"maps": s.cmd("dm", timeout=30),
            "modules": s.cmd_json("dmmj", timeout=30)}


def t_debug_breakpoint(a):
    s = debug_session()
    addr = a["addr"]
    s.cmd("s %s" % addr, timeout=30)
    out = s.cmd("db", timeout=30)
    return {"addr": addr, "result": out or "breakpoint added",
            "breakpoints": s.cmd("dbl", timeout=30)}


def t_debug_breakpoints(a):
    s = debug_session()
    return {"breakpoints": s.cmd("dbl", timeout=30)}


def t_debug_breakpoint_remove(a):
    s = debug_session()
    s.cmd("s %s" % a["addr"], timeout=30)
    return {"result": s.cmd("db-", timeout=30) or "removed",
            "breakpoints": s.cmd("dbl", timeout=30)}


def t_debug_memory(a):
    s = debug_session()
    addr, size = a["addr"], int(a.get("size", 64))
    return {"addr": addr, "size": size, "dump": s.cmd("px %d @ %s" % (size, addr), timeout=30)}


def t_debug_write(a):
    s = debug_session()
    hex_bytes = re.sub(r"\s+", "", a["hex"])
    if not re.fullmatch(r"(?:[0-9a-fA-F]{2})+", hex_bytes or ""):
        raise ToolError("`hex` must be an even-length hex string")
    return {"addr": a["addr"], "result": s.cmd("wx %s @ %s" % (hex_bytes, a["addr"]),
                                              timeout=30) or "written"}


def t_debug_detach(a):
    """End the debug session.

    rizin has no clean Windows detach, and it terminates the debuggee when the
    debugger process exits, so this stops the session (both by default and when
    `kill` is passed) rather than pretending a detach happened.
    """
    s = STATE["debug"]
    if s is None:
        raise ToolError("no debug session")
    with _lock:
        s.stop()
        STATE["debug"] = None
    return {"stopped": True,
            "note": "the rizin debugger process exited; on Windows that also ends "
                    "the debuggee"}


TOOLS = [
    # name, description, input schema, function
    ("open", "Open a binary for analysis in a persistent rizin session. Call this first.",
     {"type": "object", "properties": {
         "path": {"type": "string"},
         "arch": {"type": "string", "description": "force architecture"},
         "bits": {"type": "integer"},
         "endian": {"type": "string", "enum": ["little", "big"]},
         "write": {"type": "boolean", "description": "open for writing"},
         "flags": {"type": "array", "items": {"type": "string"},
                   "description": "extra rizin CLI flags"}},
      "required": ["path"]}, t_open),
    ("close", "Close the file and stop the rizin session.", {"type": "object",
     "properties": {}}, t_close),
    ("session", "Report the open file, analysis level and session health.",
     {"type": "object", "properties": {}}, t_session),
    ("info", "Binary metadata: format, arch, bits, OS, compiler, size, stripped.",
     {"type": "object", "properties": {"full": {"type": "boolean"}}}, t_info),
    ("hashes", "Hash the opened file (md5/sha1/sha256/sha512).",
     {"type": "object", "properties": {"algorithm": {"type": "string"}}}, t_hashes),

    ("analyze", "Run auto-analysis (applies the tuned discovery profile first, see tools/analysis-bench.py). Level basic=aa, deep=aaa, max=aaaa. Other tools reuse it.",
     {"type": "object", "properties": {
         "level": {"type": "string", "enum": ["basic", "deep", "max"], "default": "deep"},
         "extra": {"type": "array", "items": {"type": "string"},
                   "description": "extra rizin analysis commands, e.g. ['aar','aac']"}}},
     t_analyze),
    ("functions", "List analysed functions, filter by name, optionally sorted by size.",
     {"type": "object", "properties": {
         "filter": {"type": "string"}, "limit": {"type": "integer", "default": 100},
         "sort": {"type": "string", "enum": ["name", "size"]}}}, t_functions),
    ("function_info", "Full metadata for one function (size, blocks, cost, signature).",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_function_info),
    ("define_function", "Create/analyse a function at an address or name.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_define_function),
    ("undefine_function", "Remove a function definition.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_undefine_function),
    ("basic_blocks", "Basic blocks of a function with their successors.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_basic_blocks),
    ("cfg", "Control flow graph of a function (JSON or DOT).",
     {"type": "object", "properties": {"target": {"type": "string"},
                                       "format": {"type": "string", "enum": ["json", "dot"]}},
      "required": ["target"]}, t_cfg),
    ("callgraph", "Call graph for a function or the whole binary (DOT).",
     {"type": "object", "properties": {"target": {"type": "string"}}}, t_callgraph),
    ("callgraph_json", "Whole-binary call graph as JSON (nodes + call edges).",
     {"type": "object", "properties": {
         "max_funcs": {"type": "integer", "default": 1000}}}, t_callgraph_json),
    ("callpaths", "Find call paths between two functions (backward BFS over call xrefs; unanalysed CRT glue can dead-end - use define_function on it first).",
     {"type": "object", "properties": {
         "from": {"type": "string", "description": "start function name or 0x address"},
         "to": {"type": "string", "description": "end function name or 0x address"},
         "max_length": {"type": "integer", "default": 6},
         "limit": {"type": "integer", "default": 10},
         "max_queries": {"type": "integer", "default": 1500}},
      "required": ["from", "to"]}, t_callpaths),
    ("types_load", "Load types from a C header file (`path`) or inline (`content`). Types are what improve decompiled C output.",
     {"type": "object", "properties": {
         "path": {"type": "string"}, "content": {"type": "string"},
         "timeout": {"type": "integer", "default": 120}}}, t_types_load),
    ("pdb_load", "Load Microsoft PDB symbols from `path`, or the sidecar next to the opened binary.",
     {"type": "object", "properties": {
         "path": {"type": "string"}, "timeout": {"type": "integer", "default": 120}}},
     t_pdb_load),
    ("signatures_scan", "Match FLIRT signatures from the bundled sigdb against the binary.",
     {"type": "object", "properties": {
         "sig": {"type": "string", "description": "explicit .sig file or directory"},
         "timeout_per_sig": {"type": "integer", "default": 60}}},
     t_signatures_scan),
    ("variables", "Local variables and arguments detected in a function.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_variables),

    ("decompile", "Decompile a function with the bundled Ghidra decompiler.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_decompile),
    ("decompile_json", "Structured rz-ghidra decompilation output.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_decompile_json),
    ("decompile_many", "Decompile several functions in one call.",
     {"type": "object", "properties": {
         "targets": {"type": "array", "items": {"type": "string"}},
         "limit": {"type": "integer", "default": 25}}, "required": ["targets"]},
     t_decompile_many),
    ("decompile_all", "Decompile every analysed function (can be slow).",
     {"type": "object", "properties": {"limit": {"type": "integer", "default": 400}}},
     t_decompile_all),
    ("disassemble", "Disassemble a function.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_disassemble),
    ("disassemble_range", "Disassemble N instructions at an address.",
     {"type": "object", "properties": {"addr": {"type": "string"},
                                       "count": {"type": "integer", "default": 16}},
      "required": ["addr"]}, t_disassemble_range),
    ("disassemble_json", "Instruction-level JSON for a function.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_disassemble_json),

    ("xrefs_to", "References to an address or function.",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_xrefs_to),
    ("xrefs_from", "Outgoing edges of a function (calls and branches).",
     {"type": "object", "properties": {"target": {"type": "string"}},
      "required": ["target"]}, t_xrefs_from),
    ("emulate", "EXPERIMENTAL: run ESIL emulation for N steps and dump registers.",
     {"type": "object", "properties": {
         "steps": {"type": "integer", "default": 8}, "addr": {"type": "string"}}},
     t_emulate),

    ("entrypoints", "Entry points of the binary.", {"type": "object", "properties": {}},
     t_entrypoints),
    ("sections", "Sections with permissions and addresses.",
     {"type": "object", "properties": {}}, t_sections),
    ("segments", "Segments (loader view).", {"type": "object", "properties": {}}, t_segments),
    ("imports", "Imported functions, filterable by name or library.",
     {"type": "object", "properties": {"filter": {"type": "string"},
                                       "limit": {"type": "integer", "default": 300}}},
     t_imports),
    ("exports", "Exported functions.", {"type": "object", "properties": {
        "limit": {"type": "integer", "default": 300}}}, t_exports),
    ("symbols", "Symbols, filterable by name.", {"type": "object", "properties": {
        "filter": {"type": "string"}, "limit": {"type": "integer", "default": 300}}},
     t_symbols),
    ("relocations", "Relocations.", {"type": "object", "properties": {}}, t_relocs),
    ("libraries", "Linked libraries.", {"type": "object", "properties": {}}, t_libraries),
    ("resources", "Embedded resources (icons, manifests, version info).",
     {"type": "object", "properties": {}}, t_resources),
    ("strings", "Extract strings with min length and substring filters.",
     {"type": "object", "properties": {
         "filter": {"type": "string"}, "min_len": {"type": "integer", "default": 5},
         "limit": {"type": "integer", "default": 200}}}, t_strings),

    ("types_list", "List known types (filterable).", {"type": "object", "properties": {
        "filter": {"type": "string"}, "limit": {"type": "integer", "default": 200}}},
     t_types_list),
    ("type_apply", "Apply a type to an address.",
     {"type": "object", "properties": {"addr": {"type": "string"}, "type": {"type": "string"}},
      "required": ["addr", "type"]}, t_type_apply),
    ("flags", "List flags (filterable).", {"type": "object", "properties": {
        "filter": {"type": "string"}, "limit": {"type": "integer", "default": 200}}}, t_flags),
    ("add_flag", "Name an address.", {"type": "object", "properties": {
        "name": {"type": "string"}, "addr": {"type": "string", "default": "$$"}},
      "required": ["name"]}, t_add_flag),
    ("remove_flag", "Delete a flag by name.",
     {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
     t_remove_flag),

    ("search", "Search bytes, strings, assembly, values, regex, wide strings, ROP or refs.",
     {"type": "object", "properties": {
         "pattern": {"type": "string"},
         "kind": {"type": "string",
                  "enum": ["bytes", "string", "asm", "value", "regex", "wide", "rop",
                           "refs", "crypto"]}}, "required": ["pattern"]}, t_search),
    ("rop", "Find ROP gadgets.",
     {"type": "object", "properties": {"limit": {"type": "integer", "default": 200}}}, t_rop),
    ("read_bytes", "Read raw bytes at an address (hex + ascii).",
     {"type": "object", "properties": {"addr": {"type": "string"},
                                       "size": {"type": "integer", "default": 64}},
      "required": ["addr"]}, t_read_bytes),
    ("write_bytes", "Patch bytes at an address.",
     {"type": "object", "properties": {"addr": {"type": "string"}, "hex": {"type": "string"}},
      "required": ["addr", "hex"]}, t_write_bytes),
    ("write_asm", "Assemble and write an instruction at an address.",
     {"type": "object", "properties": {"addr": {"type": "string"}, "asm": {"type": "string"}},
      "required": ["addr", "asm"]}, t_write_asm),
    ("hexdump", "Hex/words/string/data dump at an address.",
     {"type": "object", "properties": {
         "addr": {"type": "string"}, "size": {"type": "integer", "default": 64},
         "mode": {"type": "string", "enum": ["hex", "words", "quadwords", "disasm",
                                             "string"]}}, "required": ["addr"]}, t_hexdump),

    ("rename", "Rename a function.", {"type": "object", "properties": {
        "target": {"type": "string"}, "name": {"type": "string"}},
      "required": ["target", "name"]}, t_rename),
    ("rename_flag", "Rename a flag.", {"type": "object", "properties": {
        "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["old", "new"]},
     t_rename_flag),
    ("comment", "Set a comment at an address.", {"type": "object", "properties": {
        "target": {"type": "string"}, "text": {"type": "string"}},
      "required": ["target", "text"]}, t_comment),

    ("library_functions", "Library functions recognised by FLIRT signatures "
                          "(candidates to skip when reversing).",
     {"type": "object", "properties": {"limit": {"type": "integer", "default": 200}}},
     t_library_functions),
    ("yara_scan", "Scan the binary with a YARA rules file.",
     {"type": "object", "properties": {"rules": {"type": "string"}}, "required": ["rules"]},
     t_yara_scan),
    ("yara_folder", "Recursively scan a folder of YARA rules.",
     {"type": "object", "properties": {"folder": {"type": "string"}},
      "required": ["folder"]}, t_yara_folder),
    ("yara_matches", "List YARA matches from the last scan.",
     {"type": "object", "properties": {}}, t_yara_matches),

    ("project_save", "Save the current session as a rizin project.",
     {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
     t_project_save),
    ("project_open", "Load a rizin project.",
     {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
     t_project_open),
    ("diff_binaries", "Diff two binaries with the bundled rz-diff.",
     {"type": "object", "properties": {"left": {"type": "string"}, "right": {"type": "string"}},
      "required": ["left", "right"]}, t_diff_binaries),
    ("config_list", "List rizin configuration values.",
     {"type": "object", "properties": {"filter": {"type": "string"}}}, t_config_list),
    ("config_get", "Read one rizin configuration value.",
     {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]},
     t_config_get),
    ("config_set", "Set a rizin configuration value (e.g. ghidra.nl.else).",
     {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
      "required": ["key", "value"]}, t_config_set),

    ("debug_open", "Open the target under rizin's Windows debugger.",
     {"type": "object", "properties": {"path": {"type": "string"},
                                       "analysis": {"type": "string"}},
      "required": ["path"]}, t_debug_open),
    ("debug_status", "Debug session status and pid.", {"type": "object", "properties": {}},
     t_debug_status),
    ("debug_step", "Step N instructions and show registers.",
     {"type": "object", "properties": {"n": {"type": "integer", "default": 1}}}, t_debug_step),
    ("debug_continue", "Continue execution until the target stops.",
     {"type": "object", "properties": {"timeout": {"type": "number"}}}, t_debug_continue),
    ("debug_registers", "Show registers (optionally one register).",
     {"type": "object", "properties": {"register": {"type": "string"}}}, t_debug_registers),
    ("debug_backtrace", "Show the call stack.", {"type": "object", "properties": {}},
     t_debug_backtrace),
    ("debug_maps", "Show memory maps and loaded modules.",
     {"type": "object", "properties": {}}, t_debug_maps),
    ("debug_breakpoint", "Set a software breakpoint at an address.",
     {"type": "object", "properties": {"addr": {"type": "string"}}, "required": ["addr"]},
     t_debug_breakpoint),
    ("debug_breakpoints", "List breakpoints.", {"type": "object", "properties": {}},
     t_debug_breakpoints),
    ("debug_breakpoint_remove", "Remove a breakpoint.",
     {"type": "object", "properties": {"addr": {"type": "string"}}, "required": ["addr"]},
     t_debug_breakpoint_remove),
    ("debug_memory", "Dump memory of the debuggee.",
     {"type": "object", "properties": {"addr": {"type": "string"},
                                       "size": {"type": "integer", "default": 64}},
      "required": ["addr"]}, t_debug_memory),
    ("debug_write", "Write bytes into the debuggee's memory.",
     {"type": "object", "properties": {"addr": {"type": "string"}, "hex": {"type": "string"}},
      "required": ["addr", "hex"]}, t_debug_write),
    ("debug_detach", "Detach from (or kill) the debuggee.",
     {"type": "object", "properties": {"keep_alive": {"type": "boolean"},
                                       "kill": {"type": "boolean"}}}, t_debug_detach),

    ("run_command", "Escape hatch: run any single rizin command.",
     {"type": "object", "properties": {"command": {"type": "string"},
                                       "timeout": {"type": "number"}},
      "required": ["command"]}, t_run_command),
    ("run_commands", "Escape hatch: run several rizin commands in one session.",
     {"type": "object", "properties": {
         "commands": {"type": "array", "items": {"type": "string"}}},
      "required": ["commands"]}, t_run_commands),
]

TOOL_MAP = {name: (desc, schema, fn) for name, desc, schema, fn in TOOLS}


# --------------------------------------------------------------- prompts

PROMPTS = [
    {"name": "triage",
     "description": "Triage a binary: identify it, map its surface, and summarise risk.",
     "arguments": [{"name": "path", "description": "binary to triage", "required": True}]},
    {"name": "find_check",
     "description": "Locate an input check (license/password/flag) and invert it.",
     "arguments": [{"name": "path", "description": "target binary", "required": True}]},
    {"name": "explain_function",
     "description": "Explain one function from decompilation plus its callers.",
     "arguments": [{"name": "target", "description": "function name or address",
                    "required": True}]},
    {"name": "audit_memory_safety",
     "description": "Look for classic memory-safety bugs in the analysed binary.",
     "arguments": [{"name": "path", "description": "target binary", "required": True}]},
]


def prompt_text(name, args):
    path = args.get("path", "<binary>")
    target = args.get("target", "<function>")
    if name == "triage":
        return ("Triage %s with the butter tools and report:\n"
                "1. `open` then `info` + `hashes`: format, arch, bits, compiler, "
                "packed or not.\n"
                "2. `analyze` deep, then `functions` (sorted by size) and `sections`.\n"
                "3. `imports` + `strings` (filter for urls, paths, crypto, commands).\n"
                "4. `entrypoints`, then decompile `main`/`entry0` and its callees.\n"
                "5. Summarise: purpose, notable behaviour, suspicious indicators, and "
                "the three functions most worth reading next.\n"
                "State clearly what you could not determine." % path)
    if name == "find_check":
        return ("Find and invert the input check in %s:\n"
                "1. `open`, `analyze` deep, `strings` (look for prompts, formats, flags).\n"
                "2. `xrefs_to` the interesting strings to find the comparison site.\n"
                "3. `decompile` that function and its callees; identify the transform "
                "applied to the input.\n"
                "4. Invert the transform to recover the expected input, then verify by "
                "running the binary.\n"
                "Report the recovered value only if the binary confirms it, and note "
                "every decoy or dead branch you found." % path)
    if name == "explain_function":
        return ("Explain %s:\n"
                "1. `decompile` it, then `function_info`, `variables`, `basic_blocks`.\n"
                "2. `xrefs_to` for callers and `xrefs_from` for callees; decompile the "
                "two most important callees.\n"
                "3. Describe what it does, its arguments and return value, and any "
                "side effects or error paths, quoting only what the code supports."
                % target)
    if name == "audit_memory_safety":
        return ("Audit %s for memory-safety bugs:\n"
                "1. `open`, `analyze` max, `imports` (memcpy/strcpy/sprintf/alloca).\n"
                "2. `xrefs_to` each risky import, decompile the callers.\n"
                "3. For each finding give address, the code, the missing check, and "
                "how an attacker would reach it.\n"
                "Do not report a bug you cannot point at in the decompilation." % path)
    raise KeyError(name)


# --------------------------------------------------------------- resources

def resource_list():
    return [
        {"uri": "butter://session", "name": "Session state",
         "description": "Open file, analysis level and session health",
         "mimeType": "application/json"},
        {"uri": "butter://info", "name": "Binary info",
         "description": "Format, architecture and metadata of the open file",
         "mimeType": "application/json"},
        {"uri": "butter://functions", "name": "Function list",
         "description": "All analysed functions", "mimeType": "application/json"},
    ]


RESOURCE_TEMPLATES = [
    {"uriTemplate": "butter://decompiled/{function}",
     "name": "Decompiled function",
     "description": "Ghidra C for a named function or address",
     "mimeType": "text/plain"},
    {"uriTemplate": "butter://disassembly/{function}",
     "name": "Function disassembly",
     "description": "Disassembly of a named function or address",
     "mimeType": "text/plain"},
]


def resource_read(uri):
    if uri == "butter://session":
        return json.dumps(t_session({}), indent=2, default=str)
    if uri == "butter://info":
        return json.dumps(t_info({}), indent=2, default=str)
    if uri == "butter://functions":
        return json.dumps(t_functions({"limit": 2000}), indent=2, default=str)
    m = re.match(r"butter://(decompiled|disassembly)/(.+)$", uri)
    if m:
        kind, name = m.group(1), m.group(2)
        if kind == "decompiled":
            return run("pdg @ %s" % name, timeout=DECOMPILE_TIMEOUT)
        return run("pdf @ %s" % name)
    raise ToolError("unknown resource: %s" % uri)


# --------------------------------------------------------------- MCP plumbing

def list_tools():
    return [{"name": n, "description": d, "inputSchema": s} for n, d, s, _ in TOOLS]


def text_result(payload, is_error=False):
    body = payload if isinstance(payload, str) else \
        json.dumps(payload, indent=2, default=str)
    if len(body) > 400_000:
        body = body[:400_000] + "\n... [truncated for the model: %d more characters]" % (
            len(body) - 400_000)
    out = {"content": [{"type": "text", "text": truncate(body)}],
           "isError": is_error}
    if not is_error and isinstance(payload, dict):
        # Newer clients can consume the structured form directly.
        out["structuredContent"] = json.loads(json.dumps(payload, default=str))
    return out


def handle(msg):
    """Return a result object, or None for notifications."""
    method = msg.get("method")
    params = msg.get("params") or {}

    if method == "initialize":
        want = params.get("protocolVersion")
        version = want if want in PROTOCOL_VERSIONS else PROTOCOL_FALLBACK
        return {
            "protocolVersion": version,
            "capabilities": {
                "tools": {"listChanged": False},
                "prompts": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "logging": {},
                "completions": {},
            },
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION,
                           "title": "Butter reverse engineering"},
            "instructions": (
                "Drive Butter/rizin: `open` a binary, `analyze` deep, then `decompile`, "
                "`disassemble`, `xrefs_*`, `strings`, `search`, `read_bytes`. Analysis "
                "state is kept in a persistent rizin session, so it is paid once. Any "
                "rizin command is reachable through `run_command`."
            ),
        }

    if method in ("notifications/initialized", "initialized",
                  "notifications/cancelled", "notifications/progress",
                  "notifications/roots/list_changed"):
        return None

    if method == "ping":
        return {}

    if method == "logging/setLevel":
        STATE["log_level"] = params.get("level", "info")
        return {}

    if method == "tools/list":
        return {"tools": list_tools()}

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        entry = TOOL_MAP.get(name)
        if entry is None:
            return text_result("unknown tool: %s" % name, is_error=True)
        try:
            return text_result(entry[2](args))
        except ToolError as e:
            return text_result(str(e), is_error=True)
        except Exception as e:  # noqa: BLE001 - never kill the server on a tool bug
            log("tool %s failed: %r" % (name, e))
            return text_result("%s: %r" % (type(e).__name__, e), is_error=True)

    if method == "prompts/list":
        return {"prompts": PROMPTS}

    if method == "prompts/get":
        name = params.get("name")
        try:
            text = prompt_text(name, params.get("arguments") or {})
        except KeyError:
            return {"description": "unknown prompt", "messages": []}
        return {"description": next((p["description"] for p in PROMPTS
                                     if p["name"] == name), ""),
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}

    if method == "resources/list":
        return {"resources": resource_list()}

    if method == "resources/templates/list":
        return {"resourceTemplates": RESOURCE_TEMPLATES}

    if method == "resources/read":
        uri = params.get("uri")
        try:
            body = resource_read(uri)
        except ToolError as e:
            return {"contents": [{"uri": uri, "mimeType": "text/plain",
                                  "text": "error: %s" % e}]}
        mime = "application/json" if uri.endswith(("session", "info", "functions",
                                                   "metadata")) else "text/plain"
        return {"contents": [{"uri": uri, "mimeType": mime, "text": truncate(body)}]}

    if method == "completion/complete":
        ref = (params.get("ref") or {})
        prefix = (params.get("argument") or {}).get("value") or ""
        values = []
        if ref.get("type") == "ref/prompt":
            values = [p["name"] for p in PROMPTS if p["name"].startswith(prefix)]
        elif ref.get("type") == "ref/resource":
            values = [t["uriTemplate"] for t in RESOURCE_TEMPLATES
                      if t["uriTemplate"].startswith(prefix)]
        else:
            values = [n for n in TOOL_MAP if n.startswith(prefix)]
        return {"completion": {"values": values[:50], "total": len(values),
                               "hasMore": len(values) > 50}}

    raise KeyError(method)


def dispatch(line):
    """Turn one JSON-RPC line into a JSON-RPC response dict (or None)."""
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        log("ignoring non-JSON input: %r" % line[:200])
        return None

    if isinstance(msg, list):  # batch
        responses = [r for r in (dispatch_single(m) for m in msg) if r is not None]
        return responses or None

    return dispatch_single(msg)


def dispatch_single(msg):
    msg_id = msg.get("id")
    try:
        result = handle(msg)
    except KeyError as e:
        if msg_id is None:
            return None
        return {"jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32601, "message": "method not found: %s" % e}}
    except Exception as e:  # noqa: BLE001
        log("dispatch failed: %r" % e)
        if msg_id is None:
            return None
        return {"jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32603, "message": "%s: %r" % (type(e).__name__, e)}}

    if msg_id is None or result is None:
        return None
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def serve_stdio():
    log("starting on stdio, rizin=%s" % STATE["rizin"])
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = dispatch(line)
        if response is None:
            continue
        for item in (response if isinstance(response, list) else [response]):
            sys.stdout.write(json.dumps(item) + "\n")
        sys.stdout.flush()
    with _lock:
        for key in ("session", "debug"):
            if STATE[key]:
                STATE[key].stop()


def serve_http(host, port, path="/mcp"):
    """Streamable-HTTP transport: one JSON-RPC request per POST."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "%s/%s" % (SERVER_NAME, SERVER_VERSION)

        def _json(self, code, payload):
            body = json.dumps(payload).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # health check + simple SSE-less discovery
            if self.path in ("/health", "/healthz"):
                return self._json(200, {"status": "ok", "server": SERVER_NAME,
                                        "version": SERVER_VERSION,
                                        "file": STATE["file"],
                                        "tools": len(TOOLS)})
            return self._json(200, {"server": SERVER_NAME, "version": SERVER_VERSION,
                                    "endpoint": path,
                                    "transport": "streamable-http",
                                    "tools": len(TOOLS)})

        def do_POST(self):
            if self.path not in (path, path + "/"):
                return self._json(404, {"error": "post to %s" % path})
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8", "replace")
            with _lock:
                try:
                    response = dispatch(raw)
                except Exception as e:  # noqa: BLE001
                    log("http dispatch failed: %r" % e)
                    return self._json(500, {"jsonrpc": "2.0",
                                            "error": {"code": -32603,
                                                      "message": str(e)}})
            if response is None:
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self._json(200, response)

        def log_message(self, fmt, *args):
            if LOG_LEVEL:
                log("http %s" % (fmt % args))

    server = ThreadingHTTPServer((host, port), Handler)
    log("starting on http://%s:%d%s (rizin=%s)" % (host, port, path, STATE["rizin"]))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        with _lock:
            for key in ("session", "debug"):
                if STATE[key]:
                    STATE[key].stop()


def main(argv=None):
    parser = argparse.ArgumentParser(description="butter-mcp: MCP server for Butter/rizin")
    parser.add_argument("--rizin", help="path to rizin(.exe)")
    parser.add_argument("--file", help="open this binary on startup")
    parser.add_argument("--analysis", choices=["basic", "deep", "max"],
                        help="run auto-analysis on startup (with --file)")
    parser.add_argument("--http", metavar="HOST:PORT",
                        help="serve streamable HTTP instead of stdio")
    parser.add_argument("--path", default="/mcp", help="HTTP endpoint path")
    parser.add_argument("--no-log", action="store_true", help="silence stderr logging")
    args = parser.parse_args(argv)

    global LOG_LEVEL  # noqa: PLW0603
    if args.no_log:
        LOG_LEVEL = False

    STATE["rizin"] = find_rizin(args.rizin)
    if args.file:
        t_open({"path": args.file})
        if args.analysis:
            ensure_analysis(args.analysis)

    if args.http:
        host, _, port = args.http.partition(":")
        serve_http(host or "127.0.0.1", int(port or 8765), args.path)
        return 0
    serve_stdio()
    return 0


if __name__ == "__main__":
    sys.exit(main())
