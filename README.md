# Butter

**A fast, portable, agent-friendly reverse engineering platform for Windows — built on
[rizin](https://github.com/rizinorg/rizin) + the [Ghidra decompiler](https://github.com/NationalSecurityAgency/ghidra),
forked from [Butter](https://github.com/rizinorg/cutter).**

Butter = the Butter GUI you know, renamed and hardened, shipped as a **zero-install
portable folder**, wired so that **AI agents can drive the whole thing over MCP**.

---

## Why Butter exists

| | Stock Butter | Butter |
|---|---|---|
| Install | build it yourself, or installer | one folder — `butter-dist\butter.exe`, nothing installed system-wide |
| Decompiler | rz-ghidra as-is | newest Ghidra release (12.1.3) + Sleigh specs + a real output fix (see below) |
| Engine | rizin release | rizin upstream `dev` tip |
| Plugins | Butter ABI | **Butter plugins still load unchanged** (full compat layer) |
| AI | — | 74-tool MCP server over a persistent rizin session |
| Provenance | — | everything reproducible from this repo, no manual patching |

## What's inside

```
butter/                       (this repo)
├─ src/ cmake/ dist/ scripts/ docs/ docker/    the Butter fork of Butter
│    ├── dist/patch_rz_ghidra.cmake    decompiler fix, applied at install time
│    ├── dist/patch_jsdec.cmake        jsdec compat fix, applied at install time
│    └── src/compat/                   upstream-plugin compatibility layer
├─ mcp/                 butter-mcp: 74 MCP tools over a persistent rizin session
├─ crackme/             a hostile crackme + the AI solver that defeats it (end-to-end test)
├─ tools\build-butter.bat    configure / build / install — the one build entry point
├─ tools/               build & maintenance scripts (portable, no hardcoded paths)
├─ COPYING              GPL-3 (the fork keeps Butter's license)
```

## Quick start (Windows 11, ~30 min cold build)

```bat
git clone --recurse-submodules https://github.com/DeutscherCOder/butter.git
cd butter

bash scripts/fetch_deps.sh              :: portable Qt 6.11 + PySide6 into .\cutter-deps
python -m venv .tools\venv
.tools\venv\Scripts\python -m pip install meson ninja

tools\build-butter.bat full            :: configure + build + install (~15-30 min)
butter-dist\butter.exe                :: done. the folder IS the app
```

Details, HTTP mode, troubleshooting: **[SETUP.md](SETUP.md)**.

## Decompile without the GUI

```bat
butter-dist\rizin.exe -A -q -c "s entry0; pdg" target.exe
```

## Let an AI drive it

Add to any MCP client (Claude Desktop, Cursor, Cline, Continue, Windsurf, …):

```json
{ "mcpServers": { "butter": {
    "command": "python",
    "args": ["C:/path/to/butter/mcp/butter_mcp.py"] } } }
```

One persistent rizin process: analysis is paid once (~3 s), every later tool call is
milliseconds. No processes in your client? `python mcp\butter_mcp.py --http 127.0.0.1:8765`.

Prove the whole stack end-to-end:

```bat
python crackme\solve.py      :: the AI cracks a hostile crackme through the MCP
```

## The decompiler fix worth knowing about

Upstream rz-ghidra **silently drops** function arguments whose storage doesn't fit the
architecture's ProtoModel:

```
// WARNING: [rz-ghidra] Removing arg arg_78dch because it doesn't fit into ProtoModel
```

On stack-pointer frames those "arguments" are usually just locals — so Butter demotes
them to locals instead of losing them (`dist/patch_rz_ghidra.cmake`, applied at install
time, idempotent, fails loudly if upstream drifts). On the bundled crackme, `main` used to
lose three variables.

## Deep dives

* [docs/GPU-RESEARCH.md](docs/GPU-RESEARCH.md) — using AMD/NVIDIA GPUs on Windows the stable way (stock clocks, no OC, ever)
* [docs/BENCHMARKS.md](docs/BENCHMARKS.md) — measured numbers on public official binaries (incl. PuTTY)
* [docs/IDA-vs-BUTTER.md](docs/IDA-vs-BUTTER.md) — honest strengths comparison vs IDA Pro 9.x

## Checks

```bat
python mcp\test_client.py            :: MCP protocol + tools round trip
python crackme\solve.py              :: end-to-end crack through the MCP
bash tools\test-decompiler.sh        :: decompiler smoke test + Sleigh language set
python tools\analysis-bench.py       :: what analysis profiles actually recover
python tools\ghidra-delta.py         :: how far upstream Ghidra has moved
```

## Versions in this build

| Piece | Version |
|---|---|
| rizin engine | upstream `dev` tip (`4efde3ccce`, v0.7.1-1730) |
| Ghidra decompiler | **12.1.3** (newest release) — engine + all Sleigh specs |
| rz-ghidra bridge | `dev` (`26b6130`) + this repo's stack-arg fix |
| Qt / PySide6 | 6.11 portable, project-local |

## Known rough edges

* Meson's MSVC symbol-extraction step can crash intermittently — `tools\build-rizin.bat 8`
  builds the bundled rizin with bounded parallelism and retries; produced binaries are fine.
* rizin's Windows debugger cannot always place absolute breakpoints under ASLR; stepping,
  registers, memory and backtraces work.
* The decompiler tracks the newest Ghidra **release** (12.1.3), not master.
* `MSYS_NO_PATHCONV=1` needed when calling rizin by hand from Git Bash.
* Translations are off by default (`-DBUTTER_ENABLE_TRANSLATIONS=ON` to re-enable) — the
  translation sources live in a separate upstream repo.

## Licenses

* The Butter fork of Butter: **GPL-3** (see `COPYING`) — as upstream.
* `mcp/`, `crackme/`, `tools/` helper scripts: **MIT** (see `LICENSE.md`).

## Acknowledgements

Standing on the shoulders of [rizin](https://github.com/rizinorg/rizin),
[Butter](https://github.com/rizinorg/cutter), [Ghidra](https://github.com/NationalSecurityAgency/ghidra),
[rz-ghidra](https://github.com/rizinorg/ghidra) and the whole Sleigh/FLIRT ecosystems.
