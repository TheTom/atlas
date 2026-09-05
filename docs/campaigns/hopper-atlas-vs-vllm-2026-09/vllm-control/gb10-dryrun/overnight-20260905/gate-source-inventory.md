**Gate source inventory — overnight Step B, 2026-09-05**

Inspected only immutable git objects from `fork/hopper/sm90-target-tdd-2026-09` at `8b7405ca159a6ab8bb3e593a740f4d20f93996fd` in `/tmp/atlas-vllm-control`. All source paths and line numbers below refer to that commit, not the rebasing working tree. No hardware, cargo, model download, gate execution, or source edit was performed for this inventory. Only this report was written.

The required set contains **11 gates**, not ten: `concurrency-sweep-dflash2` is the additional gate. `crates/atlas-plugin/src/gate/coverage.rs:498` defines `REQUIRED: [GateCoverage; 11]`; `crates/atlas-plugin/src/gate/mod.rs:82` repeats the same IDs. Older prose referring to ten is stale.

`--pull-request-gate` does **not** choose one shared Qwen checkpoint, nor does it select the newest record dynamically. It resolves the selected hardware class and that gate’s measured `default=true` entry from `kernels/*/*/BENCH.toml`. `--checkpoint` selects a registered variant; an arbitrary checkpoint is refused. At the inspected commit, **every default model and recipe matches that gate’s newest stored record**. This agreement is verified below; it must be rechecked if the rebased tree changes the entries. Sources: `crates/spark-server/src/cli/bench_resolve.rs:97–161`; `crates/atlas-plugin/src/gate/bench.rs:204–283`.

Canonical current-tree command, after the intended commit is clean and its release binary is built:

```sh
./target/release/spark benchmark run <gate-id> --hardware gb10 --pull-request-gate --yes
```

This reads the baseline’s recipe, server overrides and instrument/threshold parameters. Explicit `--param` values win over auto-filled defaults. The record’s full command is reproduced per gate below for exact historical parameter comparison; it is historical evidence, not a direction to override changed baselines. Sources: `crates/spark-server/src/cli/bench_run.rs:164–238`; `CONTRIBUTING.md:246`.

**Latest records and model selection**

All newest records have `git_sha=025b8acfdf`, `verdict=PASS`, and hardware `NVIDIA GB10`, host `spark-256a`, driver `580.126.09`. They are historical observations, not passing receipts for the inspected or rebased tip. All capture `ATLAS_PREFILL_CODISPATCH=0`, `ATLAS_PREFILL_CODISPATCH_SETTLE_MS=10`, `ATLAS_PREFILL_CODISPATCH_WINDOW_MS=100`; no other perf environment key is recorded.

| Required ID | Default checkpoint and newest-record checkpoint (identical) | Latest record date | Recorded elapsed | Default BENCH source |
|---|---|---|---:|---|
| `agentic-webserver` | `Qwen/Qwen3.6-35B-A3B-FP8` | 2026-09-02 | 10m 46s | `kernels/gb10/qwen3.6-35b-a3b/BENCH.toml:18` |
| `vision-fidelity` | `Qwen/Qwen3.6-35B-A3B-FP8` | 2026-09-02 | 0m 55s | `kernels/gb10/qwen3.6-35b-a3b/BENCH.toml:548` |
| `video-fidelity` | `unsloth/Qwen3.6-27B-NVFP4` | 2026-09-02 | 0m 16s | `kernels/gb10/qwen3.6-27b/BENCH.toml:297` |
| `ttft-warm-gate` | `Qwen/Qwen3.6-35B-A3B-FP8` | 2026-09-02 | 1m 32s | `kernels/gb10/qwen3.6-35b-a3b/BENCH.toml:243` |
| `ttft-cold-gate` | `Qwen/Qwen3.6-35B-A3B-FP8` | 2026-09-02 | 0m 48s | `kernels/gb10/qwen3.6-35b-a3b/BENCH.toml:177` |
| `bfcl-subset` | `unsloth/Qwen3.8-27B-NVFP4` | 2026-09-02 | 1h 37m 31s | `kernels/gb10/qwen3.8-27b/BENCH.toml:107` |
| `bfcl-subset-echolp` | `Qwen/Qwen3.6-35B-A3B-FP8` | 2026-09-02 | 2h 27m 6s | `kernels/gb10/qwen3.6-35b-a3b/BENCH.toml:121` |
| `ssm-state-poisoning-gate` | `Qwen/Qwen3.6-35B-A3B-FP8` | 2026-09-02 | 1m 24s | `kernels/gb10/qwen3.6-35b-a3b/BENCH.toml:347` |
| `decode-floor` | `unsloth/Qwen3.8-27B-NVFP4` | 2026-09-01 | 2m 0s | `kernels/gb10/qwen3.8-27b/BENCH.toml:188` |
| `concurrency-sweep` | `unsloth/Qwen3.8-27B-NVFP4` | 2026-09-02 | 24m 58s | `kernels/gb10/qwen3.8-27b/BENCH.toml:267` |
| `concurrency-sweep-dflash2` | `unsloth/Qwen3.8-27B-NVFP4` | 2026-09-02 | 3m 57s | `kernels/gb10/qwen3.8-27b/BENCH.toml:469` |

Ten original gates sum to **17,236 s (4h 47m 16s)** in these particular records; all eleven sum to **17,473 s (4h 51m 13s)**. These are sums of `hardware_state.delta.elapsed_s`, including executor coherence checks, plugin setup/provisioning and benchmark work, but excluding the self-start server/model loading that happens before executor creation. A clean-cache night can be materially longer. Sources: `crates/spark-server/src/cli/bench_run.rs:189–240`; `crates/atlas-plugin/src/executor.rs:224–231,308–338`. Descriptor estimates are more conservative: agentic ~5 min/iteration, each BFCL ~3.5 h, plain/DFlash2 concurrency ~25–90 min (shared wording), TTFT and decode ~3–6 min. These are hints, not observed durations or timeout guarantees. Sources: `benchmarks/agentic/descriptors.rs:61`, `benchmarks/bfcl/descriptors.rs`, `benchmarks/concurrency.rs:59,108`, `benchmarks/ttft/descriptors.rs:26,49`, `benchmarks/decode_floor/mod.rs:89` under `crates/atlas-plugin/src/`.

**Per-gate exact stored parameters, recipe, and command**

Each source record path below is relative to the immutable ref. Its `target_model`, `params`, `command`, `served_by`, `hardware`, `hardware_state`, and `perf_env` fields are the evidence. Recorded verdict parameters can be numerically lower than the raw committed metric bound because auto-fill incorporates the declared noise allowance; this is not a new threshold proposal. For example golden BFCL’s committed floors are 83.82 overall / 83.72 normalized with 0.4 noise, while its recorded effective parameters are 83.41999999999999 / 83.32. The source BENCH tables remain authoritative.

**`agentic-webserver`**

Source: `.benchmarks/agentic-webserver/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:19` (command), `:53` (hardware state). Recipe: `qwen3.6/qwen3.6-35b-a3b-fp8-bf16head`; default recipe matches.

```json
{
  "target_model": "Qwen/Qwen3.6-35B-A3B-FP8",
  "params": {
    "build_timeout_s": "600",
    "command_timeout_s": "180",
    "iterations": "10",
    "max_tokens": "8192",
    "max_turns": "40",
    "request_timeout_s": "900",
    "s_per_turn_budget": "8.5",
    "serve_timeout_s": "30",
    "wall_budget_s": "1800"
  },
  "serve_overrides": {}
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run agentic-webserver --param build_timeout_s=600 --param command_timeout_s=180 --param iterations=10 --param max_tokens=8192 --param max_turns=40 --param request_timeout_s=900 --param s_per_turn_budget=8.5 --param serve_timeout_s=30 --param wall_budget_s=1800 --yes --pull-request-gate
```

**`vision-fidelity`**

Source: `.benchmarks/vision-fidelity/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:12` (command), `:31` (hardware state). Recipe: `qwen3.6/qwen3.6-35b-a3b-fp8-bf16head`; default recipe matches.

```json
{
  "target_model": "Qwen/Qwen3.6-35B-A3B-FP8",
  "params": {
    "max_tokens": "128",
    "request_timeout_s": "300"
  },
  "serve_overrides": {}
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run vision-fidelity --param max_tokens=128 --param request_timeout_s=300 --pull-request-gate
```

**`video-fidelity`**

Source: `.benchmarks/video-fidelity/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:12` (command), `:31` (hardware state). Recipe: `qwen3.6/qwen3.6-27b-nvfp4-unsloth`; default recipe matches.

```json
{
  "target_model": "unsloth/Qwen3.6-27B-NVFP4",
  "params": {
    "max_tokens": "320",
    "request_timeout_s": "300"
  },
  "serve_overrides": {}
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run video-fidelity --param max_tokens=320 --param request_timeout_s=300 --pull-request-gate
```

**`ttft-warm-gate`**

Source: `.benchmarks/ttft-warm-gate/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:16` (command), `:43` (hardware state). Recipe: `qwen3.6/qwen3.6-35b-a3b-fp8-bf16head`; default recipe matches.

```json
{
  "target_model": "Qwen/Qwen3.6-35B-A3B-FP8",
  "params": {
    "median_limit_pct": "3",
    "p90_limit_pct": "5",
    "prompt_lengths": "256, 1024, 4096",
    "repeats": "12",
    "request_timeout_s": "300",
    "update_baseline": "true"
  },
  "serve_overrides": {}
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run ttft-warm-gate --param median_limit_pct=3 --param p90_limit_pct=5 --param 'prompt_lengths=256, 1024, 4096' --param repeats=12 --param request_timeout_s=300 --param update_baseline=true --pull-request-gate
```

**`ttft-cold-gate`**

Source: `.benchmarks/ttft-cold-gate/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:16` (command), `:43` (hardware state). Recipe: `qwen3.6/qwen3.6-35b-a3b-fp8-bf16head`; default recipe matches.

```json
{
  "target_model": "Qwen/Qwen3.6-35B-A3B-FP8",
  "params": {
    "median_limit_pct": "3",
    "p90_limit_pct": "5",
    "prompt_lengths": "256, 1024, 4096",
    "repeats": "12",
    "request_timeout_s": "300",
    "update_baseline": "true"
  },
  "serve_overrides": {}
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run ttft-cold-gate --param median_limit_pct=3 --param p90_limit_pct=5 --param 'prompt_lengths=256, 1024, 4096' --param repeats=12 --param request_timeout_s=300 --param update_baseline=true --pull-request-gate
```

**`bfcl-subset`**

Source: `.benchmarks/bfcl-subset/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:19` (command), `:52` (hardware state). Recipe: `qwen3.8/qwen3.8-27b-nvfp4-unsloth-bfcl`; default recipe matches.

```json
{
  "target_model": "unsloth/Qwen3.8-27B-NVFP4",
  "params": {
    "hallucination_pct": "10",
    "live_pct": "10",
    "max_new_tokens": "1024",
    "min_normalized": "83.32",
    "min_overall": "83.41999999999999",
    "non_live_pct": "62",
    "request_timeout_s": "600",
    "subset_floor": "25",
    "temperature": "0"
  },
  "serve_overrides": {}
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run bfcl-subset --param hallucination_pct=10 --param live_pct=10 --param max_new_tokens=1024 --param min_normalized=83.32 --param min_overall=83.41999999999999 --param non_live_pct=62 --param request_timeout_s=600 --param subset_floor=25 --param temperature=0 --pull-request-gate
```

**`bfcl-subset-echolp`**

Source: `.benchmarks/bfcl-subset-echolp/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:19` (command), `:57` (hardware state). Recipe: `qwen3.6/qwen3.6-35b-a3b-fp8-bf16head`; default recipe matches.

```json
{
  "target_model": "Qwen/Qwen3.6-35B-A3B-FP8",
  "params": {
    "hallucination_pct": "12",
    "live_pct": "23",
    "max_new_tokens": "1024",
    "min_normalized": "86.5",
    "min_overall": "86.1",
    "non_live_pct": "46",
    "request_timeout_s": "600",
    "subset_floor": "25",
    "temperature": "0"
  },
  "serve_overrides": {
    "ssm_cache_slots": "256"
  }
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run bfcl-subset-echolp --param hallucination_pct=12 --param live_pct=23 --param max_new_tokens=1024 --param min_normalized=86.5 --param min_overall=86.1 --param non_live_pct=46 --param request_timeout_s=600 --param subset_floor=25 --param temperature=0 --serve-override ssm_cache_slots=256 --pull-request-gate
```

**`ssm-state-poisoning-gate`**

Source: `.benchmarks/ssm-state-poisoning-gate/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:13` (command), `:42` (hardware state). Recipe: `qwen3.6/qwen3.6-35b-a3b-fp8-bf16head`; default recipe matches.

```json
{
  "target_model": "Qwen/Qwen3.6-35B-A3B-FP8",
  "params": {
    "max_tokens": "1024",
    "request_timeout_s": "300",
    "rounds": "12"
  },
  "serve_overrides": {
    "disable_thinking": "true",
    "ssm_cache_slots": "256"
  }
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run ssm-state-poisoning-gate --param max_tokens=1024 --param request_timeout_s=300 --param rounds=12 --serve-override disable_thinking=true --serve-override ssm_cache_slots=256 --pull-request-gate
```

**`decode-floor`**

Source: `.benchmarks/decode-floor/2026-09-01-025b8acfdf.json:7` (model), `:8` (params), `:12` (command), `:31` (hardware state). Recipe: `qwen3.8/qwen3.8-27b-nvfp4-unsloth`; default recipe matches.

```json
{
  "target_model": "unsloth/Qwen3.8-27B-NVFP4",
  "params": {
    "min_tok_s": "20.5",
    "request_timeout_s": "300"
  },
  "serve_overrides": {}
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run decode-floor --param min_tok_s=20.5 --param request_timeout_s=300 --pull-request-gate
```

**`concurrency-sweep`**

Source: `.benchmarks/concurrency-sweep/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:25` (command), `:84` (hardware state). Recipe: `qwen3.8/qwen3.8-27b-nvfp4-unsloth`; default recipe matches.

```json
{
  "target_model": "unsloth/Qwen3.8-27B-NVFP4",
  "params": {
    "concurrencies": "1, 2, 4, 8, 16, 32, 64, 128",
    "isls": "512",
    "min_c1": "17.2",
    "min_c128": "107.6",
    "min_c16": "82.55",
    "min_c2": "24.05",
    "min_c32": "96.8",
    "min_c4": "35.7",
    "min_c64": "107.6",
    "min_c8": "45.7",
    "min_peak": "107.6",
    "osl": "320",
    "prompt_mode": "natural",
    "request_timeout_s": "600",
    "warmup": "1"
  },
  "serve_overrides": {
    "kv_cache_dtype": "fp8",
    "max_batch_size": "128",
    "max_model_len": "4096",
    "ssm_cache_slots": "8"
  }
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run concurrency-sweep --param 'concurrencies=1, 2, 4, 8, 16, 32, 64, 128' --param isls=512 --param min_c1=17.2 --param min_c128=107.6 --param min_c16=82.55 --param min_c2=24.05 --param min_c32=96.8 --param min_c4=35.7 --param min_c64=107.6 --param min_c8=45.7 --param min_peak=107.6 --param osl=320 --param prompt_mode=natural --param request_timeout_s=600 --param warmup=1 --serve-override kv_cache_dtype=fp8 --serve-override max_batch_size=128 --serve-override max_model_len=4096 --serve-override ssm_cache_slots=8 --pull-request-gate
```

**`concurrency-sweep-dflash2`**

Source: `.benchmarks/concurrency-sweep-dflash2/2026-09-02-025b8acfdf.json:7` (model), `:8` (params), `:25` (command), `:93` (hardware state). Recipe: `qwen3.8/qwen3.8-27b-nvfp4-dflash2`; default recipe matches.

```json
{
  "target_model": "unsloth/Qwen3.8-27B-NVFP4",
  "params": {
    "concurrencies": "1, 2, 4, 8, 16",
    "isls": "512",
    "min_c1": "19.05",
    "min_c128": "0",
    "min_c16": "57",
    "min_c2": "35.38",
    "min_c32": "0",
    "min_c4": "41.77",
    "min_c64": "0",
    "min_c8": "49.62",
    "min_peak": "57",
    "osl": "200",
    "prompt_mode": "natural",
    "request_timeout_s": "600",
    "warmup": "1"
  },
  "serve_overrides": {
    "dflash": "true",
    "dflash_gamma": "8",
    "draft_model": "incoai/Qwen3.8-27B-DFlash2",
    "kv_cache_dtype": "fp8",
    "max_batch_size": "16",
    "max_model_len": "4096",
    "ssm_cache_slots": "8"
  }
}
```

Historical command, argv preserved and shell-quoted:

```sh
spark benchmark run concurrency-sweep-dflash2 --param 'concurrencies=1, 2, 4, 8, 16' --param isls=512 --param min_c1=19.05 --param min_c128=0 --param min_c16=57 --param min_c2=35.38 --param min_c32=0 --param min_c4=41.77 --param min_c64=0 --param min_c8=49.62 --param min_peak=57 --param osl=200 --param prompt_mode=natural --param request_timeout_s=600 --param warmup=1 --serve-override dflash=true --serve-override dflash_gamma=8 --serve-override draft_model=incoai/Qwen3.8-27B-DFlash2 --serve-override kv_cache_dtype=fp8 --serve-override max_batch_size=16 --serve-override max_model_len=4096 --serve-override ssm_cache_slots=8 --pull-request-gate
```

**Prerequisites and concrete blockers to verify before execution**

- **Source and receipts:** `CONTRIBUTING.md:246–262` requires every required gate to PASS at current tip, forbids dirty-tree receipts and lowering thresholds to obtain a pass. `crates/atlas-plugin/src/gate/check.rs:445–449` rejects a non-PASS run verdict. Inspect the clean rebased tree’s required set and gate coverage before claiming completion; the old `025b8acfdf` files do not certify a newly changed serving path.

- **Local recipe index:** self-start reads the cached index at the artifact root’s `atlas-recipes/index.json`; it does not silently fetch missing recipes. Its explicit remedy is `spark sync-recipes`. It verifies recipe checkpoint equals the selected baseline model, honors recipe utilization, merges declared server pins, and refuses an insufficiently free host. Sources: `crates/spark-server/src/cli/bench_selfstart.rs:144–219,293–334`. Constants: boot timeout 900s at line46 and minimum host available-memory fraction 0.85 at line68. The exact installed index bytes, model revisions, weight availability, storage needs and live host prerequisites were not inspected in this read-only task. Recipes live in the separate atlas-recipes repository; the recipe ID alone does not establish the current index’s full serve argv.

- **Three required checkpoints:** MoE `Qwen/Qwen3.6-35B-A3B-FP8` serves agentic, echolp, both TTFTs, poison and vision; dense `unsloth/Qwen3.8-27B-NVFP4` serves golden BFCL, decode and both sweeps; dense `unsloth/Qwen3.6-27B-NVFP4` serves video. The DFlash2 sweep additionally needs `incoai/Qwen3.8-27B-DFlash2`. Availability/total download footprint is unknown here. Running all IDs against the MoE would not reproduce these defaults or receipts.

- **BFCL:** requires Python >=3.10, importable venv, pip, writable `~/.atlas/artifacts/bfcl`, and network on the first uncached provision. It installs pinned `bfcl-eval==2026.3.23`, materializes the dataset from that package, and skips installation only when the content-derived stamp and artifacts match. Sources: `crates/atlas-plugin/src/benchmarks/bfcl/provision.rs:3–15,28–34,73–155`; `crates/atlas-plugin/assets/bfcl/requirements.txt`. Golden draw is non-live/live/hallucination 62/10/10%, floor 25, n=995; echolp is 46/23/12%, floor 25, n=1004. They cannot share normalized-score thresholds.

- **Video:** ffmpeg must be available in the **server’s** environment, and the recipe must enable `video_allow_ffmpeg=true`. Certified thresholds require 13 passed legs, 0 skipped, control_held=1; GIF-only execution cannot satisfy this gate. Sources: `crates/atlas-plugin/src/benchmarks/video/mod.rs:41–50`; `kernels/gb10/qwen3.8-27b/BENCH.toml:791–799` documents the shared prerequisite, while the actual required video default is the Qwen3.6 dense entry in the table. Vision and video fixture bytes are embedded in the binary and materialized locally; no runtime media download is needed (`benchmarks/vision/provision.rs:10–22`, `benchmarks/video/provision.rs:5–8`).

- **TTFT:** comparison uses a stored baseline for the same box and checkpoint. `update_baseline=true` stores non-failing runs, but a first/no-comparable-baseline run is INFO, not PASS. A regression is never saved as a new baseline. Thus a fresh artifact store can require baseline establishment before a comparable passing run; do not relabel INFO as PASS. Sources: `crates/atlas-plugin/src/benchmarks/ttft_verdict.rs:14–29,52–75`; `ttft.rs:370–379`. Committed metric ceilings additionally remain in BENCH.toml. The latest receipts use update_baseline=true, as shown above.

- **Agentic execution boundary:** this benchmark executes model-authored shell using `sh -c`, a fresh current directory, inherited environment and normal process privileges. It is **not an OS sandbox or network boundary**. File tools reject lexical/symlink escapes, but the source explicitly calls this defense in depth and says bash is unconfined. Sources: `crates/atlas-plugin/src/benchmarks/agentic/agent_path.rs:15–19`; `agent_shell.rs:48–75`. Tool commands have timeouts/output caps/process-group cleanup, not filesystem/network confinement. Existing execution isolation must therefore be established outside this driver.

- **Agentic runtime tools and network:** cargo, a working Rust compiler/linker, sh, curl, timeout, setsid, fuser and kill must be available where the benchmark runs. The prompt directs creation/testing of an Axum server, bind 0.0.0.0 using ATLAS_HARNESS_PORT (default 3001 for agent work), curl proof, and port-based cleanup. The scorer reserves a free local port, builds and runs release output, and probes it. Sources: `crates/atlas-plugin/src/benchmarks/agentic/mod.rs:76–89,294–314`; `score.rs:112–230`. Cleanup of detached processes relies on Linux `/proc/<pid>/cwd` and is a no-op without `/proc` (`agent.rs:198–228`). A fresh directory does not prevent access to other files or inherited credentials.

- **Agentic build preparation:** requires writable artifact sandbox directories and shared Cargo targets. Default warm directories are `$HOME/.cargo/atlas-warm-target` and `$HOME/.cargo/atlas-warm-template`, overridden by `ATLAS_WARM_TARGET_DIR` / `ATLAS_WARM_TEMPLATE_DIR`. `warm.rs:35,103–120,148–151,194–206` prebuilds both `cargo test --no-run` and `cargo build --release`, each under 1800 s timeout. Network deliberately remains ON because a generated project can select dependency versions absent from the warm cache. The template prewarms Axum 0.8, Tokio 1, serde 1, serde_json 1, tower 0.5, tower-http 0.6, hyper 1, reqwest 0.12, anyhow 1, thiserror 2, tracing 0.1 and tracing-subscriber 0.3. Fresh network/cache setup can extend the recorded 10m 46s agentic elapsed substantially.

- **Agentic source caveat:** `crates/atlas-plugin/src/benchmarks/agentic/descriptors.rs:14–28` says a desired `mtp_gate: force` determinism pin is not yet in the referenced external recipe and requires an atlas-recipes change. This is an explicit source caveat, not a finding about today’s uninspected local index and not permission to alter the recipe for these gates. The gate keeps its own thinking-on trajectories; its sanity completion temporarily disables thinking. Do not substitute the Nano rehearsal’s thinking/speculation settings.

No blocker above was tested on the live machine during this task; these are source-defined requirements and identified unknowns. No gate result was produced.
