# GPU research — using AMD & NVIDIA GPUs on Windows, the stable way

Date: 2026-09-15. Desktop research (AMD/NVIDIA official documentation), no code yet.
**Policy up front: no overclocking, ever.** Every projection below assumes *stock clocks*,
stock power limits, and driver-managed boost within factory spec. The goal is throughput
that is stable for hours, reproducible across runs, and safe on the "simple PC" our users
actually have.

## How the stacks actually work on Windows

| | NVIDIA | AMD |
|---|---|---|
| Platform | CUDA Toolkit 13.x (mature, official Windows support incl. new ARM preview) | HIP SDK for Windows (official subset of ROCm for Windows, supports consumer RDNA cards) |
| Programming model | CUDA C/C++ kernels via `nvcc` | HIP C++ — nearly CUDA-identical syntax, compiled by `hipcc` (or compiled *as* CUDA via_HIPIFY tooling) |
| Runtime model | kernels queued to streams; GPU does long stall-free batch work best | same; HIP SDK ships hipBLAS/hipFFT etc. on Windows |
| Driver stability | WDDM; heavy compute contexts are stable; TCC only on pro cards | WDDM; HIP SDK supported on Windows 10/11 per official system-requirements page |
| Debug/profiling | Nsight Systems / Compute, `cuda-gdb` | Radeon GPU Profiler / ROCm tooling subset |

Practical takeaway for us: **one HIP/CUDA-style kernel source can serve both vendors**
(HIP compiles for NVIDIA via hipCUDA path; or keep two thin backends). Dispatch, batching
and memory staging are the only architecture-specific bits.

## What RE workloads are actually GPU-shaped

Honest triage first — not everything belongs on a GPU:

1. **FLIRT / signature matching** — thousands of independent hash comparisons over fixed
   patterns. Embarrassingly parallel. The bundled sigdb is 48 MB; a GPU match sweep is the
   clearest early win. *(strong candidate)*
2. **Byte-pattern search (YARA-class) & mutation scans** — already parallel in spirit
   (YARA has a scanner model); large-binary sweeps benefit directly. *(strong)*
3. **String/constant mining, entropy sliding windows** — pure data-parallel maps over the
   file image. *(easy win, modest impact)*
4. **Disassembly itself** — inherently control-flow dependent (length is context-sensitive);
   GPU-unfriendly. NOT a candidate. *(avoid — this is where tools overpromise)*
5. **Emulation (ESIL/pcode)** — serial semantics, stateful. Only batch scenarios (fuzzing
   input sweeps) qualify, later. *(later)*
6. **The decompiler** — a big solver, but with serialized fixed-point phases; Ghidra runs
   it per-function on a pool. GPU gains would be inside specific numeric kernels only.
   *(research only — no promises)*

## "Stable speed, no overclocking" — the engineering rules

- **Never touch clocks/voltage/power limits.** Use the driver's own boost behavior; it is
  factory-validated. Our determinism tool is *software*: fixed batch sizes, fixed queue
  depths, and pinned clocks *within spec* are unnecessary if we measure medians.
- **Measure honestly**: report median + p95 over N runs after a warm-up run; never quote a
  best-case single run. Timestamp + driver version + GPU name recorded per benchmark.
- **Watch thermal/power**: sustained loads must stay under stock power limits (they will,
  by definition) — but log package power and temperature so a laptop GPU throttling under
  sustained load is visible in the results instead of silently skewing them.
- **Batch size > clock speed**: on both vendors, throughput comes from keeping thousands
  of threads busy with coalesced memory access — our matching/search kernels are exactly
  that shape.
- **WDDM caveats**: kernel-launch overhead under WDDM is real; amortize with fewer,
  bigger batches (work queues), or CUDA per-thread streams on NVIDIA. Do not launch
  microsecond kernels in a loop.
- **Fallback always**: the GPU path is an accelerator — CPU path must remain complete and
  default. A box with no supported GPU runs Butter exactly as today, same results.

## Integration plan for Butter (no code yet)

1. **Phase A**: `butter-mcp` grows a `gpu_status` tool (detect vendor, driver, memory,
   supported ops) + `search_bytes`/`flirt_scan` GPU backends behind the existing tool
   signatures. CPU fallback identical semantics.
2. **Phase B**: YARA sweep + entropy/constant mining on GPU; results cached like analysis.
3. **Phase C (research)**: batch function-level pcode facts (from the sidecar research)
   pushed through GPU for numeric-only passes; evaluate honestly before promising anything.

Success metric: same results, same licensing (no vendor SDK redistribution —
documented install, like CUDA's EULA requires), strictly stock clocks, CPU fallback intact.
