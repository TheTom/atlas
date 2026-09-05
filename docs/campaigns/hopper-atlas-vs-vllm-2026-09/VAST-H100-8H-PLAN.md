# Vast.ai: eight-hour, two-H100 SXM pilot

Planning snapshot: 2026-09-05, campaign code `05475310694ef0469824813e62282eb0c33d3873`.
Tom's updated quote is **$3.789/hour for both H100 SXM GPUs and 300 GB of instance
disk, with no separate volume**. This replaces the earlier 500 GB disk plus
500 GB volume configuration. Tom is proceeding with the rental and has authorized
code staging, model download and on-node fixes/rebuilds. Connection details and
activation time are still pending; no H100 performance or runtime results exist.

**Purpose: a shakedown with room to diagnose, fix and rebuild on the node.** Eight
hours is the total rental budget, including setup and export. Full campaign scoring
can follow once the hardware and engine paths have been observed. The exact offer ID/template, CPU architecture and
allocation, RAM, shared memory, network rates and exposed GPU topology remain
to be checked. This pilot is a user-selected alternative to the PRD's first
H200/27B cell; it does not replace or certify that scoring row.

## Cost and storage

| Item | Calculation from the supplied quote | Estimate |
|---|---|---:|
| Eight hours, complete quoted allocation | 8 × $3.789 | $30.31 |
| 100 GB of total billable traffic | 0.100 TB × $13.654 | $1.37 |
| 200 GB of total billable traffic | 0.200 TB × $13.654 | $2.73 |
| 500 GB of total billable traffic | 0.500 TB × $13.654 | $6.83 |
| Eight hours plus 200 GB traffic | 8 × $3.789 + $2.7308 | $33.04 |
| Saving against the previous eight-hour allocation | 8 × ($3.965 − $3.789) | $1.41 |
| One additional GPU hour | quoted total | $3.789 |

Use **$35–40 as a planning allowance**, not an approved spend or a billing cap.
Traffic includes both directions: 100 GB received plus 100 GB sent is 200 GB.
Model bytes, image layers, retries and any external staging service all count
toward the actual budget. The displayed component rates have rounding differences;
the calculation uses the displayed total. Vast meters active rental by the second
and storage continues while an online instance is stopped. Export results and
verify resource deletion after use; killing `spark` does not stop GPU billing.
[Vast billing](https://docs.vast.ai/guides/reference/billing).

Keep one verified checkpoint copy shared by the two engine legs. Qwen plus Super
requires about **165.87 decimal GB** of repository files before images, caches and
scratch; the optional Nano adds 32.70 GB. These are metadata estimates, not measured
disk occupancy. Against the nominal 300 GB allocation, Qwen plus Super leaves
about **134.13 GB** for the runtime/image, caches, scratch and filesystem overhead.
Confirm actual free space with `df` before and after each download; do not infer
usable space from the offer's capacity label. Avoid staging the entire campaign. See the pinned
[model assets](evidence/vast-h100-8h-20260905/model-assets.json).

Prepare binaries, environments and the pinned transfer manifest before arrival.
Once the instance is available, download Qwen into one task-owned cache on its
disk and have both engines load that snapshot. Budget transfer and verification
time inside the eight-hour window. There is no volume to pre-stage or retain.
Fetch Super only when its profile is ready and measured free space can cover its
files, temporary downloads and runtime caches. If that space is unavailable,
finish and export the Qwen evidence before removing only its owned checkpoint;
otherwise leave Super unrun. Do not duplicate checkpoints for separate engines or
create a volume as a fallback.

Export small result bundles throughout the run and verify the final copy before
destroying the instance: destruction removes its disk data. Stopping preserves
the data but continues storage charges; the updated quote lists disk at
$1.334/day. The default end-of-run plan is verified export followed by destruction
of the owned instance. [Vast instance lifecycle](https://docs.vast.ai/guides/instances/manage-instances).

## Work to finish before measurement

| Prerequisite | Evidence required / oracle | Current state and stopping rule |
|---|---|---|
| Run both engines in the actual Vast environment | Atlas and vLLM run sequentially as owned processes. CPU tests first reject failed launch, stale/PID-reused ownership, wrong revision and failed boot; then prove cleanup and successful identity capture. | Process integration is implemented locally and completing regression checks. Actual Vast execution remains unobserved. |
| Preserve artifact identity in process mode | Actual executable/version, environment digest, observed argv and model snapshot, process start identity and boot evidence reach the existing validator. Foreign/stale evidence must remain uncertifiable. | Owned-process model evidence is tested; actual vLLM immutable build identity remains open. Do not fabricate Docker inspection or pass a Python interpreter hash as the engine build. |
| Pin the Qwen executable and runtime | Host-compatible Atlas release binary built with `ATLAS_TARGET_HW=hopper`, `ATLAS_TARGET_MODEL=qwen3.6-35b-a3b`, selected quant bundle; SHA256 and PTX receipt at the frozen code tree. Resolve CUDA/NCCL dependencies in the prepared environment. | Qwen artifact at `8d125b31` downloaded and checksum verified. It requires glibc 2.39, CUDA 13 and NCCL. On-node builds are expected for fixes and additional model targets. |
| Pin vLLM and parser support | Exact environment inventory and immutable package/source identities; CPU import/registration of the Qwen model and `qwen3_xml` / `qwen3` parsers in that environment, including dependency versions. | **OPEN.** Inspect the actual rental environment, then install a specific version into a separate venv when needed. Retain installation output and resolved dependencies; a bare moving `pip install vllm` is insufficient provenance. |
| Freeze model transfer and load identity | Qwen revision `95a723d08a9490559dae23d0cff1d9466213d989`; pinned transfer manifest including tokenizer/config/template files, one instance-disk cache and explicit snapshot paths for both engines. | Downloader passes 21 offline tests and four negative mutations. Download and byte verification occur after activation; no weights have been downloaded. Missing or conflicting identity blocks a scored comparison. |
| Prove the revised campaign runner | Existing CPU gates plus red-first process-mode and artifact tests; frozen ladder unchanged; known-bad OSL/think/spec comparisons refused. | Real Linux CPU ownership/interruption tests pass; completing final integration checks. GPU behavior and provider-level shutdown remain unobserved. |
| Verify exact offer and stop mechanism | Two assigned H100 SXM GPUs, compatible host/driver, adequate actual CPU/RAM/shared memory, sufficient local storage and bandwidth; provider-level deadline stop tested independently of the engine process. | **OPEN pending connection.** Tom is renting the instance. Track the eight-hour deadline from actual activation, not first SSH access. |

The provider incompatibility is a source-based finding, not an observed failed Vast
instance. [Vast's container FAQ](https://docs.vast.ai/guides/instances/manage-instances#can-i-run-docker-inside-my-instance)
rules out nested Docker. At the recorded code SHA,
[`vllm_render.py:190–208`](https://github.com/TheTom/atlas/blob/8d125b31d291bdbfe0185894b5e9f3c6dceab8a4/bench/campaign/vllm_render.py#L190)
constructs `docker run`, and
[`model_launch_capture.py`](https://github.com/TheTom/atlas/blob/8d125b31d291bdbfe0185894b5e9f3c6dceab8a4/bench/campaign/model_launch_capture.py)
requires container inspection evidence. The retained
[vLLM Qwen dry render](evidence/vast-h100-8h-20260905/current-vllm-qwen3.6-35b-a3b-fp8.dryrun.log)
exits 0 but still emits Docker commands. It is not a Vast execution proof.

Vast also offers VMs. Removing the volume eliminates the earlier volume-attachment
constraint, but Vast's host guidance still warns about datacenter GPU P2P/NVLink
support in VMs. Any VM alternative needs its own verified offer and
topology evidence. [VM guide](https://docs.vast.ai/guides/instances/virtual-machines),
[multi-GPU VM guidance](https://docs.vast.ai/host/vms).

## Model order and scope

Claude's plan and rental kit were inspected on September 5, including his
[campaign handoff](https://github.com/Avarok-Cybersecurity/atlas/issues/899#issuecomment-5553224414).
Adopt his on-node rebuild loop, CUDA fault diagnostics, short profiling captures
and continuous result export. His RTX measurements were 3m45s cold and 55s warm
on 128 vCPUs, with a 1.2 GB target directory; these are observations from another
host, not promised H100 build times. His setup estimates also exclude the actual
rental's download and installation variability.

The plans differ in model order: his starts Nano NVFP4 for the cheap loader/kernel
audit, then Nano FP8 for the control, then Super. Our first pinned Qwen checkpoint
and matching binary are ready, so Qwen stays the first download. Nano remains a
targeted diagnostic if its earlier refusal needs reproducing. Do not compare
Atlas Nano NVFP4 against vLLM Nano FP8 as a same-checkpoint pair. Super remains
conditional on the complete two-GPU recipe and process path.

Keep compilation available throughout the booking. Prefer the CUDA 13 devel,
Ubuntu 24.04 environment used by the repository Dockerfile; inspect the rented
image and host driver before installing missing userspace dependencies. CUDA
toolkit installation inside the container cannot upgrade the host driver. Retain
the pinned Rust toolchain, source checkout and one reusable Cargo target directory
on the instance disk. Account for toolkit, Cargo registry/build artifacts, vLLM
venv and diagnostic traces in the measured disk reserve.

For each fix: retain the failing command/output, make a focused change on an
isolated `codex/rental-h100-20260905` branch, run its regression, then rebuild with
`ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL=<selected-model> ATLAS_TARGET_QUANT=nvfp4`
and `cargo build --locked --release -p spark-server --bin spark --no-default-features
--features cuda,nccl`. Preserve the previous executable; record source commit,
dirty diff if any, compiler versions, elapsed time, target-directory size and the
new executable SHA256. Re-run the failed gate with the same recipe. Integrate only
reviewed fixes into PR895, following the exact repository/fork guards. Every
change under perf paths requires a new gate-tip identity; never pool pre-fix and
post-fix measurements.

Claude's diagnostic kit is useful for investigation, with limits: missing
logprobs makes the token oracle unavailable; the first divergent token does not
by itself identify a faulty kernel, and raw completions only narrow the template
hypothesis. Sanitizer or profiler runs are diagnostic evidence and are excluded
from performance rows. Use the frozen campaign ladder for comparisons.

1. **First defensible pair: Qwen3.6-35B-A3B-FP8, one H100 per engine leg,
   spec off, think off.** Both current recipes are single-GPU profiles. Run the
   engines sequentially on the same assigned GPU. This buys a small-model Hopper
   runtime/coherency/instrument proof before risking a 128 GB model load. The other
   GPU can remain idle; simultaneously measuring both engines would share host
   resources and complicate the comparison. [Official Qwen H100 recipe](https://recipes.vllm.ai/Qwen/Qwen3.6-35B-A3B-FP8/hw/h100.json).
2. **Two-GPU follow-on: Nemotron-3-Super FP8, conditional.** A complete NVIDIA
   cookbook profile exists for 2×H100 with vLLM 0.17.1, TP2/PP1/DP1, TRITON_ATTN and
   the `super_v3` plugin. Its source is pinned at commit
   `1118307315f77e4498212865c050d104cb0870e9`. This must be a separate frozen profile;
   merely changing TP8 to TP2 in the current catalog mixes recipes. Atlas's current
   H100 counterpart is EP2/TP1. Keep speculation off and thinking matched; resolve
   the cookbook's alias, port, effective context and prefix-cache policy before
   scoring. Prepare the separate environment and parser off the clock. If any
   prerequisite remains open, leave Super unrun. [NVIDIA cookbook](https://github.com/NVIDIA-NeMo/Nemotron/blob/1118307315f77e4498212865c050d104cb0870e9/usage-cookbook/Nemotron-3-Super/vllm_cookbook.ipynb).
3. **Nano is a conditional fallback, not a default third download.** Its GB10 Atlas
   coherency diagnosis and vLLM parser provisioning remain unresolved. Resolve those
   cheaply first. GLM, Kimi, MiniMax, H200 and B200 rows are outside this booking.

Use the frozen shapes: lat 1024/256 and agent 4096/512, C=1 and C=16,
one warmup plus three measured repetitions. Preserve current percentile semantics,
retain raw JSON and label any incomplete row. A full Qwen set with vLLM A/A and one
Atlas pass is **12 cell invocations**. The current runner boots and tears down per
cell; budget for 12 boots, not three. Do not silently introduce engine reuse or
shorten repetitions to fit the schedule. Estimate the remaining cells from actual
first-cell timings, then drop lower-priority cells if needed.

## Eight-hour schedule, measured from activation

These are priorities and decision points, not predictions of first-silicon speed.
Eight hours is a maximum; useful debugging is part of the booking. The earlier
blanket stop at hour one for setup or hour two without a passing pair is withdrawn.

| Elapsed time | Work | Oracle / stopping rule |
|---|---|---|
| 00:00–00:45 | Record GPU UUIDs, `nvidia-smi -q`, topology, driver, CPU/RAM/shared memory and actual disk quota. Stage source, build tools and verified Qwen binary while the pinned checkpoint downloads. Start incremental export. | Require the assigned idle H100s and a CUDA 13-capable host driver. Measure throughput/setup time; this is a target, not a claim that downloads finish in 45 minutes. |
| 00:45–02:00 | Architecture/kernel audit, first Qwen requests, coherency on both engines, first lat C1 pair if green. | Preserve each failed boot/coherency result. A frozen build gets one attempt capped at 30 minutes; a code fix starts a separately identified diagnostic attempt. |
| 02:00–04:00 | Diagnose and rebuild focused fixes; complete the first useful pair and its vLLM A/A check. | Each debugging cycle needs a concrete hypothesis, reproduction and bounded next check. Reassess every 30 minutes; stop a blocked line of work when no informative next experiment fits. |
| 04:00–06:30 | Complete remaining Qwen shapes or test Super on both GPUs if its recipe/process environment is ready and disk/time permit. | Prioritize a trustworthy completed pair over breadth. No new model after 05:00; use measured transfer/build/boot times and retain export reserve. |
| 06:30–07:15 | Close the most valuable outstanding pair or diagnostic reproduction; assemble and validate all artifacts. | A compare exit 0 alone is insufficient: inspect verdicts and validator output. No new model or long rebuild; preserve incomplete work and its reproduction. |
| 07:15–07:45 | Final incremental export, local hash verification, receipt/index review, provider-level stop. | Verify the evidence exists off-instance before deletion and verify the provider reports stopped. Keep uploading small evidence bundles throughout the run. |
| 07:45–08:00 | Reserved margin for stop confirmation and cleanup. | GPU billing must cease before hour 8. Destroy the owned instance after verified export; record actual charges. No volume is created or retained. |

Download Qwen first after activation and measure actual throughput. At 1 Gbit/s
its 37.49 GB repository has a theoretical minimum
of about five minutes; Qwen plus Super takes about 22 minutes. Protocol, hashing
and storage overhead increase these times. Refuse a download whose projected
space or completion time consumes the experiment/export reserve. Never overlap
downloads, compilation, package installation or heavy hashing with a scored
ladder. The decision to continue debugging depends on the observed failure and
the next useful experiment, while the eight-hour deadline remains fixed.

## Evidence and readiness status

Every attempted cell retains engine/binary identity, image/environment digest,
actual serve argv and selected environment, pinned model load proof, GPU/driver
snapshot and SHA256, harness SHA, boot/coherency JSON, raw ladder JSON, comparison,
section-10 artifact and validator output. Record TTFT p50/p99, TPOT p50, token rate
and each gate's verdict directly from those artifacts. CPU compilation and the
earlier GB10 rehearsal remain separately labelled; neither is H100 evidence.

Preparation observed so far: six current H100 dry renders exit 0,
[with commands and exit codes](evidence/vast-h100-8h-20260905/current-render-receipt.json).
They include the unsuitable Super TP8 recipe. Source pins and payload estimates
are captured. The process integration now passes CPU tests, including real Linux
ownership and signal handling; the actual Qwen environment and two-GPU Super
profile remain unobserved/incomplete. A2/B/D1 GPU work remains as reported in
[LEAD-RECOVERY-REPORT.md](LEAD-RECOVERY-REPORT.md).

Current publication checks passed: campaign 80 on macOS and 78 on Linux (Linux
lacks shellcheck/typos, covered on macOS), launcher 30, Dockerfiles 17, Atlas
renderer 329, vLLM renderer 253, validator 26, assembler 16, and Spark 1 CPU PTX
suite 7. Process rendering has six cases; real Linux runner has two; process
ownership has eleven, including a separately installed pinned setproctitle
reproduction. The inventory correction passes 932 atlas-plugin tests and
workspace rustdoc. Formatting, typos and shellcheck pass. See the
[current validation receipt](evidence/rental-readiness-20260905/validation/receipt.json).
The test-only inventory change is under `crates/`, so the new perf identity is
`gate-tip-05475310`; no GPU perf records exist at that tag.

The targeted Qwen Hopper x86 build completed successfully on the authorized fork:
[build run 33978523017](https://github.com/TheTom/atlas/actions/runs/33978523017).
Its 75,814,080-byte executable has SHA256
`683f70e837519e6f91ed09fa23f6978a8c16e877477f5a762202c8963af09bce`.
The bundled checksum was verified after a deliberately wrong checksum failed.
ELF inspection found glibc 2.39, `libcublasLt.so.13`, `libcudart.so.13`,
`libcuda.so.1`, `libnccl.so.2` and `libibverbs.so.1` dependencies. This is compile
and link evidence; runtime compatibility will be observed on the rented node.

Next: stage the prepared bundle when SSH details arrive and observe the
real host. Missing immutable vLLM build identity remains a certification blocker;
do not relabel the Python interpreter hash as the engine build.
