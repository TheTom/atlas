# Atlas PTX gate — `rtx-pro-6000` @ `sm_120a`

* generated: 2026-09-05T13:44:11Z on `spark1`
* toolchain: Build cuda_13.0.r13.0/compiler.36424714_0
* strict (`--Werror all-warnings`, as build.rs): True
* self-test: known_good passed=True, `known_bad_post_hopper.cu` failed=True
* **871/871 kernels compiled** (0 failed, 0 rejected entry function(s))

| model | kernels | pass | fail |
|---|---:|---:|---:|
| deepseek-v4-flash | 185 | 185 | 0 |
| nemotron-3-nano-30b-a3b | 171 | 171 | 0 |
| nemotron-super-120b-a12b | 171 | 171 | 0 |
| qwen3-next-80b-a3b | 171 | 171 | 0 |
| qwen3.6-35b-a3b | 173 | 173 | 0 |

No failures: every kernel in this hardware set emitted PTX and assembled for the target architecture.

## Highest register pressure

| model | kernel | max registers | spill bytes |
|---|---|---:|---:|
| deepseek-v4-flash | `gated_delta_rule_persistent` | 255 | 2240 |
| deepseek-v4-flash | `gated_delta_rule_wy2_resident` | 255 | 112 |
| deepseek-v4-flash | `gated_delta_rule_wy2_resident_f16` | 255 | 24 |
| deepseek-v4-flash | `gated_delta_rule_wy3_resident` | 255 | 16 |
| deepseek-v4-flash | `gated_delta_rule_wy3_resident_f16` | 255 | 148 |
| nemotron-3-nano-30b-a3b | `gated_delta_rule_persistent` | 255 | 2240 |
| nemotron-3-nano-30b-a3b | `gated_delta_rule_wy2_resident` | 255 | 112 |
| nemotron-3-nano-30b-a3b | `gated_delta_rule_wy2_resident_f16` | 255 | 24 |
| nemotron-3-nano-30b-a3b | `gated_delta_rule_wy3_resident` | 255 | 16 |
| nemotron-3-nano-30b-a3b | `gated_delta_rule_wy3_resident_f16` | 255 | 148 |

Compilation is not correctness. Nothing here has run on rtx-pro-6000 silicon; these kernels are known to EXIST for the architecture, not to produce the right numbers or to be fast.
