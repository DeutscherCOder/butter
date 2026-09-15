#!/usr/bin/env python3
"""Crack the Butter crackme -- entirely through the butter-mcp server.

This is the AI's seat: it talks to `mcp/butter_mcp.py` over JSON-RPC on stdio
exactly like an agent would, and never touches the source of the challenge or
the plaintext password. Everything below is recovered from the binary.

Method
------
1. `open` + `analyze deep`, then `decompile main`.
2. Collect every data address main mentions. The real payload is the one that
   decrypts to the CKR1 magic, so the address is *verified*, not assumed.
3. Recover the key. The key rounds in `derive_key()` were constant-folded by the
   compiler, but the junk table it folds away is still in .rdata, and its first
   element is 0x9E3779B9 -- a recognizable magic (TEA delta / XxHash golden
   ratio). Scan for it with the `search` tool, read the 16 words, replay the LCG.
   Also try key ^ 0xDEADBEEF, which is what the anti-debug path folds in.
4. Undo the payload cipher (rotate/add/xor chain, both directions invertible).
5. Parse the payload header, then *symbolically interpret* the bytecode VM: ops
   push input[i], constants and secret[i] onto a stack, and CMPNE becomes an
   equality constraint. Invert each constraint expression to recover input[i].
6. Verify: re-run the VM interpreter over the recovered password, then execute
   the real crackme.exe and require "Access granted".

Run:  python crackme/solve.py
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "mcp"))

from test_client import Client  # noqa: E402  (local MCP client)

CRACKME = os.path.join(HERE, "crackme.exe")
BLOB_READ = 4096          # over-read is harmless: the cipher decodes as a prefix
MAGIC = b"CKR1"
CIPHER_INIT = 0x5A
DEADBEEF = 0xDEADBEEF
JUNK_MAGIC = "b979379e"   # first g_junk[] entry, 0x9E3779B9, little endian on disk
LCG_MUL, LCG_ADD = 1103515245, 12345


def say(step, msg=""):
    print("\n[*] %s" % step)
    if msg:
        print(msg)


# --------------------------------------------------------------- primitives

def rotl8(v, n):
    n &= 7
    return v & 0xFF if n == 0 else ((v << n) | (v >> (8 - n))) & 0xFF


def rotr8(v, n):
    n &= 7
    return v & 0xFF if n == 0 else ((v >> n) | (v << (8 - n))) & 0xFF


def derive_key(junk):
    """Replay the LCG the binary folds away at compile time."""
    k = 0x9E3779B9
    for word in junk:
        k = (k * LCG_MUL + LCG_ADD) & 0xFFFFFFFF
        k ^= word
        k ^= k >> 7
    return k


def decrypt(blob, key):
    """Inverse of decrypt_blob() in crackme.c."""
    kb = [(key >> (8 * i)) & 0xFF for i in range(4)]
    out = bytearray()
    prev = CIPHER_INIT
    for i, c in enumerate(blob):
        c = rotl8(c, 3)
        c = (c - ((prev * 3 + i) & 0xFF)) & 0xFF
        c ^= kb[i & 3]
        out.append(c)
        prev = c
    return bytes(out)


# ------------------------------------------------------- symbolic VM solving
#
# Expressions are tuples: ('var', i) ('const', v) ('secret', i)
#                        ('xor', a, b) ('rotl', a, b) ('add', a, b) ('sub', a, b)

OP_NOP, OP_PUSH_ARG, OP_PUSH_IMM = 0x00, 0x11, 0x2A
OP_XOR, OP_ROTL, OP_SECRET, OP_CMPNE = 0x37, 0x4C, 0x55, 0x68
OP_LEN, OP_ACCEPT, OP_HALT = 0x73, 0x8E, 0xF0
VM_STACK = 8


def vm_run(code, secret, data):
    """Faithful interpreter -- used to verify the solution, mirroring vm_run().

    Returns True only when the VM accepts `data`.
    """
    stack, pc, accepted = [], 0, False
    push = stack.append
    while pc < len(code):
        op = code[pc]
        pc += 1
        if op == OP_NOP:
            continue
        elif op == OP_LEN:
            if pc >= len(code) or len(data) != code[pc]:
                return False
            pc += 1
        elif op in (OP_PUSH_ARG, OP_SECRET, OP_PUSH_IMM):
            if pc >= len(code) or len(stack) >= VM_STACK:
                return False
            if op == OP_PUSH_ARG:
                push(data[code[pc]] if code[pc] < len(data) else -1)
            elif op == OP_SECRET:
                push(secret[code[pc]] if code[pc] < len(secret) else -1)
            else:
                push(code[pc])
            pc += 1
        elif op in (OP_XOR, OP_ROTL):
            if len(stack) < 2:
                return False
            b = stack.pop()
            a = stack.pop()
            push((a ^ b) & 0xFF if op == OP_XOR else rotl8(a & 0xFF, b & 0xFF))
        elif op == OP_CMPNE:
            if len(stack) < 2:
                return False
            b = stack.pop()
            a = stack.pop()
            if a != b:
                return False
        elif op == OP_ACCEPT:
            accepted = True
        elif op == OP_HALT:
            break
        else:
            return False
    return accepted


def as_value(expr, secret):
    if expr[0] == "const":
        return expr[1]
    if expr[0] == "secret":
        return secret[expr[1]]
    return None


def solve_expr(expr, target, solution, secret):
    """Invert `expr == target` for the single input byte it depends on."""
    kind = expr[0]
    if kind == "var":
        solution[expr[1]] = target & 0xFF
        return
    if kind == "const":
        if expr[1] != target:
            raise ValueError("contradictory constant %r != %r" % (expr[1], target))
        return
    if kind in ("xor", "rotl", "add", "sub"):
        a, b = expr[1], expr[2]
        cst = as_value(b, secret)
        invertible_left = cst is not None
        cst_a = as_value(a, secret)
        invertible_right = cst_a is not None
        if kind == "xor":
            if invertible_left:
                return solve_expr(a, (target ^ cst) & 0xFF, solution, secret)
            if invertible_right:
                return solve_expr(b, (target ^ cst_a) & 0xFF, solution, secret)
        elif kind == "rotl":
            if invertible_left:
                return solve_expr(a, rotr8(target & 0xFF, cst), solution, secret)
        elif kind == "add":
            if invertible_left:
                return solve_expr(a, (target - cst) & 0xFF, solution, secret)
            if invertible_right:
                return solve_expr(b, (target - cst_a) & 0xFF, solution, secret)
        elif kind == "sub":
            if invertible_left:
                return solve_expr(a, (target + cst) & 0xFF, solution, secret)
            if invertible_right:
                return solve_expr(b, (cst_a - target) & 0xFF, solution, secret)
    raise ValueError("cannot invert %r" % (expr,))


def solve_vm(code, secret):
    """Symbolically walk the bytecode and recover the accepted input."""
    stack, pc, acc = [], 0, False
    length = None
    solution = {}
    known = {OP_NOP, OP_PUSH_ARG, OP_PUSH_IMM, OP_XOR, OP_ROTL,
             OP_SECRET, OP_CMPNE, OP_LEN, OP_ACCEPT, OP_HALT}

    while pc < len(code):
        op = code[pc]
        pc += 1
        if op not in known:
            raise ValueError("unknown opcode 0x%02X at %d" % (op, pc - 1))
        if op == OP_NOP:
            continue
        if op == OP_LEN:
            length = code[pc]
            pc += 1
        elif op == OP_PUSH_ARG:
            stack.append(("var", code[pc]))
            pc += 1
        elif op == OP_SECRET:
            stack.append(("secret", code[pc]))
            pc += 1
        elif op == OP_PUSH_IMM:
            stack.append(("const", code[pc]))
            pc += 1
        elif op in (OP_XOR, OP_ROTL):
            b, a = stack.pop(), stack.pop()
            stack.append(("xor" if op == OP_XOR else "rotl", a, b))
        elif op == OP_CMPNE:
            b, a = stack.pop(), stack.pop()
            target = as_value(b, secret) if as_value(a, secret) is None \
                else as_value(a, secret)
            lhs = a if as_value(a, secret) is None else b
            solve_expr(lhs, target, solution, secret)
        elif op == OP_ACCEPT:
            acc = True
        elif op == OP_HALT:
            break

    if not acc:
        raise ValueError("bytecode never reaches ACCEPT")
    if length is None:
        raise ValueError("bytecode has no LEN op")
    return bytes(solution[i] for i in range(length)), length


# ------------------------------------------------------------------ MCP glue

class Session:
    """Thin wrapper over the MCP client so the crack reads like a transcript."""

    def __init__(self, binary):
        self.c = Client()
        self.c.send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}})
        self.c.send("notifications/initialized", notify=True)
        self.binary = binary

    def open(self):
        return self.c.call("open", {"path": self.binary})

    def analyze(self, level="deep"):
        return self.c.call("analyze", {"level": level})

    def decompile(self, target="main"):
        return self.c.call("decompile", {"target": target})

    def search(self, pattern):
        return self.c.call("search", {"pattern": pattern})

    def read(self, addr, size):
        r = self.c.call("read_bytes", {"addr": hex(addr), "size": size})
        raw = re.sub(r"\s+", "", r.get("hex", ""))
        if not raw:
            return b""
        return bytes.fromhex(raw)

    def close(self):
        self.c.close()


def candidates_from_decompile(code):
    """Every plausible data address the decompiler mentioned, deduplicated."""
    addrs = {int(m, 16) for m in re.findall(r"0x1[0-9a-fA-F]{8,}", code)}
    return sorted(addrs)


def candidates_from_search(hits):
    """All addresses a `search` result reported (a magic constant may recur)."""
    text = hits.get("hits", "") if isinstance(hits, dict) else str(hits)
    return sorted({int(m, 16) for m in re.findall(r"0x1[0-9a-fA-F]{6,}", text)})


def crack():
    s = Session(CRACKME)

    info = s.open()
    say("open %s" % os.path.basename(CRACKME),
        "  size=%s  sha256=%s  arch=%s" % (info.get("size"), info.get("sha256", "")[:16],
                                          info.get("file_info", {}).get("arch")))
    res = s.analyze("deep")
    print("  analyze deep -> %s functions" % res.get("functions"))

    dec = s.decompile("main")
    main_c = dec["code"]
    say("decompile main", "  %d chars of Ghidra C recovered" % len(main_c))

    # ---- key: find the folded-away junk table and replay the LCG
    hits = s.search(JUNK_MAGIC)
    junk_addrs = candidates_from_search(hits)
    if not junk_addrs:
        print("[!] junk table not found: %s" % hits)
        return 1

    # The payload address is never assumed: whatever address in main decrypts to
    # the CKR1 magic under a key derived from a junk-table candidate *is* the
    # payload. Ambiguity in either is resolved by that joint check.
    blobs = {addr: s.read(addr, BLOB_READ) for addr in candidates_from_decompile(main_c)}
    payload = None
    for junk_addr in junk_addrs:
        raw = s.read(junk_addr, 64)
        if len(raw) < 64:
            continue
        junk = [int.from_bytes(raw[i:i + 4], "little") for i in range(0, 64, 4)]
        key = derive_key(junk)
        for addr, blob in blobs.items():
            if len(blob) < 16:
                continue
            for k in (key, key ^ DEADBEEF):
                plain = decrypt(blob, k)
                if plain[:4] == MAGIC:
                    payload, used_key, payload_addr = plain, k, addr
                    break
            if payload:
                break
        if payload:
            break
    if payload is None:
        print("[!] no (junk table, payload) candidate pair produced the CKR1 magic")
        return 1
    say("key recovery",
        "  junk table @ %s, %d bytes scanned (unreferenced: the compiler folded\n"
        "  the key rounds away, only the table survived in .rdata)\n"
        "  replayed LCG over 16 words -> key = 0x%08X" % (hex(junk_addr), len(raw), key))
    say("payload recovery",
        "  blob @ %s, %d bytes, decrypted with 0x%08X%s -> magic CKR1"
        % (hex(payload_addr), len(blob), used_key,
           " (anti-debug variant)" if used_key != key else ""))

    # ---- parse the payload header
    slen = payload[4] | (payload[5] << 8)
    clen = payload[6] | (payload[7] << 8)
    secret = payload[8:8 + slen]
    code = payload[8 + slen:8 + slen + clen]
    say("payload header",
        "  secret %d bytes @ 0x08, bytecode %d bytes @ 0x%02X" % (slen, clen, 8 + slen))

    # ---- invert the bytecode VM
    password, length = solve_vm(code, secret)
    say("symbolic VM inversion",
        "  %d CMPNE constraints over %d opcodes -> %d input bytes recovered"
        % (len(password), len(code), length))

    # ---- verify with our own interpreter, then with the real binary
    ok = vm_run(code, secret, password)
    print("  re-run VM over recovered input: %s" % ("ACCEPT" if ok else "REJECT"))
    proc = subprocess.run([CRACKME, password.decode("latin-1")],
                          capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    s.close()

    say("result",
        "  password : %s\n  crackme  : %s (exit %d)"
        % (password.decode("latin-1"), out or "<no output>", proc.returncode))
    return 0 if ("Access granted" in out and ok) else 1


if __name__ == "__main__":
    sys.exit(crack())
