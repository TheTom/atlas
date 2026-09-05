# H100 Rental Day - Plan

Written 2026-09-05 from the RTX PRO 6000 session ([[Borrowed RTX PRO 6000 Box - Work Log]]) and Grok's rental notes. Kit: `~/dev/rental-kit/` (see its README): `preflight_node.sh`, `bootstrap.sh`, `build_spark.sh`, `dl_queue.sh` (shared `HF_HOME=/root/hf`), `install_vllm.sh`, `sync_results.sh`, plus the diagnostics `logit_diff.py` (token-level Atlas-vs-vLLM oracle with `--raw` completions mode; exit 2 when a server returns no logprobs), `fault_triage.sh` (`CUDA_LAUNCH_BLOCKING=1` rerun + compute-sanitizer memcheck + dmesg/Xid capture), `profile_decode.sh` + `loadgen.py` (nsys decode trace under load, top-15 kernel table; `--launch` mode, attach semantics probed at runtime). Campaign tooling lives on `TheTom/atlas:hopper/sm90-target-tdd-2026-09` (upstream atlas#895), owned by the Codex session.

## What to rent

| Requirement | Why | Abort if |
|---|---|---|
| **Driver ≥ 580 ("Max CUDA" ≥ 13.0)** | Atlas links the CUDA 13 runtime; a 12.x driver fails at `cuInit`, PTX never matters. RTX box had 595.71 | driver < 580 |
| CC 9.0 (H100/H200), 1 or 2 GPUs | hopper target is `sm_90a`, exact arch | anything else |
| NVLink if 2 GPUs | Atlas TP/EP over NVLink is untested; PIX-only tells us nothing about a real 8× node | `topo -m` shows no `NV*` |
| ≥ 300 GB disk (Tom's quote: 300 GB instance, no volume, 2× H100 SXM, $3.789/h) | Super FP8 120 GiB + Nano 18+31 + vLLM ~10 + toolkit 4 + repo/target 3 ≈ 190 GB, **only if both engines share one HF cache** (`HF_HOME=/root/hf`; `dl_queue.sh` fills it; never `--local-dir`) | < 250 GB |
| Ubuntu 22.04/24.04 container with apt | bootstrap uses the NVIDIA apt repo for CUDA 13 + NCCL ≥ 2.28 | no apt |
| No docker inside? fine | Atlas runs as a host binary; vLLM control via `uv pip install vllm` (`install_vllm.sh`) or the provider's docker if available | |

Budget: 1× H100 ≈ $2–4/h. Shakedown = 4 h. Scoring day = separate booking after the shakedown is green.

## Sequence (shakedown, 1× H100 or H200)

| T+ | Step | Gate |
|---|---|---|
| 0:00 | `bash preflight_node.sh --want-gpus 1 --want-cc 9.0` | `PREFLIGHT: GO`, else destroy the instance |
| 0:05 | `bash bootstrap.sh` in tmux (apt deps, NVIDIA repo, CUDA 13.0 + NCCL ≥ 2.28, rustup, clone PR branch, hf CLI). Start `sync_results.sh` on the Mac | `BOOTSTRAP_EXIT=0` (~25 min, mostly the toolkit download) |
| 0:05 | in parallel: `dl_queue.sh` (Nano NVFP4 19 GiB → Nano FP8 31 → Super FP8 120) | Nano NVFP4 done before the build finishes |
| 0:30 | `bash build_spark.sh hopper nemotron-3-nano-30b-a3b` | `BUILD_OK` (~4 min cold). Do **not** use CI artifacts from before c4c1b562 (memory bug) |
| 0:35 | `spark serve <nano-nvfp4> --check-kernels --no-tui --gpu-ordinal 0` | exit 0, JSON `compiled_arch sm_90a`, `device_cc 9.0`, `unresolved 0`, and the log line `KV budget self-relative (ledger)` (proves the discrete-GPU fix is in) |
| 0:40 | serve Nano on loopback, `bench/hopper_ab/coherency_gate.py` | determinism ok, known answers; compare with the RTX result (Tokyo/primes pass, arithmetic/spelling refused) |
| 0:50 | vLLM control on Nano FP8 via `bench/campaign/run_cell.sh --engine vllm ...` (dry-run first) | artifact validates; coherency gate on vLLM answers the "model or engine" question for the refusals |
| 1:15 | `run_cell.sh --engine atlas` same cell | paired artifact; this is the first scored H100 pair |
| 1:45 | Super FP8: `build_spark.sh hopper nemotron-super-120b-a12b`, check-kernels, coherency, then the same pair | Super is TP1-capable on 80 GB? FP8 120 GiB is **not**: needs 2× H100 or H200 (141 GB). On 1× H100 skip Super, do Qwen3.6-35B FP8 (35 GiB) instead |
| 3:00 | wrong-arch oracle for free: run the **b200** CI/`build_spark.sh b200` binary on the H100 | refuses in < 10 s with `compiled_arch sm_100a` vs `device_cc 9.0`, no weight load |
| 3:30 | `sync_results.sh` final pull, destroy instance | results in `~/dev/rental-kit/results/` |

## Rules that cost us before

- One engine on the GPUs at a time. Kill vLLM before Atlas and the reverse.
- Freeze the vLLM control once its artifact validates; never touch its flags after Atlas numbers exist.
- Same checkpoint revision, max_len, concurrency ladder, temperature 0, thinking off, MTP off on both, until coherency is green.
- `ATLAS_TARGET_QUANT=nvfp4` always: kernel sets live under `<model>/nvfp4/` for every target; FP8 checkpoints load through them. `fp8` yields no kernels.
- Bind servers to 127.0.0.1. Rental hosts expose random ports.
- Results leave the box every 5 min (`sync_results.sh`). The RTX container vanished after 50 min with everything on it.
- Check `nvidia-smi --query-compute-apps` before every GPU step; refuse if a foreign PID holds the GPU.

## Known Atlas facts going in

- x86_64 build proven (CI + RTX box). Cold 3 m 45 s, warm 55 s on 128 vCPU.
- Discrete-GPU KV budget bug fixed (atlas#904, on #895 since c4c1b562). Watchdog half fixed too.
- `sm_90a` static shared-memory ceiling is 227 KiB; the 22 gb10 prefill rejections do not apply.
- Hopper compiles out the W4A4 NVFP4 tail (`-DATLAS_NO_WARP_BLOCKSCALE_MMA`); `moe_w4a16_*_k64_fp4` are expected-absent. NVFP4 checkpoints still load (W4A16 path).
- `--check-kernels` loads weights before it audits, so it needs a model dir; Nano is the cheap one.
- Nano NVFP4 on Blackwell: ~277 tok/s decode, 75 ms TTFT; deterministic; refuses arithmetic/spelling probes regardless of KV dtype. Unresolved whether model or engine; the vLLM control settles it.

## Instrumentation on the day

| Symptom | Tool | What it answers |
|---|---|---|
| won't load / refuses / OOM | `--check-kernels` JSON, `RUST_LOG=info` KV-budget lines | which stage, which arch, which kernel lookup |
| answers wrong | `logit_diff.py --raw` against the vLLM control | model vs engine; first divergent token position; template vs kernel |
| CUDA error at a sync point | `fault_triage.sh` | which request, which kernel (sanitizer), Xid |
| slower than vLLM | `profile_decode.sh` | kernel time table for a 30 s decode window |
| any of the above needs a fix | `rental/h100-<date>` branch, `build_spark.sh` (55 s warm) | Codex cherry-picks into #895 afterward |

## Open before booking

- [ ] Codex's inventory-test fix for the Hopper Qwen27B target (review thread on #895) so `cargo test` is green at the tip we build.
- [ ] Decide 1× H100 (Nano + Qwen3.6-35B) vs 2× H100/1× H200 (adds Super FP8 and the NVLink question).
- [ ] Provider account + payment ready; instance template with "Max CUDA ≥ 13.0" filter.
