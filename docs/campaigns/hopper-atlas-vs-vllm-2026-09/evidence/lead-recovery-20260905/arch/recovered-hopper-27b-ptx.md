# Atlas PTX gate — `hopper` @ `sm_90a`

* generated: 2026-09-05T15:22:43Z on `spark1`
* toolchain: Build cuda_13.0.r13.0/compiler.36424714_0
* strict (`--Werror all-warnings`, as build.rs): True
* HARDWARE.toml `[build] extra_nvcc_flags`: `-DATLAS_NO_WARP_BLOCKSCALE_MMA`
* self-test: known_good passed=True, `known_bad_post_hopper.cu` failed=True
* **181/181 kernels compiled** (0 failed, 0 rejected entry function(s))

| model | kernels | pass | fail |
|---|---:|---:|---:|
| qwen3.8-27b | 181 | 181 | 0 |

No failures: every kernel in this hardware set emitted PTX and assembled for the target architecture.

## Highest register pressure

| model | kernel | max registers | spill bytes |
|---|---|---:|---:|
| qwen3.8-27b | `gated_delta_rule` | 255 | 1224 |
| qwen3.8-27b | `gated_delta_rule_fla` | 255 | 324 |
| qwen3.8-27b | `gated_delta_rule_persistent` | 255 | 124 |
| qwen3.8-27b | `gated_delta_rule_wy2_resident` | 255 | 120 |
| qwen3.8-27b | `gated_delta_rule_wy2_resident_f16` | 255 | 40 |
| qwen3.8-27b | `gated_delta_rule_wy3_resident` | 255 | 204 |
| qwen3.8-27b | `gated_delta_rule_wy3_resident_f16` | 255 | 64 |
| qwen3.8-27b | `nvfp4_mmq` | 255 | 0 |
| qwen3.8-27b | `q2_0_mmq` | 255 | 0 |
| qwen3.8-27b | `q4k_mmq` | 255 | 0 |

Compilation is not correctness. Nothing here has run on hopper silicon; these kernels are known to EXIST for the architecture, not to produce the right numbers or to be fast.
