# crackme

A deliberately hostile Windows target, built to be cracked with Butter's Ghidra decompiler and
driven entirely through [`../mcp`](../mcp) by an agent.

**Spoiler warning.** The password and flag are printed at the bottom of this file.

## What it protects itself with

| Layer | What it does |
|---|---|
| Encrypted payload | The password check is not code: it is a bytecode VM program, stored encrypted in `.rdata` (`169` lines of generated data) |
| Folded key | The blob key is derived by a 16-round LCG over a junk table. MSVC constant-folds the whole derivation, so no key-derivation code exists at runtime — only the table survives, unreferenced, in `.rdata` |
| Runtime-derived magic | The payload magic `CKR1` never appears as a string or as a plain immediate; it is assembled from constants and xored at runtime |
| Anti-debug that does not exit | `IsDebuggerPresent`, `CheckRemoteDebuggerPresent`, `PEB.BeingDebugged` and a `QueryPerformanceCounter` timing check do not terminate. They fold `0xDEADBEEF` into the key, so under a debugger the payload decrypts to garbage and the check just fails |
| Decoy checker | A second, unreachable password checker with fake passwords and a fake flag, plus dead code behind an opaque predicate, junk hash-constant table and garbage strings like `CLUTTER{str1ngs_ar3_f0r_b3g1nn3rs}` |
| No symbols | Built `/MT /O2 /GS-` with no PDB, so `main` is the only meaningful name |

Only `crackme.exe` is distributable — `gen_blob.py` holds the plaintext password.

## Build

```bat
crackme\build.bat
```

Regenerates `blob_data.h` from `gen_blob.py`, then compiles with VS 2026. Behaviour:

```bat
crackme.exe "ButterDecompilersGoBrrr_2026"   ->  Access granted. flag: ...
crackme.exe hunter2                           ->  Access denied.
crackme.exe "CLUTTER{str1ngs_ar3_f0r_b3g1nn3rs}"  ->  Access denied.   (decoy)
```

## Solve it

```bash
python crackme/solve.py
```

It never reads `crackme.c` or `gen_blob.py` — every fact below comes out of the binary through
the MCP server:

1. `open` + `analyze deep` + `decompile main`.
2. Collect every data address the decompiled `main` mentions. **The payload address is verified,
   not assumed:** whatever address decrypts to the `CKR1` magic *is* the payload.
3. Recover the key. The key rounds were folded away, but the junk table is still in `.rdata` and
   its first word is `0x9E3779B9` — a recognisable magic (TEA delta / XxHash golden ratio). The
   `search` tool finds it, `read_bytes` pulls the 16 words, and the LCG is replayed. The solver
   also tries `key ^ 0xDEADBEEF`, the anti-debug variant.
4. Invert the payload cipher. Rotate-add-xor is invertible in both directions and the chain only
   looks backwards, so over-reading is harmless: `decrypt(blob)[:n]` is valid for any `n`.
5. Parse the payload header (`CKR1`, `u16` secret length, `u16` bytecode length).
6. **Symbolically interpret the VM.** Ops push `input[i]`, constants and `secret[i]` onto a stack;
   `CMPNE` becomes an equality constraint whose expression tree is inverted
   (`rotl8(input[i] ^ mask, rot) == secret[i]` → `input[i] = rotr8(secret[i], rot) ^ mask`).
7. Verify twice: re-run a faithful interpreter over the recovered password, then run the real
   `crackme.exe` and require `Access granted`.

```
[*] open crackme.exe
  size=151040  sha256=ab336ad2bc6088d5
  analyze deep -> 423 functions

[*] decompile main
  8639 chars of Ghidra C recovered

[*] key recovery
  junk table @ 0x1400184b0, 64 bytes scanned (unreferenced: the compiler folded
  the key rounds away, only the table survived in .rdata)
  replayed LCG over 16 words -> key = 0x885AC135

[*] payload recovery
  blob @ 0x140018320, 4096 bytes, decrypted with 0x885AC135 -> magic CKR1

[*] payload header
  secret 29 bytes @ 0x08, bytecode 352 bytes @ 0x25

[*] symbolic VM inversion
  29 CMPNE constraints over 352 opcodes -> 29 input bytes recovered
  re-run VM over recovered input: ACCEPT

[*] result
  password : ClutterDecompilersGoBrrr_2026
  crackme  : Access granted. flag: CLUTTER{v1rtu4l_m4ch1n3s_4nd_p4ck3rs} (exit 0)
```

Independently of the solver: `key = 0x885AC135` shows up in the decompiled `main` as the four
folded immediates `0x35 0xc1 0x5a 0x88`, which is a nice cross-check that the LCG replay is right.

`analysis/main.decompiled.c` is the raw Ghidra output for `main`, kept as the artifact the
solver worked from.

## Where it is still crackable (by design)

* The bytecode is a straight-line program with no branches, so the constraints are independent and
  invert in one pass. A VM with data-dependent control flow, or a table-driven dispatch, would need
  real symbolic execution (angr, Triton, Z3).
* The cipher is a symmetric stream, invertible from the first byte, so the payload address can be
  identified by trial decryption. A keyed hash of the whole payload, or compression/encryption with
  a header MAC, would remove that.
* Anti-debug failures only corrupt the payload. A shared-vs-debugger-independent key (e.g. derived
  from `cpuid`/`rdtsc` mixed into the check itself) would make the "just patch the branch" route
  harder, but nothing here defeats a kernel debugger or ScyllaHide.

## Spoilers

```
password : ClutterDecompilersGoBrrr_2026
flag     : CLUTTER{v1rtu4l_m4ch1n3s_4nd_p4ck3rs}
```
