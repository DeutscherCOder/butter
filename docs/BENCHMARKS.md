# Butter benchmarks — measured, not promised

Date: 2026-09-15. Machine: consumer Windows 11 desktop (this PC), stock everything.
Engine: `butter-dist/rizin.exe` built from this repo (rizin dev tip `4efde3ccce`,
Ghidra decompiler 12.1.3 + patches). Method: `tools/analysis-bench.py` logic —
one fresh rizin process per metric, ANSI-stripped output, wall-clock per profile.

## Targets (public, official binaries)

| Target | What | Size |
|---|---|---|
| `crackme/crackme.exe` | our shipped test target (MSVC /MT /O2) | 151 KB |
| `tools/testprobe/probe.exe` | locally built probe (source in repo) | 741 KB |
| `putty.exe` | **official PuTTY 0.83-ish w64 release** from `the.earth.li` (sha256 prefix `d01fdb5aae8f1125`) — a real, public, security-audited binary | 1,706 KB |

## Results — auto-analysis profiles (CPU)

| target | profile | functions found | pdg anchor lines | wall time |
|---|---|---|---|---|
| crackme | baseline `aaa` | 423 | 209 | 3.1 s |
| crackme | tuned profile + `aaa` | **614 (+45%)** | 209 (same) | 3.2 s |
| crackme | profile + `aav`+`aap` | 614 | 209 | 3.5 s |
| probe | baseline | 1,009 | 77 | 5.9 s |
| probe | tuned profile | **3,351 (+232%)** | 70 | 9.1 s |
| probe | profile + `aav`+`aap` | 3,384 | 70 | 9.3 s |
| putty.exe | baseline | 1,953 | 83 | 10.0 s |
| putty.exe | tuned profile | **3,173 (+62%)** | 81 | 12.7 s |

The tuned profile (`analysis.hasnext/jmp.indir/jmp.tblmax=2048/ptrdepth=4/...`,
see `tools/analysis-bench.py`) finds **45–232% more functions** for +0.1–3.4 s.

**Reading the numbers honestly:** the decompiled *anchor function* output stays
essentially identical across profiles — more discovery ≠ better per-function C.
Per-function quality comes from types, signatures, and calling conventions (the next
benchmarks below), which is exactly where our stack-arg fix and type-loading work aim.

## What this means

- On a "simple PC", full `aaa` on a real 1.7 MB application costs ~10 s; the tuned
  profile buys much better *coverage of the binary* for +27% time.
- Warm-session MCP calls are ~0.16 s vs ~3.2 s cold (`mcp/README.md`) — the persistent
  session is the biggest perceived-speed feature already shipped.
- GPU acceleration targets (see `docs/GPU-RESEARCH.md`) are the byte-sweep workloads
  (FLIRT/YARA/search), where wall time on multi-MB binaries is expected to drop by an
  order of magnitude — those benchmarks will be added here once the GPU backends land.

## Reproduce

```bat
python tools\analysis-bench.py crackme\crackme.exe tools\testprobe\probe.exe putty.exe
python mcp\test_client.py        :: MCP round trip (includes timing printout)
python crackme\solve.py          :: end-to-end crack through the MCP
```
