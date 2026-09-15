# Clutter setup (Windows 11)

Short version first, details below. Also see the root [README.md](README.md) and
[`mcp/README.md`](mcp/README.md) (the MCP server).

## Already built — just run it

If you have a built copy, the folder is the whole app: portable Qt, rizin, the Ghidra
decompiler, FLIRT signatures and an embedded Python 3.12. Nothing is installed system-wide.

```
clutter-dist\clutter.exe
```

| What | Path |
|---|---|
| GUI | `clutter-dist\clutter.exe` |
| CLI engine | `clutter-dist\rizin.exe` |
| Decompile from the CLI | `clutter-dist\rizin.exe -A -q -c "s entry0; pdg" target.exe` |
| The test target | `crackme\crackme.exe` |
| MCP server | `mcp\clutter_mcp.py` |

```bat
clutter-dist\clutter.exe crackme\crackme.exe     :: open the crackme in the GUI
crackme\crackme.exe "ClutterDecompilersGoBrrr_2026"   :: try the password
```

## Build from source

Needs **Visual Studio 2022/2026 with C++** and **Python 3.12** on PATH. First time only:

```bat
bash scripts/fetch_deps.sh                       :: portable Qt 6.11 + PySide6 -> cutter-deps\
python -m venv .tools\venv
.tools\venv\Scripts\python -m pip install meson ninja
```

Then, whenever:

```bat
tools\build-clutter.bat full                     :: configure + build + install (~15-30 min cold)
```

Script modes: `configure` (CMake only) · `reconfigure` (wipe cache) · `build` ·
`install` · `full`. If the rizin step fails: `tools\build-rizin.bat 8`, then re-run.
To rebuild only the decompiler after a Ghidra upgrade: `tools\build-ghidra.bat`.

## Plug it into an AI

Add to your client's MCP config (Claude Desktop, Cursor, Cline, Continue, Windsurf, …):

```json
{ "mcpServers": { "clutter": {
    "command": "python",
    "args": ["C:/path/to/clutter/mcp/clutter_mcp.py"] } } }
```

Pre-open a file so the agent doesn't waste a call:

```json
"args": ["C:/path/to/clutter/mcp/clutter_mcp.py",
         "--file", "C:/path/to/target.exe", "--analysis", "deep"]
```

No processes allowed in your client? Use HTTP instead:

```bat
python mcp\clutter_mcp.py --http 127.0.0.1:8765  :: POST JSON-RPC to /mcp
```

## Checks

```bat
python mcp\test_client.py        :: MCP round trip
python crackme\solve.py          :: cracks the crackme through the MCP
bash tools\test-decompiler.sh    :: decompiler smoke test
python tools\analysis-bench.py   :: analysis profile comparison
```

## Versions in this build

| Piece | Version |
|---|---|
| rizin engine | **0.10.0, upstream `dev` tip** (`4efde3ccce`, v0.7.1-1730) |
| Ghidra decompiler | **12.1.3** — the newest Ghidra *release*, engine + all Sleigh specs |
| rz-ghidra bridge | `dev` (`26b6130`) + this repo's Ghidra 12.1.3 / stack-arg fixes |
| Qt / PySide6 | 6.11 portable, project-local |

## If something is off

| Symptom | Fix |
|---|---|
| `rizin not found` | Set `CLUTTER_RIZIN` to `clutter-dist\rizin.exe` |
| A tool times out | Session restarts itself; use `analyze` level=basic, or raise `timeout` |
| Breakpoint never hits | rizin's Windows module list is incomplete under ASLR — `debug_step` instead |
| `?e` fails in `run_command` | rizin blocks `?`-commands over a pipe; use `echo` |
| Calling rizin by hand in Git Bash | `export MSYS_NO_PATHCONV=1` |
| No Python console in the GUI | Re-run `tools\build-clutter.bat install` (needs `python312*` next to `clutter.exe`) |
| Meson symbol-extractor crash (0xC000070A) | `tools\build-rizin.bat 8`, then re-run the build |
