# butter-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) server that gives any AI client
the full power of the Butter / rizin backend: analyse a binary, decompile with the bundled
Ghidra decompiler, disassemble, follow xrefs, inspect sections / imports / exports /
symbols / relocations / strings, search bytes and code, read and write memory, apply types,
scan with YARA, drive the Windows debugger, diff two binaries, and reach anything else
through a raw rizin escape hatch.

Standard library only — nothing to `pip install`. It drives the `rizin.exe` that already
ships next to Butter, so no GUI, no plugin and no project file are required.

```
    AI client  --JSON-RPC (stdio or HTTP)-->  butter_mcp.py  --pipes-->  rizin.exe
```

Full setup instructions for every client are in [`../SETUP.md`](../SETUP.md).

## Design

* **One persistent rizin process.** Analysis runs once per opened file and stays in that
  process, so a session pays the ~3s of `aaa` a single time instead of on every tool call.
  Measured on the bundled crackme: a decompile is ~0.16s warm versus ~3.2s when every call
  respawns rizin.
* **Marker-delimited I/O.** Commands are written to rizin's stdin and each one is followed
  by `echo <unique-marker>`. `echo` is used deliberately: rizin refuses to run the `?e` /
  `?v` evaluator commands when the input comes from a pipe.
* **Timeouts with recovery.** Every command has a deadline; on a timeout the session is
  killed, restarted and the error says so, rather than silently hanging the agent.
* **Structured first, honest always.** JSON-producing tools parse rizin's JSON; when a
  command is rejected, the tool returns what rizin actually said instead of reporting
  success. Output is never truncated mid-JSON (a 650 KB `aflj` would break parsing), only
  after tools project the fields they return.
* **Noise filtering.** ANSI escapes and rizin's esil `Cannot peek memory` spam are dropped.

## Transports

```bash
python mcp/butter_mcp.py                                    # stdio (default)
python mcp/butter_mcp.py --file target.exe --analysis deep   # pre-open a binary
python mcp/butter_mcp.py --http 127.0.0.1:8765               # streamable HTTP
```

HTTP: `POST /mcp` takes one JSON-RPC request (batches are supported), `GET /health`
reports server state. Environment: `BUTTER_RIZIN` (path to rizin), `BUTTER_MCP_LOG=0`
to silence stderr logging.

## Protocol surface

* `initialize` negotiates the protocol revision (`2025-06-18`, `2025-03-26`, `2024-11-05`)
  and advertises tools, prompts, resources, logging and completions.
* `tools/list`, `tools/call` (results carry both text content and `structuredContent`).
* `prompts/list`, `prompts/get` — `triage`, `find_check`, `explain_function`,
  `audit_memory_safety`.
* `resources/list`, `resources/read`, `resources/templates/list` —
  `butter://session`, `butter://info`, `butter://functions`,
  `butter://decompiled/{function}`, `butter://disassembly/{function}`.
* `ping`, `logging/setLevel`, `completion/complete`, notification handling.

## Tools (74)

| Group | Tools |
|---|---|
| Session | `open` `close` `session` `info` `hashes` |
| Analysis | `analyze` `functions` `function_info` `define_function` `undefine_function` `basic_blocks` `cfg` `callgraph` `callgraph_json` `variables` `library_functions` |
| Decompilation | `decompile` `decompile_json` `decompile_many` `decompile_all` |
| Disassembly | `disassemble` `disassemble_range` `disassemble_json` |
| Xrefs | `xrefs_to` `xrefs_from` `emulate` (experimental) |
| Structure | `entrypoints` `sections` `segments` `imports` `exports` `symbols` `relocations` `libraries` `resources` `strings` |
| Types & naming | `types_list` `type_apply` `flags` `add_flag` `remove_flag` `rename` `rename_flag` `comment` |
| Search | `search` `rop` |
| Memory | `read_bytes` `write_bytes` `write_asm` `hexdump` |
| Signatures | `library_functions` `yara_scan` `yara_folder` `yara_matches` |
| Projects & diff | `project_save` `project_open` `diff_binaries` |
| Config | `config_list` `config_get` `config_set` |
| Debugging | `debug_open` `debug_status` `debug_step` `debug_continue` `debug_registers` `debug_backtrace` `debug_maps` `debug_breakpoint` `debug_breakpoints` `debug_breakpoint_remove` `debug_memory` `debug_write` `debug_detach` |
| Escape hatches | `run_command` `run_commands` |

`run_command` is the safety net: anything rizin can do is reachable even if it is not
wrapped (`aaa`, `axt`, `/r`, `aar`, `axg`, `afr`, `iSS`, `z`, plugin commands, …).

## Verify

```bash
python mcp/test_client.py                              # protocol round trip
python mcp/dump-decompile.py <binary> <function> [out] # decompile one function
python crackme/solve.py                                # solves the crackme via this server
```

## Debugging caveats

Stepping, registers, memory and backtraces work against Windows targets. Software
breakpoints at absolute addresses can miss because rizin's Windows module list is
incomplete under ASLR — step to the address instead. ESIL cannot emulate Windows API
calls, so `emulate` is marked experimental and time-boxed.
