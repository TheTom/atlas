# GB10 architecture preflight rehearsal — Step D1

**Runtime proof is blocked, not passed.** A real Hopper release binary compiled successfully on Spark 2, but a separate GPU tenant appeared before the first model download or engine invocation. The occupancy guard refused the next step. No architecture refusal, CUDA module load, weight load, or control audit was executed. These are GB10 rehearsal observations, never Hopper/B200 performance data.

Code source: `b2c17cfe30c33c53d28c4fbec35f6204b8cfb14b`. Host: `pidtom@192.168.50.36`, NVIDIA GB10, driver `580.173.02`, CUDA `13.0.88`, Rust `1.93.1`, aarch64. [Initial occupancy and `nvidia-smi -q`](evidence/arch-preflight-gb10/initial-preflight/stdout.txt) showed only Xorg/gnome graphics processes, zero compute processes and no containers. [Model inventory](evidence/arch-preflight-gb10/nano-location-inventory/stdout.txt) and [missing-path output](evidence/arch-preflight-gb10/nano-location-inventory/stderr.txt) show Nano was absent from the inspected cache/model locations.

| Binary | Expected | Observed | Oracle | Verdict |
|---|---|---|---|---|
| Hopper / `sm_90a` | Build a real release `spark` without using the GPU | Exit 0, all 171 kernels compiled; 208.46 s by GNU time; 1,149,850,057-byte target directory | Compiler exit, complete stderr, ELF identity and binary SHA | Build PASS; runtime unobserved |
| B200 / `sm_100a` | Build a separate release binary | Not started after occupancy stop | A real binary and captured build status are required | BLOCKED |
| GB10 / `sm_121f` | Build the matching control binary | Not started after occupancy stop | A real binary and captured build status are required | BLOCKED |

The build emitted PTX with `nvcc --ptx`; it did not run `ptxas` or the CUDA driver. A successful build is not assembly validation or kernel correctness. The Hopper binary was an aarch64 ELF. SHA-256: `9232f77f2898f1450a93ecd458d153a7a6a476c20e6078b7d2ce28a1a92b7398`. [Build command/environment](evidence/arch-preflight-gb10/hopper/build.command.json), [full stderr](evidence/arch-preflight-gb10/hopper/build.stderr.txt), [GNU time](evidence/arch-preflight-gb10/hopper/build.time.txt), [target size](evidence/arch-preflight-gb10/hopper/target-size.stdout.txt), and [ELF/source provenance](evidence/arch-preflight-gb10/build-final-provenance/stdout.txt) are preserved. Cargo used a task-owned copy of the existing dependency cache and a fresh target directory; this is not a network-cold build. `CARGO_BUILD_JOBS=4` was explicit, while the kernel build itself reported 20 parallel nvcc workers.

At 12:55:39 UTC, the [next-step guard](evidence/arch-preflight-gb10/nano-config-prefetch/stdout.txt) observed PID 231116 using 20,408 MiB. The [follow-up snapshot](evidence/arch-preflight-gb10/foreign-occupancy/stdout.txt) identified the separate `/home/pidtom/butter-selectors/rust/target/debug/deps/iron_selector_model-5f27772cdf230715` workload under a successor PID. The guard exited 1 before its `mkdir` or `curl`; even the proposed pinned Nano `config.json` download did not start. No foreign process was signalled. The already-running CPU-only Hopper build completed; no further heavy or GPU step was started.

| Runtime oracle | Required observation | Actual observation and verdict |
|---|---|---|
| A: matching GB10 control | Exit 0, JSON `compiled_arch=sm_121f`, `device_cc=[12,1]` | No binary/control invocation; BLOCKED |
| B: genuine Hopper and B200 mismatch | Nonzero exit under 10 s, JSON and human message naming compiled arch and CC 12.1, no earlier weight load | Hopper binary exists but was never executed; B200 not built; BLOCKED |
| C: normal `spark serve` | Same early refusal; trace/log proves no CUDA module or safetensors load before it | No serve or strace invocation; BLOCKED |
| D: normal N=1 launcher | Reports refusal promptly, exits nonzero and clears owned rank records | No real-binary launch; BLOCKED. CPU suite evidence below is supplementary only. |

Known-bad-first rule: the genuinely mismatched Hopper binary was intended to run before accepting the matching control. Occupancy prevented the first runtime negative probe, so no green runtime conclusion is drawn. Stopping rule applied: the hard occupancy rule stops new heavy/GPU work; preserve the block and move to D2/D3 rather than wait or disturb the tenant. D4 is not eligible because D1 runtime proof remains incomplete.

Invocation sources, read before building:

- `docs/HARDWARE.md` documents `ATLAS_TARGET_MODEL='*' cargo build --release -p spark-server`, verbatim hardware `arch` forwarding, and that Hopper FP8 checkpoints use the `nvfp4` kernel directory.
- `docker/hopper/Dockerfile:49–59,93–104` declares `ATLAS_TARGET_HW`, the Nano model slug, `ATLAS_TARGET_QUANT=nvfp4`, and `cargo build --release -p spark-server --bin spark --no-default-features --features cuda,nccl`. The recorded build narrows only the documented target dimensions and adds `--locked`.
- `scripts/start-node-ep.sh:653–725` builds `spark serve MODEL` with topology, ordinal, port, bootstrap and `--no-tui`; check mode adds `--check-kernels` and forces world/EP/TP to 1. [Both exact dry-rendered invocations](evidence/arch-preflight-gb10/planned-launcher-commands/serve.stdout.txt) and the [check invocation](evidence/arch-preflight-gb10/planned-launcher-commands/check-kernels.stdout.txt) are preserved as plans, not executions.
- `bench/campaign/run_cell.sh:88–91,755–759` points at that launcher and performs the kernel audit before normal serve. `crates/spark-server/src/main_modules/serve_phases/preflight.rs:326–333` calls the architecture preflight before constructing `AtlasCudaBackend`.

A source-only contract risk remains for the eventual runtime check: `kernel_gate.rs:171–180` serializes `device_cc` as a string such as `"12.1"`, whereas this task's oracle requires `[12,1]`. The JSON emitter is downstream of `init_gpu_backend`; whether an early mismatch emits any check JSON remains unobserved. These are source observations, not a reproduced GPU failure, and no frozen code was changed.

The existing launcher CPU suite first failed under inherited `RUST_LOG=warn` because assertion (a) expects a literal `env RUST_LOG=info` prefix: [exit 1 and stderr](evidence/arch-preflight-gb10/launcher-cpu-suite/stderr.txt). `env -u RUST_LOG bash scripts/start_node_ep_test.sh` then passed **30 assertions**, including dead-rank detection and cleanup: [actual output](evidence/arch-preflight-gb10/launcher-cpu-suite-clean-env/stdout.txt). This is a P2 environment-sensitive test finding, not evidence that oracle D ran on a GPU.

Cleanup and disk accounting are recorded in [cleanup output](evidence/arch-preflight-gb10/cleanup/stdout.jsonl). All task-owned remote clone, dependency cache, target tree, binary copies, evidence scratch and scripts were removed after verifying all 39 copied build-evidence hashes. No model checkpoint, container or image was created. `df -h /` showed 62 GiB free initially, 57 GiB immediately before cleanup and 60 GiB afterward (63,965,319,168 bytes available). The final owned tree occupied 2,564,610,699 apparent bytes; the build resource samples remained above 61 GB free. Whole-filesystem usage also changed due to other work, so its delta is not attributed entirely to this task.
