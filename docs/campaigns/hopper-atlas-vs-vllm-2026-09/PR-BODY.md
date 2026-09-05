# Two NVIDIA datacentre targets: Hopper (sm_90a) and B200 (sm_100a)

Draft PR body for the branch. Sections follow CONTRIBUTING.md's required set —
What, Why, Benchmarks, Authorship — with the evidence and the gaps stated
separately, because a precise negative result is worth more than a confident
guess.

## What

Atlas targeted one NVIDIA architecture: GB10 (`sm_121f`). This adds two more
and the machinery that keeps them honest.

**`kernels/hopper/` (H100/H200, SM 9.0, `sm_90a`) and `kernels/b200/`
(B200/GB200, SM 10.0, `sm_100a`).** Neither ships a kernel of its own. Each is
218 relative symlinks into `kernels/gb10/` — the 181-entry `common/` plus the
five P0 models' `nvfp4/` directories — with a real `MODEL.toml` per model,
because sampling and behaviour are checkpoint properties that must stay
editable per hardware. This is the mechanism `kernels/strix/` already used,
applied whole rather than curated: these are NVIDIA targets driven by the same
nvcc, and the gb10 kernels are written to an SM80-class instruction floor
(`mma.sync.m16n8k16`, `cp.async.cg`, no TMA, no `__CUDA_ARCH__` gating).

**A GPU architecture preflight.** Atlas compiles one SM architecture per build
— no fatbin, no multi-`-gencode` — so a binary and a GPU can simply disagree,
and until now nothing checked. The driver's answer was
`CUDA_ERROR_NO_BINARY_FOR_GPU` raised inside `cuModuleLoadData`, naming neither
the arch in the binary nor the card in the box. `atlas_core::arch` encodes the
three PTX compatibility rules, `spark-runtime` applies them before the backend
is constructed, and the message names both sides and the fix.

**A compile gate that needs no silicon.** `scripts/hopper_ptx_gate.sh` runs
`nvcc --ptx` then `ptxas -v` for a hardware set's whole kernel list on any CUDA
host, and writes a JSON ledger plus a markdown summary with per-model pass/fail
counts, the first error of every failure, and the worst register/spill numbers.
It self-tests first, always, and refuses to report if its own failure path did
not execute.

**Bench plumbing:** `hopper`, `b200` and `gb200` registered as box classes;
GPU-name → box-class mapping for the new SKUs; a Hopper A/B driver skeleton and
results template; and a PRD with the vLLM control recipes.

## Why

Three things had to be true before a single number could be measured on rented
Hopper or Blackwell time, and none of them were.

**The kernels had to exist for the architecture.** Nothing in CI compiled a
line of CUDA for anything but `sm_121f`, and the question "does this kernel
exist on sm_90a" cannot be answered by reading it. The PTX gate answers it for
871 kernels in about four minutes, on a box we already own, and found the one
kernel that does not — before anyone rented an H100 to discover it.

**The wrong image had to fail loudly.** Two published images that look
identical from the outside, whose failure mode is silent until boot, is a
support ticket per operator. It is also the failure the campaign itself was
most likely to hit first.

**A run had to be scoreable.** `--hardware h100` was refused as an unknown box
class, which reads to an operator as a typo rather than as "go measure it".

## Benchmarks

No performance numbers. This branch measures whether kernels COMPILE, and says so
everywhere it reports.

Measured on `spark1` (DGX Spark, GB10, aarch64), CUDA 13.0.88 / nvcc V13.0.88,
2026-09-05, `--jobs 4`. Receipts are committed under
`docs/campaigns/hopper-atlas-vs-vllm-2026-09/receipts/`.

The two tables below are the **first-pass** run, which is what found the one
failure. "Both targets are now 173/173" further down is the same gate after
that failure was addressed; the tables are left as measured rather than
restated.

### Hopper — `sm_90a`

| model | kernels | pass | fail |
|---|---:|---:|---:|
| deepseek-v4-flash | 185 | 185 | 0 |
| nemotron-3-nano-30b-a3b | 171 | 171 | 0 |
| nemotron-super-120b-a12b | 171 | 171 | 0 |
| qwen3-next-80b-a3b | 171 | 171 | 0 |
| qwen3.6-35b-a3b | 173 | 172 | **1** |
| **total** | **871** | **870** | **1** |

`nemotron-super-120b-a12b` also passes under `--strict` (`--Werror
all-warnings`, which the real build always adds): 171/171.

### B200 — `sm_100a`

| model | kernels | pass | fail |
|---|---:|---:|---:|
| deepseek-v4-flash | 185 | 185 | 0 |
| nemotron-3-nano-30b-a3b | 171 | 171 | 0 |
| nemotron-super-120b-a12b | 171 | 171 | 0 |
| qwen3-next-80b-a3b | 171 | 171 | 0 |
| qwen3.6-35b-a3b | 173 | 172 | **1** |
| **total** | **871** | **870** | **1** |

`nemotron-super-120b-a12b` passes `--strict` (171/171); `qwen3.6-35b-a3b` under
`--strict` is 172/173, failing on the same kernel as the non-strict run.

### The one failure, and why it is two different failures

`kernels/gb10/qwen3.6-35b-a3b/nvfp4/moe_w4a16_grouped_gemm.cu`, both times, for
different reasons:

```
sm_90a   Instruction 'cvt with .e2m1x2' not supported on .target 'sm_90a'
sm_100a  Instruction 'mma with block scale' not supported on .target 'sm_100a'
```

Hopper has no FP4 conversion at all. Datacentre Blackwell has the conversion
and lacks the **warp-level** block-scaled MMA, which is a consumer-Blackwell
instruction — on sm_100a that work goes through `tcgen05.mma` against tensor
memory instead. The two Blackwell architectures are siblings, not a ladder:

| instruction | sm_90a | sm_100a | sm_120a / sm_121 |
|---|---|---|---|
| `cvt.rn.satfinite.e2m1x2.f32` | ✗ | ✓ | ✓ |
| `mma.sync ... .kind::mxf4nvf4.block_scale` | ✗ | ✗ | ✓ |
| `redux.sync.max.abs.f32` | ✗ | ✓ | ✗ |

The going-in expectation was that this kernel would pass on sm_100a because
`.e2m1x2` is a Blackwell instruction. It does not.

### Both targets are now 173/173

Only the **W4A4 tail** of that file needs those instructions — FP4 weights AND
FP4 activations, two entry points: `moe_w4a16_fused_gate_up_t_k64_fp4` and
`moe_w4a16_down_t_k64_fp4`. Everything above them is W4A16 (4-bit weights
dequantised to BF16, plain `mma.sync`) and assembles at the SM80 floor. So the
tail sits inside `#ifndef ATLAS_NO_WARP_BLOCKSCALE_MMA`, and both hardware
targets define that macro in HARDWARE.toml's new `[build] extra_nvcc_flags` —
one define for both, because neither has the warp-level form and an arch
comparison would get one of them wrong.

GB10's PTX for the file is byte-identical across the change:
`sha256 137b44c2762d1996c9a1551a906a692cb067edae0b4ee4beee9098d303de4b3a`
(`nvcc --ptx -arch=sm_121f -O3 --fmad=false -DTQ_PLUS_SIGNS`, Spark 1, CUDA
13.0.88, before and after). The two absent entry points are declared in each
target's `MODEL.toml` `[expected_absent.moe_w4a16]` with that architecture's
ptxas error as the reason, so the boot audit calls them an expected absence
instead of refusing to serve. Both are `try_kernel` lookups fired only behind a
default-off opt-in (`ATLAS_HOLO_MOE_GATEUP_FP4` / `ATLAS_HOLO_MOE_DOWN_FP4`):
what is lost on Hopper and B200 is the FP4 escape hatch, and the FP8 path
serves.

Receipts, both `--strict`:
`receipts/ptx_gate_hopper_qwen36_w4a4guard_2026-09-05.*` (173/173, sm_90a) and
`receipts/ptx_gate_b200_qwen36_w4a4guard_2026-09-05.*` (173/173, sm_100a).

This removes a compile-time blocker; it does not make either target an NVFP4
target. The real fix is still different per architecture — Hopper an Sm90 MoE
grouped GEMM, B200 the same math through tcgen05 — and neither is done here.
The other four P0 targets were already complete on both.

### Register pressure

`ptxas -v` numbers, not timings. 574 of 871 kernels differ in max registers or
spill bytes between the two arches; 32 sit at the 255-register ceiling and 42
spill on each. Total spill is 12,056 bytes at sm_90a against 19,400 at sm_100a,
and it moves in both directions:

| kernel | sm_90a regs/spill | sm_100a regs/spill |
|---|---:|---:|
| `gated_delta_rule_persistent` | 255 / 124 | 255 / **2256** |
| `gated_delta_rule_fla` | 255 / 324 | 254 / **0** |
| `gated_delta_rule_wy3_resident` | 255 / 204 | 255 / 16 |
| `gated_delta_rule` | 255 / 1552 | 255 / 1396 |
| `w4a16_gemm` | 168 / 624 | 168 / 492 |

`gated_delta_rule_persistent` — an 18x spill increase in the persistent GDN
decode kernel — is the first thing to profile when silicon is available. A
pass/fail gate cannot see it. Spill bytes are a hint, not a measurement; none
of this has been timed.

## Authorship

**AI-authored, in full.** Every line in this branch — Rust, CUDA fixture,
shell, YAML, markdown, and every commit message — was written by an AI agent
(Claude). There is **no hand-written code** in this PR, so per CONTRIBUTING.md
there is nothing to defend.

The human contributions were direction and access: scoping the campaign,
choosing the P0 model set and the two architectures, and providing the DGX
Spark the gate ran on. Every measurement quoted above was produced by running
the committed script on that box, and the ledgers it emitted are committed
unmodified.

## What is NOT verified

The honest list. Everything here is a real gap, not a hedge.

- **No Hopper or Blackwell silicon was touched.** No H100, H200, B200 or GB200
  was involved at any point. `nvcc --ptx` and `ptxas` are cross-compilers: they
  answer whether an instruction exists for a target architecture, and nothing
  else. Nothing in this branch says these kernels produce correct numbers or
  run at any particular speed.
- **`[expected_absent]` is unharvested on both new targets.** Those tables are
  produced by `spark serve --check-kernels` on the real device. Both trees
  carry GB10's harvest verbatim, and every copied `MODEL.toml` opens by saying
  so. Until they are re-harvested, a kernel genuinely missing on Hopper or B200
  can read as an expected absence.
- **The arch preflight has never rejected a real GPU.** Its rules are pinned
  against the NVIDIA CUDA C++ Programming Guide's PTX-compatibility section and
  its verdicts are unit-tested, but no driver has been asked to confirm one.
- **NCCL intra-node is untested.** Every multi-GPU Atlas run to date is 2
  ranks, one GPU per node, over RoCE, with NVLS and GDR disabled and Ring
  pinned — GB10 pessimisations. No NVLink intra-node run exists, and an 8×GPU
  node is the normal shape of the hardware this targets.
- **The NVFP4 CUTLASS wrappers are not ported.** `crates/spark-runtime/cuda/
  cutlass_nvfp4_gemm.cu` is gated on `CUTLASS_ARCH_MMA_SM120_SUPPORTED ||
  CUTLASS_ARCH_MMA_SM121_SUPPORTED` and compiles to nothing for both sm_90a and
  sm_100a. Hopper would need an Sm90 block-scaled path; B200 needs
  `cutlass::arch::Sm100` collectives behind `CUTLASS_ARCH_MMA_SM100_SUPPORTED`.
- **The `.benchmarks/` perf-gate records are invalidated by this branch.**
  `PERF_PATHS` contains bare `crates` and `kernels`, and this branch changes
  both, so every committed record now reads as not covering the tip. **A GB10
  re-measure is required before merge** — the records must be re-run at the
  final commit, on the box, and committed from a clean tree. No record here was
  produced by this branch, and no threshold was touched.
- **The `compile-b200` CI job has never run.** It mirrors `compile-hopper` line
  for line apart from `ATLAS_TARGET_HW`; the equivalent build was run by hand on
  the DGX (below), but GitHub Actions has not executed the job itself.

## Test evidence

Full gate on Linux (`spark1`, aarch64), `ATLAS_SKIP_BUILD=1
CUDARC_CUDA_VERSION=13000`, `-j 6`:

| check | result |
|---|---|
| `cargo fmt --all -- --check` | pass |
| `cargo clippy --workspace --tests` | pass, 0 warnings |
| `cargo test --workspace --no-fail-fast` | **5552 passed, 0 failed, 82 ignored** across 80 suites |
| `cargo doc --workspace --no-deps` | pass, 0 warnings |
| `python3 scripts/check_kernel_shadows.py` | `kernel shadow structure: OK` |
| `typos` (macOS) | pass |
| `scripts/check-license-headers.sh` (macOS) | 2851 files checked, 0 invalid |

Real (non-stub) kernel builds on nvcc, proving `build.rs` end to end for both
new targets:

```
ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL=nemotron-super-120b-a12b \
  cargo build --release -p atlas-kernels     171 kernels, 2m29s
ATLAS_TARGET_HW=b200   ATLAS_TARGET_MODEL=nemotron-super-120b-a12b \
  cargo build --release -p atlas-kernels     171 kernels, 18s
```

The b200 build's generated registry records
`KernelTarget { arch: "sm_100", ... }` alongside `ptx_arch: "sm_100a"` — the
two readings the preflight fix depends on, confirmed against a real build
rather than a stub.

Every commit on the branch carries its own red→green line. The ones worth
naming here:

- `the_preflight_judges_the_verbatim_arch_not_the_stripped_base_sm` — the
  defect this branch fixes: the preflight was reading the suffix-stripped base
  SM, so `sm_90a` kernels would have PASSED on a CC 10.0 device.
- `every_kernel_hardware_dir_is_registered` — `hopper` was in the kernel tree
  and not in the box-class registry.
- `every_hardware_set_in_the_tree_is_guarded` — `b200` was outside both halves
  of the kernel-structure gate.
- `every_target_hint_names_a_hardware_set_that_exists` — drove creating
  `kernels/b200/` after `target_hint` promised it.
- `ldb_kernels_keep_their_dialect_specific_bounds` and
  `every_real_target_resolves_a_nonempty_source_set` — two hand-maintained
  inventories that the new hardware sets made stale.

Three tests were reported earlier in the campaign as pre-existing failures
(`cli::bench_selfstart::tests::a_baseline_declared_serve_pin_…` and two
`tui::bench_variants::tests::…`). They **do not fail** on Linux: a clean
`567b5eb` worktree on the same box runs spark-server's 2441 tests green, and
the branch tip runs 2446 green. Whatever produced those failures was not the
base commit.

## Follow-ups

1. **Re-measure the `.benchmarks/` gates on GB10** at the final commit and
   commit the records from a clean tree. Required before merge.
2. **An Sm90 and an Sm100 MoE grouped GEMM** for qwen3.6-35b-a3b. Two separate
   pieces of work, not one — see the failure analysis above.
3. **Harvest `[expected_absent]`** with `spark serve --check-kernels` on the
   first H100/H200 and B200 that becomes available, and replace GB10's tables
   in both trees.
4. **Profile `gated_delta_rule_persistent` on sm_100a.** 2256 spill bytes where
   sm_90a has 124.
5. **Port the NVFP4 CUTLASS wrappers** to `cutlass::arch::Sm100`, and decide
   whether Hopper gets an Sm90 block-scaled path or stays FP8/BF16-only.
6. **An NVLink intra-node NCCL run**, and unwinding the GB10 pessimisations in
   `scripts/start-ep2.sh` for non-GB10 hardware.
7. **B300 / GB300 (sm_103a)** is a separate target, deliberately not started:
   `target_hint` returns `None` for CC 10.3 and the PTX gate refuses that arch
   because it has no negative self-test fixture for it.
