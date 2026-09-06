# Final combined source CPU gates — PASS

Exact tested clean commit: `9cfce36ceac0ac9bfa43b23c26a63cf0beac7770`. Before/after tracked source content hash: `b6b9e5fc971102c85011ecbd599bdb72586e8b594a1973d2c369ca65dca7a75f` over 3200 paths. Both source receipts match. All10 stages exited0. No source changes were made on the rental by this agent.

| Stage | Exit | Passed | Failed | Ignored | Wall seconds |
|---|---:|---:|---:|---:|---:|
| atlas-kernels | 0 | 75 | 0 | 7 | 14.004 |
| spark-model | 0 | 645 | 0 | 14 | 50.008 |
| spark-server | 0 | 2456 | 0 | 19 | 102.034 |
| xgrammar | 0 | 829 | 0 | 1 | 20.005 |
| hopper-ptx-gate-selftest | 0 | 0 | 0 | 0 | 4.003 |
| nvfp4-preprocessor | 0 | 0 | 0 | 0 | 2.003 |
| workspace-rustdoc | 0 | 0 | 0 | 0 | 46.008 |
| workspace-doctests | 0 | 0 | 0 | 2 | 34.006 |
| affected-clippy | 0 | 0 | 0 | 0 | 46.007 |
| format | 0 | 0 | 0 | 0 | 6.003 |

The PTX gate selftest separately observed **7/7 assertions**, including the real nvcc/ptxas known-bad two-entry rejection. Its optional shellcheck step was skipped because shellcheck is absent on the rental; parent owns the Mac shellcheck gate. Actual rental preprocessing selected **0,0,13,13,0** MMQ exports for SM900,1000,1200,1210,1300. The new production finalize regression passed by name in spark-model/output.log.

`xgrammar` totals include826 unit tests, two optional-tokenizer integration entries and one vocabulary_allocations integration test. Its separate doctest stage reported0passed/1ignored. The two integration entries return early without their configured local tokenizer; this runner did not set `QWEN_TOKENIZER_JSON`. They are not proof of a fresh native-checkpoint grammar replay. Workspace doctests reported0 executed tests and2 ignored tests; the build/validation command nevertheless exited0. All ignored GPU tests stayed ignored; no --ignored was passed.

Environment: Rust/cargo1.93.1, `CUDA_VISIBLE_DEVICES=''`, `ATLAS_SKIP_BUILD=1`, `CUDARC_CUDA_VERSION=13000`, jobs6, separate `/workspace/atlas-rental/target-cpu-checks`. The GPU release target was untouched. nvcc13.0.48 supplied the CPU-only PTX negative selftest.

Started 2026-09-05T23:15:34.481802+00:00; finished 2026-09-05T23:21:04.264976+00:00. `df -h /`:398G free before,388G after. Exact free bytes 426369310720→415824064512; task disk bytes 79022022656→89549094912. CPU target final9.8G. Neither20GiB floor nor300GB task cap was approached. The parent allowed a Butter GPU lease during final CPU work; initial and final captured nvidia-smi snapshots both happened to show0MiB and no processes. This CPU result makes no GPU timing or numerical correctness claim.

Full stage commands, output logs, exit codes, time-v, resource records and source receipts were exported unchanged from `/workspace/atlas-rental/results/cpu-checks/9cfce36ceac0ac9bfa43b23c26a63cf0beac7770-20260905T231534Z/` into the sibling directory `9cfce36ceac0ac9bfa43b23c26a63cf0beac7770-20260905T231534Z/`. `rental-cpu-log-manifest.json` hashes every exported file. Additional compiler/occupancy/df receipts are in `cpu-gate-prep/rental-before.txt` and `rental-after.txt`.

This supersedes the earlier temporary Mac/Spark1 broad-test block in REPORT.md. The parent still must validate the repaired MMQ fallback on a fresh real H100 engine before claiming the runtime defect fixed.
