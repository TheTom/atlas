# Atlas PTX gate — `gb10` @ `sm_121a`

* generated: 2026-09-05T13:45:46Z on `spark1`
* toolchain: Build cuda_13.0.r13.0/compiler.36424714_0
* strict (`--Werror all-warnings`, as build.rs): True
* self-test: known_good passed=True, `known_bad_post_hopper.cu` failed=True
* **173/173 kernels compiled** (0 failed, 0 rejected entry function(s))

| model | kernels | pass | fail |
|---|---:|---:|---:|
| qwen3.6-35b-a3b | 173 | 173 | 0 |

No failures: every kernel in this hardware set emitted PTX and assembled for the target architecture.

## Highest register pressure

| model | kernel | max registers | spill bytes |
|---|---|---:|---:|
| qwen3.6-35b-a3b | `gated_delta_rule` | 255 | 1412 |
| qwen3.6-35b-a3b | `gated_delta_rule_persistent` | 255 | 2240 |
| qwen3.6-35b-a3b | `gated_delta_rule_wy2_resident` | 255 | 112 |
| qwen3.6-35b-a3b | `gated_delta_rule_wy2_resident_f16` | 255 | 24 |
| qwen3.6-35b-a3b | `gated_delta_rule_wy3_resident` | 255 | 16 |
| qwen3.6-35b-a3b | `gated_delta_rule_wy3_resident_f16` | 255 | 148 |
| qwen3.6-35b-a3b | `inferspark_prefill_v47` | 252 | 0 |
| qwen3.6-35b-a3b | `gated_delta_rule_fla` | 250 | 0 |
| qwen3.6-35b-a3b | `w4a16_gemm` | 168 | 0 |
| qwen3.6-35b-a3b | `fp8_gemm_t_blockscaled` | 162 | 0 |

Compilation is not correctness. Nothing here has run on gb10 silicon; these kernels are known to EXIST for the architecture, not to produce the right numbers or to be fast.
