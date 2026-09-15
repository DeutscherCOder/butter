# IDA Pro vs Butter — strengths, honestly compared

Goal: not to "compete" rhetorically but to *beat where beatable*, be silent where not,
and be strongest where IDA cannot follow. Date: 2026-09-15; IDA reference is the 9.2–9.4
line (public release notes).

## Where IDA is genuinely strong (respect, and no denial)

- **Hex-Rays maturity**: 20+ years of microcode optimization; output quality on weird
  code (hand-written asm, obfuscation, exotic conventions) is still the bar.
- **Loader/processor breadth**: Dyld shared caches, SVE2/SME, Hexagon, MCore, Swift ABI —
  enormous surface built over decades.
- **The ecosystem**: IDAPython plugins exist for everything; teams already have .idb/.iil
  workflows and the new Git-based Teams sharing.
- **Microcode viewer** (9.2): visibility into optimization levels that no open tool matches.
- **Polish**: decades of UI refinement, database robustness on huge files.

## Where Butter is strong *today* (measured or structural)

| Strength | Why it beats IDA |
|---|---|
| **Price & licensing** | GPL-3 + MIT, zero cost, zero license servers, zero dongles |
| **Agent-native (MCP)** | 79 tools over a persistent session, stdio+HTTP — an AI agent drives the *whole* tool. IDA added MCP via third-party plugins; it is not a design center |
| **Open pipeline end-to-end** | every byte from disassembly to decompiled C is inspectable and patchable (we literally patch the decompiler at install time — try that with Hex-Rays) |
| **Portable by construction** | one folder, no installer, no registry, runs from a USB stick |
| **Fresh engine** | rizin dev tip + Ghidra 12.1.3 (newest release) + Sleigh specs for ~150 processors |
| **Existing-plugin compatibility** | upstream Cutter plugins (C++/Python) load unchanged — an ecosystem IDA cannot tap |
| **Honest benchmarks in-repo** | `docs/BENCHMARKS.md` reproduces every number on public binaries |

## Where Butter will beat IDA (the plan, grounded in the research docs)

1. **The AI-in-the-loop advantage** — IDA sells a tool; Butter ships a tool *plus* the
   protocol for agents to name, type, and cross-reference everything automatically
   (`docs/GPU-RESEARCH.md` Phase B / pcode research Phase 1). A human+agent in Butter
   should out-pace a human alone in IDA on typical binaries even while Hex-Rays prints
   prettier C for the hardest 5%.
2. **GPU stock-clock throughput** — FLIRT/YARA/byte-sweep at driver-default speeds on the
   user's existing NVIDIA/AMD card; IDA has no GPU story.
3. **Speed of iteration** — open repo: a fix lands in a fork the same day (our rz-ghidra
   stack-arg fix already does what upstream took months to even acknowledge). No waiting
   on a vendor release cycle.
4. **Parallel analysis** — rizin's single-core analysis (upstream issue #4765, 7–22 min on
   a huge binary) becomes multi-core via the pcode sidecar; IDA already parallelizes, we
   close that specific gap with our own architecture, cacheable this time.

## Where we deliberately do not fight (yet)

- Microcode-level output quality on pathological obfuscation — Hex-Rays wins today; we
  track Ghidra releases and improve incrementally (and our patch system compounds).
- Exotic loader breadth (Dyld shared cache workflows etc.) — Sleigh/rizin cover a lot, not
  everything; be honest, chip away by user demand.

**Net positioning:** IDA = best single-human craft tool, closed and priced accordingly.
Butter = the open, portable, agent-first platform that gets *faster to value* on every
binary a typical analyst or AI agent touches — and compounds weekly because it is open.
