# Step B prerequisites at the recovered code

Read-only source assessment. No GPU access, remote inspection, build, model download, recipe synchronization, or gate execution was performed. `prerequisites.json` records the inspected HEAD, the 11 current measured default rows, their exact thresholds/pins, and latest historical timing evidence.

**All gates cannot be declared runnable yet.** The canonical suite needs three main checkpoints plus one draft, a populated external recipe index, three model-specific GB10 binaries or a wildcard binary, and Python/Rust/ffmpeg runtime tools. Two repository sizes and the selected machine's existing cache contents remain unverified. Running one model group at a time could satisfy the storage limit, but this must be measured before each allocation.

| Build target | Required checkpoint | Gate IDs | Known storage prerequisite |
|---|---|---|---|
| `qwen3.6-35b-a3b` | `Qwen/Qwen3.6-35B-A3B-FP8` | agentic-webserver, vision-fidelity, ttft-warm-gate, ttft-cold-gate, bfcl-subset-echolp, ssm-state-poisoning-gate | 37,463,662,160 weight bytes, plus metadata; D3 pin `95a723d08a9490559dae23d0cff1d9466213d989` |
| `qwen3.8-27b` | `unsloth/Qwen3.8-27B-NVFP4` | bfcl-subset, decode-floor, concurrency-sweep, concurrency-sweep-dflash2 | 23,444,511,857 full repository bytes, including MTP; overnight pin `57926baca9a82b4d6906b43f2750d55315f5b10f` |
| `qwen3.6-27b` | `unsloth/Qwen3.6-27B-NVFP4` | video-fidelity | Exact size and revision still need metadata inventory |
| additional draft, same qwen3.8 binary | `incoai/Qwen3.8-27B-DFlash2` | concurrency-sweep-dflash2 | Exact size/revision unverified; baseline pins gamma8 and exact draft HF ID |

Source: [required set](</Users/tom/Documents/New project/atlas-campaign-code/crates/atlas-plugin/src/gate/mod.rs:82>), [35B defaults](</Users/tom/Documents/New project/atlas-campaign-code/kernels/gb10/qwen3.6-35b-a3b/BENCH.toml:18>), [27B defaults](</Users/tom/Documents/New project/atlas-campaign-code/kernels/gb10/qwen3.8-27b/BENCH.toml:107>), [video default](</Users/tom/Documents/New project/atlas-campaign-code/kernels/gb10/qwen3.6-27b/BENCH.toml:297>). Links use workspace files; the machine-readable inventory pins HEAD.

## Build and command plan

After the final perf-path change is committed and tagged, build from an owned clean Spark1 checkout at that exact tag. Reuse `/home/pidtom/atlas-hopper-gate-full/target` through `CARGO_TARGET_DIR`; never change the warm checkout. Verify free space first: the reported ~12GiB free on Spark1 does not prove a fresh release build will fit. Do not delete shared cache data to make it fit.

`ATLAS_TARGET_MODEL` accepts one literal model or `*`, not a comma-separated list ([build.rs](</Users/tom/Documents/New project/atlas-campaign-code/crates/atlas-kernels/build.rs:1039>)). Three targeted builds avoid compiling unrelated targets and preserve the model identity for 3.6 versus 3.8. Each reuses the same cargo target directory; copy its resulting binary before starting the next. `ATLAS_TARGET_QUANT=nvfp4` is the kernel bundle even for the FP8 checkpoint. No GPU work is involved in nvcc emitting PTX.

```sh
# Execute from the owned, clean checkout of the final gate tag on Spark1.
# GATE_BIN_DIR is an owned directory whose size is accounted for.
for GATE_MODEL in qwen3.6-35b-a3b qwen3.8-27b qwen3.6-27b; do
  env -u ATLAS_SKIP_BUILD \
    ATLAS_TARGET_HW=gb10 ATLAS_TARGET_MODEL="$GATE_MODEL" \
    ATLAS_TARGET_QUANT=nvfp4 CUDARC_CUDA_VERSION=13000 \
    CARGO_TARGET_DIR=/home/pidtom/atlas-hopper-gate-full/target \
    cargo build --release --locked -p spark-server --bin spark || break
  cp /home/pidtom/atlas-hopper-gate-full/target/release/spark \
    "$GATE_BIN_DIR/spark-gb10-$GATE_MODEL" || break
  sha256sum "$GATE_BIN_DIR/spark-gb10-$GATE_MODEL"
done
```

`ATLAS_SKIP_BUILD` must be unset; leaving the CPU-test value active makes a stub, not a GPU binary. Preserve build stdout/stderr, exit, wall time, binary SHA, git/tag identity, driver/toolchain versions and disk snapshots. Stop a failing build and retain its result; do not treat an older binary as the tagged build. The default features already are CUDA+NCCL ([Cargo.toml](</Users/tom/Documents/New project/atlas-campaign-code/crates/spark-server/Cargo.toml:9>)).

The source-supported gate invocation is one process per gate:

```sh
"$GATE_BIN_DIR/spark-gb10-qwen3.6-35b-a3b" benchmark run agentic-webserver --hardware gb10 --pull-request-gate --yes
"$GATE_BIN_DIR/spark-gb10-qwen3.6-35b-a3b" benchmark run vision-fidelity --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.6-35b-a3b" benchmark run ttft-warm-gate --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.6-35b-a3b" benchmark run ttft-cold-gate --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.6-35b-a3b" benchmark run ssm-state-poisoning-gate --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.6-35b-a3b" benchmark run bfcl-subset-echolp --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.8-27b" benchmark run decode-floor --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.8-27b" benchmark run concurrency-sweep --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.8-27b" benchmark run concurrency-sweep-dflash2 --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.8-27b" benchmark run bfcl-subset --hardware gb10 --pull-request-gate
"$GATE_BIN_DIR/spark-gb10-qwen3.6-27b" benchmark run video-fidelity --hardware gb10 --pull-request-gate
```

Do not paste historical explicit threshold parameters: the current baseline derives them. Do not use `--model` or `--url` with gate mode. Self-start has a 900-second boot cap, refuses when available system memory is below85%, and shuts down after each run ([bench_selfstart.rs](</Users/tom/Documents/New project/atlas-campaign-code/crates/spark-server/src/cli/bench_selfstart.rs:46>)).

## Runtime preparation and storage

1. Finish A2 and remove its owned containers/images/checkpoints before StepB model staging. Check and retain `nvidia-smi`, `pgrep -a -x spark`, `docker ps`, and `df -h /` before every GPU or disk-heavy step. Foreign occupancy stops StepB. At56GiB free, the 12GiB floor leaves44GiB for all new live allocations. The largest known checkpoint consumes34.89GiB, leaving only9.11GiB for metadata, environments, logs, image layers and temporary downloads. This is a capacity calculation, not an observed fit.
2. Reuse an owned HF cache across one model group at a time. Set `HF_HUB_CACHE`, `HF_HOME`, `HF_XET_CACHE`, `HF_ASSETS_CACHE`, `ATLAS_HOME`, `PIP_CACHE_DIR`, `ATLAS_WARM_TARGET_DIR` and `ATLAS_WARM_TEMPLATE_DIR` to owned paths. Count every allocated directory and image. Keep each model's complete pinned snapshot plus an owned `refs/main` containing that same40SHA, and retain a manifest/hash of actual loaded files. No unrelated/sibling snapshots may be present.
3. **Do not pin these gate loads using extra `--serve-override model_from_path=...` or `cache_dir=...`.** The current recipe renderer permits additions, but [scoring.rs](</Users/tom/Documents/New project/atlas-campaign-code/crates/atlas-plugin/src/gate/scoring.rs:83>) rejects every override not pinned in BENCH.toml. Likewise replacing the DFlash2 draft ID with a filesystem path makes its record fail the required exact override. The isolated cache/ref solution preserves canonical argv. Fail if the selected revision has no complete weights; do not let sibling fallback choose another snapshot.
4. Populate the owned recipe index with `ATLAS_HOME="$GATE_STATE" "$GATE_BIN_DIR/spark-gb10-qwen3.6-35b-a3b" sync-recipes`, then retain the index SHA and its `tree_sha` and inspect the six required recipe IDs from `prerequisites.json`. The fetch source is explicitly `Avarok-Cybersecurity/atlas-recipes` ([fetch.rs](</Users/tom/Documents/New project/atlas-campaign-code/crates/spark-server/src/recipe/fetch.rs:55>)). Stop an absent recipe, model mismatch or unknown flag; do not substitute a superficially similar campaign recipe. Several required recipe IDs have no local fixture, so fixtures alone do not prove the live index is complete.
5. BFCL provisions pinned `bfcl-eval==2026.3.23` into the owned ATLAS_HOME; Python>=3.10, venv and pip must work. Vision/video bytes are embedded. Video additionally requires ffmpeg in the serving environment and `video_allow_ffmpeg=true` in the resolved recipe; 13 passed, zero skipped and control-held are required. Missing ffmpeg is a measured block, not a reason to accept GIF-only output.
6. Agentic additionally prewarms debug+release Axum projects and needs cargo/rustc/linker, sh, curl, timeout, setsid, fuser and kill. Its warm targets can consume the remaining space; inventory their growth before the35B load. If that combination cannot retain12GiB, record the agentic storage block and continue the other gates.

Sequential deletion can keep current occupancy under70GB of new usage, but does not bound cumulative downloaded bytes. Even the two known main payloads sum to60.9GB before the third model, draft and dependencies. No claim that all checkpoints fit together is justified. Exact sizes of the third model and draft must be obtained before those stages.

## Agentic boundary

The actual driver uses inherited-environment `sh -c`, not an OS sandbox ([agent_shell.rs](</Users/tom/Documents/New project/atlas-campaign-code/crates/atlas-plugin/src/benchmarks/agentic/agent_shell.rs:49>)); its path helper explicitly says bash is unconfined ([agent_path.rs](</Users/tom/Documents/New project/atlas-campaign-code/crates/atlas-plugin/src/benchmarks/agentic/agent_path.rs:15>)). The user's instruction already authorizes running this benchmark and the necessary reversible isolation setup. No further permission is implied by the CLI's `--yes`.

Use a disposable container with a private PID namespace and private bridge network, no host networking, host PID namespace, privileged mode, Docker socket, home directory, SSH keys/agent, or Git credentials. Mount only the owned final-tag checkout and model cache read-only and owned artifact/build/output directories writable; record outputs may use owned `.benchmarks` and `.github/record-signers` binds. Give the container its own normal user and toolchain. Keep credentials out of its environment. Preserve the recipe/gate flags and CPU resources; isolation setup must not quietly change benchmark thresholds or hide tool failures. Prove the boundary first using a harmless host-only canary that must be unreadable, while an owned workspace file must be writable and generated-server traffic works inside the private namespace. If the environment cannot both confine the shell and provide dependencies inside the disk limit, record an agentic prerequisite block; do not run unconfined model shell on the shared host. No such container was built or run in this assessment.

## Red-first checks and stopping rule

Before GPU work, the final binary's `benchmark --pull-request-gate-check --pr 895` should refuse stale/missing records; capture that red output as the gate oracle. A deliberately nonexistent `--checkpoint` with a registered gate should also refuse before any weights load. Do not use fail-open flags or alter thresholds.

A fresh TTFT store first returns INFO because it has no same-box baseline; that is not PASS. Retain the INFO run and, only for this documented baseline-establishment condition, run the unchanged gate once more against the established same-box baseline. Never retry a FAIL until it turns green; the code correctly refuses to store a regressed result ([ttft_verdict.rs](</Users/tom/Documents/New project/atlas-campaign-code/crates/atlas-plugin/src/benchmarks/ttft_verdict.rs:14>)).

Per gate stop after one completed PASS/FAIL or documented boot/prerequisite failure, then move to the next eligible gate. Retain stdout/stderr/exit/wall time, raw artifacts and signed `.benchmarks/<id>/*.json` + `.sig`; a new owned signing identity also creates `.github/record-signers/*.pub`. Incomplete runs must not produce usable records. Verify the exact registration path before staging it from command output.

The eleven newest historical default-model records sum to17473seconds (4h51m13s); the two BFCL runs alone are4h04m37s. Boot, download and fresh dependency preparation are additional. These are timing hints from older GB10 runs, not current measurements. End when all eleven gate verdicts or explicit blocks are recorded, the full current-tree gate check is observed, and every owned Spark2 asset is removed with final df evidence. A source change after the gate tag invalidates the prior run's applicability and requires a new tag/run; never relabel it.
