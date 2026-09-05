# Vast.ai: eight-hour, two-H100 SXM pilot

Planning snapshot: 2026-09-05, campaign code `8d125b31d291bdbfe0185894b5e9f3c6dceab8a4`.
Tom confirmed that the quoted $3.965/hour covers **both H100 SXM GPUs**, 500 GB
instance disk and a separate 500 GB volume. No rental has been made. This is a
preparation plan, with no H100 performance or runtime results.

**Booking decision: HOLD until the execution environment, selected binaries and
launch identity checks below are proven.** The earlier 2–4 engineering-hour
estimate preceded discovery of the Vast execution gap; it is not a reliable
remaining-time estimate. The exact offer ID/template, CPU architecture and
allocation, RAM, shared memory, network rates and exposed GPU topology remain
to be checked. This pilot is a user-selected alternative to the PRD's first
H200/27B cell; it does not replace or certify that scoring row.

## Cost and storage

| Item | Calculation from the supplied quote | Estimate |
|---|---|---:|
| Eight hours, complete quoted allocation | 8 × $3.965 | $31.72 |
| 100 GB of total billable traffic | 0.100 TB × $13.654 | $1.37 |
| 200 GB of total billable traffic | 0.200 TB × $13.654 | $2.73 |
| 500 GB of total billable traffic | 0.500 TB × $13.654 | $6.83 |
| Eight hours plus 200 GB traffic | $31.72 + $2.7308 | $34.45 |
| One additional GPU hour | quoted total | $3.965 |

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
disk occupancy. The 500 GB volume has room for this selected model set, subject to
measured temporary space. Avoid staging the entire campaign. See the pinned
[model assets](evidence/vast-h100-8h-20260905/model-assets.json).

The screenshot allocates both 500 GB disk and 500 GB volume. Measure the prepared
image footprint before choosing a smaller instance disk; keep the shared models
on the volume. Dropping the separate volume would save only about $1.11 over eight
hours at this quote. Keeping it for another day costs about $3.33, using the quoted
daily rate. Choose retention deliberately after exporting the small result bundle.

Vast volumes are tied to a physical host, so keeping one does not reserve the GPUs
or make it attachable elsewhere. The current documentation supports cloud-to-volume
copy, which may permit advance staging after a host is selected; that path and its
traffic/storage charges must be verified before relying on it. Direct local-machine
to-volume copying is unsupported. Do not assume free staging or a resumable GPU
reservation. [Vast volumes](https://docs.vast.ai/guides/instances/storage/volumes).

## Work to finish before booking

| Prerequisite | Evidence required / oracle | Current state and stopping rule |
|---|---|---|
| Run both engines in the actual Vast environment | A prepared immutable image/environment runs Atlas and vLLM sequentially as owned processes. CPU tests first reject failed launch, stale/PID-reused ownership, wrong revision and failed boot; then prove cleanup and successful identity capture. | **P0 OPEN.** Standard Vast container rentals cannot run nested Docker; the current vLLM launcher requires it. No paid experiment until this integration is tested. |
| Preserve artifact identity in process mode | Actual executable/version, environment digest, observed argv and model snapshot, process start identity and boot evidence reach the existing validator. Foreign/stale evidence must remain uncertifiable. | **P1 OPEN.** Current model launch evidence is Docker-specific. A shell wrapper alone does not close this gap. Do not fabricate Docker inspection records. |
| Pin the Qwen executable and runtime | Host-compatible Atlas release binary built with `ATLAS_TARGET_HW=hopper`, `ATLAS_TARGET_MODEL=qwen3.6-35b-a3b`, selected quant bundle; SHA256 and PTX receipt at the frozen code tree. Resolve CUDA/NCCL dependencies in the prepared environment. | **OPEN.** The first recovered x86 artifact targets Super. Compile and link Qwen off the GPU clock, then verify its build receipt. |
| Pin vLLM and parser support | Exact image/environment digest; CPU import/registration of the Qwen model and `qwen3_xml` / `qwen3` parsers in that environment, including dependency versions. | **OPEN.** An official recipe and source registry are available; selected-image support is unobserved. Never install an untested upgrade during the rental. |
| Stage and identify shared model bytes | Qwen revision `95a723d08a9490559dae23d0cff1d9466213d989`; hash-verified snapshot plus tokenizer/config/template files; both engines' actual load paths resolve there. | **OPEN.** Metadata pinned; rental cache not staged. Missing or conflicting identity blocks a scored comparison. |
| Prove the revised driver off the GPU clock | Existing CPU gates plus red-first process-mode, deadline and artifact tests; frozen ladder unchanged; known-bad OSL/think/spec comparisons refused. | Existing Docker path is tested; Vast path is not. Stop preparation at the first failed dependency, record and fix it before booking. |
| Verify exact offer and stop mechanism | Two assigned H100 SXM GPUs, compatible host/driver, adequate actual CPU/RAM/shared memory, sufficient local storage and bandwidth; provider-level deadline stop tested independently of the engine process. | **OPEN.** Price screenshot alone cannot establish these. No paid API action is authorized by this plan. |

The provider incompatibility is a source-based finding, not an observed failed Vast
instance. [Vast's container FAQ](https://docs.vast.ai/guides/instances/manage-instances#can-i-run-docker-inside-my-instance)
rules out nested Docker. At the recorded code SHA,
[`vllm_render.py:190–208`](https://github.com/TheTom/atlas/blob/8d125b31d291bdbfe0185894b5e9f3c6dceab8a4/bench/campaign/vllm_render.py#L190)
constructs `docker run`, and
[`model_launch_capture.py`](https://github.com/TheTom/atlas/blob/8d125b31d291bdbfe0185894b5e9f3c6dceab8a4/bench/campaign/model_launch_capture.py)
requires container inspection evidence. The retained
[vLLM Qwen dry render](evidence/vast-h100-8h-20260905/current-vllm-qwen3.6-35b-a3b-fp8.dryrun.log)
exits 0 but still emits Docker commands. It is not a Vast execution proof.

Vast also offers VMs, but they are not an assumed workaround: the volume guide
currently excludes VM attachment, and Vast's host guidance warns about datacenter
GPU P2P/NVLink support in VMs. Any VM alternative needs its own verified offer and
topology evidence. [VM guide](https://docs.vast.ai/guides/instances/virtual-machines),
[multi-GPU VM guidance](https://docs.vast.ai/host/vms).

## Model order and scope

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

These are work ceilings and priorities, not predictions of first-silicon speed.
Eight hours is a maximum; a conclusive failure can end the booking early.

| Elapsed time | Work | Oracle / stopping rule |
|---|---|---|
| 00:00–00:20 | Record GPU UUIDs, `nvidia-smi -q`, `nvidia-smi topo -m`, driver, CPU/RAM/shared memory, filesystem capacity and model/image hashes. Run the prepared short P2P/NCCL check before a two-GPU cell. | Expected assigned devices and functioning communication. Hardware/environment mismatch: export evidence and stop. No driver/toolchain installation. |
| 00:20–01:45 | First Qwen lat C1 pair, architecture/kernel audit, boot, hardened coherency, ladder and paired artifacts. Add vLLM A/A for this shape only after both legs pass. | Each engine has at most one 30-minute boot attempt with the frozen flags. Failure is a result; try the other engine, not new flags. If there is no valid primary pair by hour 2, export and stop rather than start Super. |
| 01:45–03:30 | Remaining Qwen shapes, prioritizing a complete A/B row over another unpaired run, then remaining vLLM A/A cells. | Same model bytes, GPU, think/spec policy and valid output lengths. Keep failed/missing rows explicit. Use observed boot/cell durations to decide what fits. |
| 03:30–06:30 | Super on both GPUs only if its profile/environment was frozen before rental and the Qwen pair passed. Start with lat C1, then C16, then agent shapes as time allows. | Both engine boots/coherency must pass before a performance claim. No new model after 05:00; keep at least 90 minutes for a pair, plus final export time. |
| 06:30–07:15 | Close the most valuable outstanding pair or A/A check; assemble and validate all artifacts. | A compare exit 0 alone is insufficient: inspect row verdicts and validator output. No new model or environment change. |
| 07:15–07:45 | Final incremental export, local hash verification, receipt/index review, provider-level stop. | Verify the evidence exists off-instance before deletion and verify the provider reports stopped. Keep uploading small evidence bundles throughout the run. |
| 07:45–08:00 | Reserved margin for stop confirmation and cleanup. | GPU billing must cease before hour 8. Delete owned instance/volume after verified export unless retention is explicitly chosen; record actual charges. |

If model files are not staged before activation, download Qwen first and measure
actual throughput. At 1 Gbit/s its 37.49 GB repository has a theoretical minimum
of about five minutes; Qwen plus Super takes about 22 minutes. Protocol, hashing
and storage overhead increase these times. Refuse a download whose projected
space or completion time consumes the experiment/export reserve. Never overlap
downloads or heavy hashing with a scored ladder. At one hour, an unresolved
environment/setup problem ends the booking; do not use the remaining seven hours
for package or launcher debugging.

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
are captured; the new Vast process integration, targeted Qwen environment and
two-GPU Super profile are **not implemented or runtime-validated**. PR895 CI at
this snapshot still has queued checks. A2/B/D1 GPU work remains as reported in
[LEAD-RECOVERY-REPORT.md](LEAD-RECOVERY-REPORT.md).

Publication checks passed: campaign 77, launcher 30, Dockerfiles 17, Atlas renderer
329, vLLM renderer 253, validator 26, assembler 8 and Spark 1 CPU PTX suite 7;
formatting, typos and local PTX-script shellcheck also passed. These validate the
existing code, not the proposed Vast adapter. See the
[validation receipt](evidence/vast-h100-8h-20260905/validation.json).

The targeted Qwen Hopper x86 build was dispatched on the authorized fork at the
recorded code SHA and is in progress:
[build run 33978523017](https://github.com/TheTom/atlas/actions/runs/33978523017).
Its artifact and runtime dependencies remain unverified; no GPU was rented.

The next preparation milestone is a tested, downloadable Qwen execution bundle
with a complete dry rehearsal through the artifact validator. Re-estimate booking
readiness after that milestone. This plan itself is not a green light to rent.
