# Architecture preflight — kernels vs the GPU in the box

Atlas compiles **one** SM architecture per build. `kernels/<hw>/HARDWARE.toml`
`[hardware].arch` picks it (`sm_121f` for gb10, `sm_90a` for hopper); there is
no fatbin and no multi-`-gencode`. A binary and a GPU can therefore simply
disagree, and until this slice nothing checked.

Adding a Hopper target makes that a shipping concern rather than a theoretical
one: two published images now exist, they look identical from the outside, and
the failure mode for picking the wrong one is silent until boot.

## What the operator used to see

The driver rejects the load inside `cuModuleLoadData`, with a
`CUDA_ERROR_NO_BINARY_FOR_GPU` / `CUDA_ERROR_UNSUPPORTED_PTX_VERSION`-class
status. That error names neither the architecture in the binary nor the card in
the machine, so the first actionable datum is a support ticket.

## What runs now

`init_gpu_backend` (`crates/spark-server/src/main_modules/serve_phases/preflight.rs`)
calls `spark_runtime::cuda_backend::arch_preflight::preflight_device_arch`
**before** constructing the backend — that is, before any module load:

1. bind the process CUDA host on the serve ordinal (a `OnceLock`; the backend
   then reuses the same context);
2. read `CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR` (75) and `_MINOR` (76)
   through the `cuDeviceGetAttribute` FFI that already existed for the SM-count
   query — no new symbols;
3. apply `atlas_core::arch::ptx_arch_runs_on_device` to
   `(ptx_set.ptx_arch, device_cc)`;
4. on success log at info, e.g. `device CC 9.0, kernels built for sm_90a`;
   on failure abort the serve with the message below.

A build that recorded **no** architecture — the `ATLAS_SKIP_BUILD=1` stub
registry compiles nothing — is warned and skipped. A check with no input has no
opinion, and passing it would let a stub build claim hardware compatibility it
never tested.

### It judges the VERBATIM arch, not the base SM

`TargetPtxSet` carries two readings of one `kernels/<hw>/HARDWARE.toml`
`[hardware].arch` declaration, and the preflight may only be handed one of
them:

| field | hopper | what it is |
|---|---|---|
| `target.arch` (`KernelTarget.arch`) | `sm_90` | the base SM, feature suffix stripped — an IDENTITY: the key `crates/atlas-core/src/target.rs`'s constants, the gate baselines and every committed record use |
| `ptx_arch` | `sm_90a` | the declaration verbatim — what nvcc was handed |

The suffix **is** the compatibility rule, so stripping it changes the verdict
rather than shortening it. `sm_90a` judged as `sm_90` is plain PTX, which the
forward-compat rule runs on any CC >= 9.0 — so Hopper-only kernels would PASS
this preflight on a B200 (CC 10.0) or a GB10 (12.1) and then die inside
`cuModuleLoadData`, which is the failure the preflight was added to replace.
`spark_runtime::cuda_backend::arch_preflight::preflight_arch` owns that pick so
no call site repeats it, and `--check-kernels` reports `compiled_arch` from the
same field.

## The message

Verbatim, for the gb10 image booted on an H100:

```
kernels compiled for sm_121f cannot run on this GPU (compute capability 9.0):
family-specific PTX (sm_121f) runs only on compute capability 12.1 or later
within the 12.x family; fix: rebuild with ATLAS_TARGET_HW=hopper
(kernels/hopper/HARDWARE.toml arch must match this GPU) or use the image built
for this GPU
```

(one line in the log; wrapped here). The reverse case names `gb10`, and a
compute capability Atlas ships nothing for says `no shipped target matches
compute capability <X.Y>` instead of naming a target that does not exist.

`--check-kernels` reports the same two facts in its machine-readable line:
`compiled_arch` (verbatim `[hardware].arch`, i.e. `ptx_arch`) and `device_cc`
(`"12.1"`, or `null` when nothing can be asked). The pre-existing `arch` field is retained,
carrying the same value under the name it shipped with.

## Compatibility matrix

The rules, and the oracle for every test in
`crates/atlas-core/src/arch_tests.rs`, are the NVIDIA CUDA C++ Programming
Guide: *Application Compatibility → PTX Compatibility*, plus the
family-specific architecture features added in CUDA 12.9.

| suffix | rule | example |
|---|---|---|
| none (`sm_XY`) | runs on any device with CC >= X.Y (JIT forward-compat) | `sm_80` on 12.1 ✅ |
| `a` (`sm_XYa`) | runs ONLY on CC == X.Y — never forward-compatible | `sm_90a` on 10.0 ❌ |
| `f` (`sm_XYf`) | same major family, CC >= X.Y | `sm_121f` on 12.0 ❌ |

Cases pinned by test:

| compiled | device CC | verdict | why |
|---|---|---|---|
| `sm_121f` | 12.1 | ✅ | the shipped gb10 pairing |
| `sm_121f` | 12.0 | ❌ | family, but below the compiled CC |
| `sm_121f` | 10.0 | ❌ | different major family |
| `sm_121f` | 9.0 | ❌ | the gb10 image on an H100 |
| `sm_90a` | 9.0 | ✅ | the shipped hopper pairing |
| `sm_90a` | 10.0 | ❌ | `a` never travels forward |
| `sm_90a` | 12.1 | ❌ | `a` never travels forward |
| `sm_90` | 9.0 | ✅ | plain PTX |
| `sm_90` | 12.1 | ✅ | plain PTX, JIT forward |
| `sm_80` | 9.0 | ✅ | plain PTX, JIT forward |
| `sm_121` | 9.0 | ❌ | forward only, never backward |
| `gfx1151`, `metal3.1` | any | ✅ (not judged) | not an NVIDIA SM arch |

The last row is a decision, not an oversight: a CUDA compute capability says
nothing about a SCALE/HIP or Metal target, so `parse_sm_arch` returns `None`
and the check passes. `None` is the marker a caller tests for "not NVIDIA".

## Target hints

`atlas_core::arch::target_hint` maps a device CC to the `kernels/<hw>/` target
that serves it. Keep it in step with what `kernels/` actually ships.

| device CC | `ATLAS_TARGET_HW` |
|---|---|
| 9.0 | `hopper` |
| 12.1 | `gb10` |
| anything else | none — "no shipped target" |

## Not covered

The preflight compares the compiled architecture against the device. It does
**not** verify that a kernel exists for every lookup — that is the separate
`--check-kernels` audit — and it cannot detect a build whose `HARDWARE.toml`
arch disagrees with the kernels actually compiled, because that file is the
SSOT both sides read.
