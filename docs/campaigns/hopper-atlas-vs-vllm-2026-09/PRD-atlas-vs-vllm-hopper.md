# PRD: Atlas vs vLLM on NVIDIA datacenter GPUs — Hopper (H100 / H200) and Blackwell (B200)

| Field | Value |
|---|---|
| Status | Draft for execution (2026-09-04) |
| Audience | Eng, infra, sales engineering |
| Hardware | H100 SXM 80 GB (sm_90), H200 SXM 141 GB (sm_90), B200 SXM 180 GB (sm_100) |
| Challenger | Atlas Inference (`spark serve`), built from source for the target arch |
| Control | vLLM official recipe image + published flags for that model/SKU |
| Goal | Customer-facing receipts that the target models were tested on enterprise Hopper and Blackwell boxes |
| Companion PR | `hopper/sm90-target-tdd-2026-09` — adds `kernels/hopper` (sm_90a) and `kernels/b200` (sm_100a) targets, device-arch preflight, bench hardware ids, campaign driver |

## 0. What changed vs the first draft (evidence from the repo, 2026-09-04)

The first draft assumed an Atlas Hopper build exists and that every listed model is supported. Neither is true today. Everything below is corrected against the tree; file references are the oracle.

| Draft assumption | Repo evidence | Consequence |
|---|---|---|
| "Atlas (Hopper / SM90 build)" exists | Only NVIDIA target is `kernels/gb10/HARDWARE.toml` (`arch = "sm_121f"`). No `sm_90`, no fatbin, no H100 image; the only published image is `avarok/atlas-gb10` (aarch64). | Phase 0 (bring-up) added. Campaign cannot start until the companion PR compiles `sm_90a` / `sm_100a` PTX. |
| Qwen3.8-Flash-Next is P0 | The checkpoint is real (`Qwen/Qwen3.8-Flash-Next-FP8`, 125B, GDN + 512-expert MoE + 51B per-layer embedding, vLLM recipe needs nightly ≥ 0.29) but Atlas has no `qwen3.8-flash-next` target, `model_type`, or mention anywhere in the tree. Closest: `kernels/gb10/qwen3-next-80b-a3b`. | Demoted to **P2, blocked on a `spark-model` port**. Qwen3-Next-80B-A3B substitutes as the GDN+MoE representative. vLLM-only cells for Flash-Next are allowed as a reference row, labelled as such. |
| MiniMax M3 conditional | `MiniMaxAI/MiniMax-M3` exists with a vLLM recipe (427B/26B, H200+ only); the Atlas tree has MiniMax **M2.7** only (`kernels/gb10/minimax-m2-229b`). | Atlas row becomes M2.7; M3 is vLLM-only reference until ported. |
| NVFP4 vs FP8 quant choice open | `crates/spark-runtime/cuda/cutlass_nvfp4_gemm.cu` is gated `CUTLASS_ARCH_MMA_SM120/121_SUPPORTED`; `docs/adr/0004-nvfp4-fp8-quantization.md` says NVFP4 tensor cores are Blackwell-only. | Hopper A/B is **FP8 checkpoints only**. B200 A/B runs FP8 (parity with Hopper) and NVFP4 (Atlas's home quant, native on both engines). |
| vLLM baseline = whatever recipe says | `bench/ladder38/RESULTS.md`: with MTP on for both engines Atlas wins 2/8 rungs on GB10; the README "3.6× vs vLLM" came from a vLLM run with spec-decode off. | Spec-decode must be **on for both or off for both**; never mixed. Mixed cells are not publishable. |
| Super runs on 2×H100 | vLLM's recipe guide shows TP4 for Super FP8 and the model card claims 1×H200 fits; the recipe's rendered hardware JSON (re-checked 2026-09-05, `vllm-control/RECIPE-VERIFICATION.md`) is **H100 TP8, H200 TP8, B200 TP1**. The 2×H100 line is an NVIDIA cookbook variant. | Recipe-max Super boxes: 8×H100, 8×H200, 1×B200. Matched-topology rows: 4×H100 (guide) and 2×H100 (cookbook), footnoted. 1×H200 is a card claim, not a rendered profile. |
| 8×GPU nodes are routine | Every multi-GPU Atlas run to date is 2 ranks, one GPU per node, over RoCE (`docs/DEPLOYMENT.md:51-62`). NCCL env in `scripts/start-ep2.sh` disables NVLS/GDR and pins Ring (GB10 pessimizations). No intra-node NVLink run exists. | Topology ladder: 1 GPU → 2 GPU (TP or EP) → 4 → 8, each a gate. DeepSeek V4-Flash (EP only; `num_key_value_heads=1`) is the riskiest. |
| Thinking-off row is free | `kernels/gb10/nemotron-super-120b-a12b/MODEL.toml`: Super is thinking-first; forcing `enable_thinking=false` in the prompt "prematurely closes the think block" and degrades answers. | For Super the primary row is think-on with the reasoning parser stripping `<think>`; think-off is a secondary row and its coherency gate may fail legitimately. |

## 1. Summary

Enterprise buyers will not put Atlas in an RFP without datacenter data: measured TTFT, prefill/decode, concurrency and coherency on H100, H200 and B200. GB10 / Spark numbers are not Hopper or Blackwell data (the repo says so itself: `book/src/operations/benchmarks.md:132`).

This PRD defines a cost-controlled A/B, preceded by a test-driven bring-up:

1. Phase 0 — does Atlas compile for and boot on the box? (no A/B hardware needed for the compile half)
2. Phase A — does Atlas load the model and stay coherent?
3. Phase B — TTFT / TPOT / tok/s per user / node tok/s at frozen shapes.
4. Phase C — same node, same weights, same client, vLLM official recipe.

Win condition is an honest Pareto, not "always faster". A C=1 loss with a C=16 win is publishable if coherency passed.

## 2. Definitions

| Term | Meaning |
|---|---|
| Hopper | H100 / H200, compute capability 9.0, PTX `sm_90` / `sm_90a` |
| Blackwell DC | B200 / GB200, compute capability 10.0, PTX `sm_100` / `sm_100a`. B300 / GB300 are `sm_103` and out of scope until a box exists |
| Hopper data / Blackwell data | Benchmarks collected on those GPUs, never extrapolated from GB10 |
| Cell | One (engine, model, SKU, topology, workload, concurrency, spec on/off, think on/off) result |
| Certified | Boot + coherency + latency pack + matched vLLM A/B + JSON artifact, all on the same node within 24 h |
| Recipe-max | vLLM's published best flags for that model/SKU |
| Matched topology | Same GPU count and parallel layout on both engines; used when Atlas cannot run recipe-max, footnoted |
| Spec-matched | Speculative decoding on for both engines with the same draft depth, or off for both |
| Oracle | The named source that tells us a result is wrong (RST). Every gate below names one |

## 3. Scope

### 3.1 In scope

| Priority | Model | Checkpoint (A/B quant) | Atlas target dir | Default box |
|---|---|---|---|---|
| Plumbing | Nemotron 3 Nano 30B-A3B | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8` | `nemotron-3-nano-30b-a3b` | 1×H100, then 1×B200 |
| P0 | Nemotron 3 Super 120B-A12B | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8` | `nemotron-super-120b-a12b` | 8×H100 / 8×H200 (rendered recipe) with 4×H100 and 2×H100 matched rows → 1×B200 (rendered TP1) |
| P0 → **blocked** | Qwen3.6-35B-A3B (flagship, native FP8, MTP) | `Qwen/Qwen3.6-35B-A3B-FP8` | `qwen3.6-35b-a3b` — one NVFP4 MoE kernel fails to compile on sm_90a **and** sm_100a (see §12) | 1×H100, 1×B200 once the Sm90 / tcgen05 grouped GEMM lands |
| P1 | Qwen3-Next-80B-A3B (GDN + MoE stand-in for Flash-Next) | `Qwen/Qwen3-Next-80B-A3B-Instruct-FP8` | `qwen3-next-80b-a3b` | 2×H100 / 1×H200 / 1×B200 |
| P1 | DeepSeek V4-Flash | `deepseek-ai/DeepSeek-V4-Flash-0731` (FP8; vLLM has **no H100 recipe**) | `deepseek-v4-flash` | 8×H200, 8×B200 per recipe (Atlas EP only) |
| P1 (vLLM ref until ported) | GLM-5.3-Flash (~320B / 18B active) | `zai-org/GLM-5.3-Flash` FP8 | **none — `ATLAS_UNSUPPORTED`** (no `glm` `model_type` in `crates/spark-model/src/factory.rs`) | 4–8×H200, same booking as Flash-Next |
| Phase D, own booking | Kimi K3 (2.8T MoE, 16 of 896 experts active, KDA attention) | `moonshotai/Kimi-K3` **native MXFP4 QAT only** (MXFP4 experts + MXFP8 activations; attention / shared experts / lm_head higher precision; 1.56 TB weights). Never A/B a community W4A8 / INT4 requant against it | **`ATLAS_UNSUPPORTED` until it loads MXFP4 KDA + LatentMoE in 30 min** (no Kimi / KDA `model_type`; Atlas has no pipeline parallel) | **2×8 B200 (16 GPUs), TP8 + PP2, `--max-model-len 49152`.** Not 8×H200 (short 430 GB), not 8×B200 (short ~120 GB). Hopper-only customer: 16×H200 `--moe-backend marlin`, labelled "Hopper emulate" |
| Canary (vLLM ref) | GLM-4.5-Air FP8 (106B / 12B) | `zai-org/GLM-4.5-Air-FP8` | none | 2×H100 or 1×H200 |
| B200 extra | Any P0 model, NVFP4 checkpoint | `nvidia/*-NVFP4` per `MODEL.toml hf_id` | same | B200 only |

### 3.2 Conditional (Phase D only)

- MiniMax M2.7 (`MiniMaxAI/MiniMax-M2.7`, `kernels/gb10/minimax-m2-229b`) on 8×H200 — only if Super and Qwen3.6 are green and Atlas boots it inside 30 minutes. KV must stay BF16 per recipe fixture.
- Qwen3.8-Flash-Next (`Qwen/Qwen3.8-Flash-Next-FP8`, 250 GB FP8: 4×H100 + PLE CPU offload, 8×H200 TEP8, 4×B200) — Atlas cell only after a `spark-model` port lands (separate PR). vLLM reference row may be collected while the box is rented.
- MiniMax M3 (`MiniMaxAI/MiniMax-M3`, 8×H200 BF16 / 8×B200 NVFP4) — vLLM reference row only; Atlas has M2.7.
- Kimi K3 — one 16×B200 booking, one quant, one config. Scored row: spec **off** on both engines; DSpark is a second row only. Thinking and tool parsers on (`kimi_k3`). If Atlas cannot load MXFP4 KDA / LatentMoE inside 30 minutes, mark `ATLAS_UNSUPPORTED` and **do not rent the 16-GPU node** for an Atlas leg (the vLLM-only receipt can still be taken if a customer asked "do you run K3"). Atlas has TP + EP but no PP, so "same TP/PP" becomes matched GPU count with TP8 + EP2 and a footnote. This row is not part of the cheap Hopper campaign; Super / Flash-Next / GLM-5.3-Flash stay on 2–8 Hopper GPUs.
- GLM-5.3 (~743B / 39B active, `zai-org/GLM-5.3`, official Hopper default 8×H200 FP8) — **same 8×H200 rental as DeepSeek V4-Flash; pick one per booking or reuse the node overnight.** Atlas cell only if a GLM port boots inside 30 min; otherwise vLLM-only receipt. GLM-4.5 (358B) and any "GLM 3.5" are not on the list — there is no enterprise GLM 3.5 SKU; the line went 4.5 → 4.7 → 5 → 5.3.

### 3.3 Out of scope (separate PRD)

Qwen3.8-Max / Qwen3.8-2.4T-A95B (multi-node), DeepSeek V4-Pro, Kimi K3 as an Atlas cell (see §3.2 for its vLLM-reference row), B300/GB300 (`sm_103`), 1M-context sweeps, prefill/decode disaggregation as the default comparison, presenting GB10 numbers as datacenter receipts.

### 3.4 Engines

| Role | Engine | Rule |
|---|---|---|
| Challenger | Atlas `spark` built with `ATLAS_TARGET_HW=hopper` (sm_90a) or `ATLAS_TARGET_HW=b200` (sm_100a) | If the Phase 0 PTX gate or boot fails, stop. Do not A/B Spark vs H100. |
| Control | vLLM official recipe image for that model (pinned digest) | Not an ad-hoc `pip install vllm`. Flags from §7 only. |

Same physical node. Sequential only, never both engines resident. Same Hugging Face cache on a persistent volume. Same client binary and driver hash.

## 4. Success criteria

A cell is certified only if every gate passes. Each gate names its oracle.

| Gate | Bar | Oracle |
|---|---|---|
| Compile (Phase 0) | Every kernel in `kernels/<hw>/common` and the model's `nvfp4/` dir emits PTX and passes `ptxas` for the target arch | `scripts/hopper_ptx_gate.sh` ledger; per-arch negative fixture must fail (`redux.sync.max.abs.f32` for sm_90a/sm_12x, `mma.block_scale` for sm_100a). **Result 2026-09-05 (Spark 1, CUDA 13.0.88): sm_90a 870/871, sm_100a 870/871; the one failure is `qwen3.6-35b-a3b/nvfp4/moe_w4a16_grouped_gemm.cu` on both** — receipts in `receipts/` |
| Preflight | `spark serve --check-kernels` exits 0 on the box; compiled arch matches device CC | `--check-kernels` JSON (`compiled_arch`, `device_cc`); mismatch message is the negative case |
| Boot | `/health` returns 200 and a 1-token request completes ≤ 30 min after weights are local | `bench/hopper_ab/time_to_ready.sh` JSON; else NO-GO, tear down |
| Coherency | Two greedy runs, same prompt, byte-identical. Tool-call JSON parses with `finish_reason == "tool_calls"`. No `<think>` in content when thinking is off. GLM-4.5-Air rows add think-on and think-off through glm45. GLM-5.3/Flash are always-thinking: block think-off cells until a separate matched policy is frozen; parser-separated content is not evidence of disabled reasoning. GLM-5.x tool calls use glm47 | `bench/hopper_ab/coherency_gate.py` (derived from `scripts/test_coherence.py`); known-answer probes from `bench/agentic/coherence_check.py` (391 / Tokyo / rotaregirfer) |
| Latency pack | `lat` and `agent` at C=1 and C=16, 1 warmup + 3 reps, spread ≤ 10 % | `bench/ladder38/harness_w55_conc_ladder.py` output; vacuity floor 0.8 from `crates/atlas-plugin/src/benchmarks/concurrency.rs` |
| A/B | vLLM leg with §7 flags, same shapes, same box, within 24 h, spec-matched | `bench/hopper_ab/compare.py` refuses mismatched isl/osl/seed/temperature/kwargs |
| Artifact | JSON per cell + full serve command + `nvidia-smi -q` + image digest + `git sha` + PTX ledger sha | §10 schema; `GateRecord` hardware block |

### Customer SLO (proposed — freeze at kickoff, then do not move)

| Workload | C | TTFT p50 | TPOT p50 | Note |
|---|---|---|---|---|
| lat 1024 / 256 | 1 | ≤ 300 ms | ≤ 25 ms (≥ 40 tok/s/user) | Interactive chat |
| lat 1024 / 256 | 16 | ≤ 1.0 s | ≤ 50 ms | Shared endpoint |
| agent 4096 / 512 | 1 | ≤ 800 ms | ≤ 30 ms | Tool-calling turn |
| agent 4096 / 512 | 16 | ≤ 2.5 s | ≤ 60 ms | Agent fleet |

SLO misses are reported, not hidden. A cell that misses SLO but beats vLLM is a "relative win"; a cell that meets SLO but loses to vLLM is a "fit-for-purpose" row.

## 5. Phases and stop rules

| Phase | Needs | Output | Stop rule |
|---|---|---|---|
| 0 Compile + preflight | nvcc only (Spark 1 has CUDA 13.0; no H100 needed) | PTX ledger per model per arch; `--check-kernels` on the first GPU box | Any P0 model kernel fails to compile → fix or shadow before renting GPUs |
| A Boot + coherency | 1 box per SKU, smallest topology | boot JSON, coherency JSON | Boot > 30 min or coherency fail → NO-GO for that (model, SKU) |
| B Latency pack | same box | ladder JSON (C = 1, 16; optional 2..128) | Vacuous cells (> 20 % under budget) → rerun once, then mark |
| C vLLM A/B | same box, Atlas torn down | vLLM ladder JSON + compare table | Recipe-max fails on Atlas topology → matched topology, footnote |
| D Overflow | leftover hours | M2.7, NVFP4-on-B200, ladder to C=128 | Budget exhausted |

Order of boxes: 1×H100 (Nano, Qwen3.6; GLM-4.5-Air canary on 2×H100 if a GLM number is wanted cheaply) → 4×H100 / 2×H100 (Super) → 1×H200 (Super, Qwen3-Next, the 27B head-to-head) → 4–8×H200 (Flash-Next vLLM ref, GLM-5.3-Flash) → 1×B200 (Nano, Qwen3.6, NVFP4 rows) → 2×B200 (Super) → one 8×H200 booking for V4-Flash **or** GLM-5.3 (not both as separate weeks) → 8×B200. Never start an 8-GPU rental before the 1- and 2-GPU cells are certified.

## 6. Atlas recipes (best guesses to cut time-to-first-token; verify on the box)

Binary is `spark`. Flags below exist in `crates/spark-server/src/cli/serve_args.rs`. Values start from the repo's own recipes (`crates/spark-server/tests/fixtures/recipes/**.yaml`, `README.md` Recipe A, `bench/ladder38/published.json`) and are adjusted for HBM boxes.

### 6.0 Build (x86_64, CUDA ≥ 12.8 for sm_90a; 13.0+ for sm_100a)

```bash
# Hopper
export ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL='nemotron-super-120b-a12b' ATLAS_TARGET_QUANT=nvfp4
export CUDA_HOME=/usr/local/cuda RUSTUP_TOOLCHAIN=stable
cargo build --release -p spark-server          # ~6 min full build on a 20-core box
./target/release/spark serve <MODEL> --check-kernels --no-tui   # exit code = unresolved kernels
# B200: ATLAS_TARGET_HW=b200 (sm_100a). NVFP4 CUTLASS wrappers still need an Sm100 port; FP8/BF16 paths do not.
```

Common flags for every cell (from the ladder38 Atlas leg, adapted):

```
--bind 0.0.0.0 --port 8888 --no-tui --request-timeout 0
--gpu-memory-utilization 0.90 --max-num-seqs 128 --max-batch-size 32
--enable-prefix-caching true --scheduling-policy slai
--warmup-prompt bench/hopper_ab/warmup_1024.txt     # kills the 5–30 s first-request autotune
--kv-cache-dtype fp8 --kv-high-precision-layers auto
```

Think-off rows add `--disable-thinking`. Spec-on rows add `--speculative --num-drafts 3 --mtp-quantization bf16` (K=4) and the vLLM leg must use `num_speculative_tokens: 3`.

### 6.1 Per model

| Model | Topology | Atlas specifics | Source / caveat |
|---|---|---|---|
| Nemotron 3 Nano FP8 | 1 GPU | `--max-seq-len 32768`; **no MTP** ("No MTP support", recipe fixture) → spec off on both engines | `recipes/nemotron-3-nano*.yaml` |
| Nemotron 3 Super FP8 | 2×H100: `--world-size 2 --ep-size 2 --tp-size 1` (EP=2 is the only validated Super layout); 1×H200 / 1×B200 may fit at util 0.92 | `--max-seq-len 65536 --ssm-cache-slots 0`; tool parser: MODEL.toml pins `bare_json`, recipe yaml says `qwen3_coder` — **use `bare_json`** (MODEL.toml documents the qwen3_coder token loop). `speculative: true` in the recipe conflicts with `MTP_SUPPORTED_MODEL_TYPES` in `crates/spark-model/src/preflight.rs` — verify on box; default spec **off**. Think-on primary row | `recipes/nemotron-3-super*.yaml`, `kernels/gb10/nemotron-super-120b-a12b/MODEL.toml` |
| Qwen3.6-35B-A3B FP8 | 1×H100 / 1×H200 / generated 1×B200 | Dedicated FP8 recipe exists: TP1, trust-remote-code, auto tools/qwen3_xml, qwen3 reasoning, encoder DP. Exact commands in `vllm-control/RECIPE-VERIFICATION.md`. | recipe K3/Triton; campaign K2 is an explicit adaptation |
| Qwen3-Next-80B-A3B Instruct FP8 | 1×H200 / generated 8×H100 / generated 1×B200 | Hermes parser; no reasoning parser; Instruct supports only non-thinking. Requested 2×H100 is reconstructed. | qwen3_next_mtp K2 and no-enable-chunked-prefill, or spec off |
| DeepSeek V4-Flash FP8 | 8×H200 `--world-size 8 --ep-size 8 --tp-size 1`; 4×B200 EP=4 | TP impossible (MQA). Spec off (public checkpoint ships no usable MTP for Atlas; `docs/deepseek_v4_mtp_support.md` is a design, not shipped). `--kv-cache-dtype fp8`, `--max-batch-size 1 → raise stepwise`, `--oom-guard-mb 512`. Tool parser `deepseek_v4` is accepted by the parser but missing from `flag_values.rs` — rely on auto-resolution, do not pass the flag | `recipes/deepseek-v4/*.yaml`, `docker/gb10/deepseek-v4-flash/nvfp4/Dockerfile` |

### 6.2 Multi-GPU on one node (never done before — treat as Phase A work)

- Atlas ranks are separate processes (`--rank i --world-size N --master-addr 127.0.0.1 --master-port 29500`), one per GPU: use `CUDA_VISIBLE_DEVICES=i` per rank or `--gpu-ordinal i`. Spec flags must be identical across ranks (`QUICKSTART.md:328-333`).
- Undo the GB10 NCCL pessimizations from `scripts/start-ep2.sh`: do not set `NCCL_SOCKET_IFNAME=enp1s0f0np0`, `NCCL_NVLS_ENABLE=0`, `NCCL_NET_GDR_LEVEL=0`, `NCCL_ALGO=Ring`, `NCCL_PROTO=Simple`. Start with NCCL defaults; record `NCCL_DEBUG=INFO` for the first boot. NCCL ≥ 2.28 is required by the image gate.
- Only rank 0 serves HTTP; point the client at it.

### 6.3 Time-to-testing shortcuts

1. Run the PTX gate on any nvcc box today (Spark 1) for `sm_90a` and `sm_100a`; every failing kernel gets a Hopper/B200 shadow copy before the rental clock starts.
2. Prefetch weights to a persistent volume with `hf download`; never download on GPU hours.
3. Build the `spark` binary in CI (`linux-x86_64-nvidia-cuda` release target already exists) so the box only runs it.
4. First boot with `--check-kernels`, then with `RUST_LOG=info` and `--max-batch-size 1`; only then the recipe flags.
5. Keep the vLLM image pulled and the HF cache warm before Atlas tears down, so the A/B window stays inside 24 h.

## 7. vLLM recipes (control)

Use only the official recipe image and flags for the model; pin the image digest in the artifact. Full per-SKU commands, flag tables, conflicts and URLs are in `VLLM-RECIPES.md` (same directory). Summary:

| Model | SKU | Recipe line (verbatim source) | Spec-matched form |
|---|---|---|---|
| Nemotron 3 Super FP8 | 8×H100 / 8×H200 / 1×B200 | Current hardware JSON commands in `vllm-control/RECIPE-VERIFICATION.md`; TP4 guide/card example is separate. Tool names qwen3_xml/qwen3_coder alias in v0.28.0. | recipe MTP K3 on both or neither |
| Nemotron 3 Super FP8 | 1×B200 | model-card form (H200 TP1 unverified) with `--tensor-parallel-size 1`, `--mamba-ssm-cache-dtype float32`, `--kv-cache-dtype fp8` | same |
| Nemotron 3 Nano FP8 | 1×H100 / 1×H200 | `vllm serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 --trust-remote-code --async-scheduling --kv-cache-dtype fp8 --tensor-parallel-size 1 --moe-backend flashinfer_cutlass` | spec off both |
| Qwen3.6-35B-A3B FP8 | 1×H100 / 1×H200 / generated 1×B200 | Dedicated FP8 recipe exists: TP1, trust-remote-code, auto tools/qwen3_xml, qwen3 reasoning, encoder DP. Exact commands in `vllm-control/RECIPE-VERIFICATION.md`. | recipe K3/Triton; campaign K2 is an explicit adaptation |
| Qwen3-Next-80B-A3B Instruct FP8 | 1×H200 / generated 8×H100 / generated 1×B200 | Hermes parser; no reasoning parser; Instruct supports only non-thinking. Requested 2×H100 is reconstructed. | qwen3_next_mtp K2 and no-enable-chunked-prefill, or spec off |
| GLM-5.3 FP8 | generated 8×H200 (not marked verified) | Image v0.28.0; exact JSON commands in `vllm-control/RECIPE-VERIFICATION.md`. Always-thinking; think-off campaign cells blocked until a matched policy is defined. | JSON MTP K5 opt-in; dotted form is valid equivalent syntax |
| GLM-4.5-Air FP8 | proposed 2×H100 / 1×H200 | Still reconstructed: dedicated twins 404; FP8 card command serves BF16 Air TP8. Single H200 would need TP1, not TP2. | spec off both |
| Kimi K3 MXFP4 | 2×8 B200, TP8 + PP2 alternative | Exact head/worker JSON in `vllm-control/RECIPE-VERIFICATION.md`; worker headless and FP8 attention-config required. Context49152/text-only are campaign adaptations. JSON latest vs guide kimi-k3 image conflict requires digest validation. Hopper default is 16×H200 TP16/Marlin with maxlen32768/maxseq5. | spec off both; recipe DSpark strategy list excludes TP8+PP2 |
| DeepSeek V4-Flash FP8 | 8×H200 / 8×B200 | `vllm serve deepseek-ai/DeepSeek-V4-Flash-0731 --trust-remote-code --kv-cache-dtype fp8 --block-size 256 --enable-expert-parallel --tensor-parallel-size 8 --tokenizer-mode deepseek_v4 --tool-call-parser deepseek_v4 --enable-auto-tool-choice --reasoning-parser deepseek_v4 --reasoning-config '{...}'`; B200 adds `--attention_config.use_fp4_indexer_cache True --moe-backend deep_gemm_mega_moe` | spec **off** both (Atlas has no V4 MTP; spec-on still requires hardware verification) |

Fairness pins for the client, both engines (from `bench/ladder38/harness_w55_conc_ladder.py`):

```
temperature 0.0, seed 42, presence_penalty 0.0, frequency_penalty 0.0
chat_template_kwargs: {"enable_thinking": false}   # the only key vLLM honours for think-off
per-request nonce in the prompt (defeats prefix cache on both engines)
usage from stream_options.include_usage, not counted deltas
```

Recipe resolutions and remaining conflicts are recorded in `vllm-control/RECIPE-VERIFICATION.md`: Qwen recipes exist; v0.28.0 aliases the Super tool parsers and DeepSeek packed KV dtype; Kimi image/PP speculation and GLM-5.3 think-off remain unresolved. Treat generated SKU commands separately from verified hardware. Reset prefix cache successfully before each separate ladder process because the nonce counter restarts; in v0.28.0 the isolated benchmark server needs VLLM_SERVER_DEV_MODE=1 and POST /reset_prefix_cache must return success=true. Record this as an orchestration adaptation.

## 8. Hardware / topology matrix

| SKU | Mem | BW | Arch | Atlas target | Quant on both engines | Notes |
|---|---|---|---|---|---|---|
| H100 SXM | 80 GB | 3.35 TB/s | 9.0 | `hopper` (sm_90a) | FP8 | Super recipe-max is TP4; V4-Flash and M3 have no H100 recipe — use H200 |
| H200 SXM | 141 GB | 4.8 TB/s | 9.0 | `hopper` (sm_90a) | FP8 | Super fits 1 GPU; V4-Flash 8 GPUs (vLLM TEP8, Atlas EP=8); NVFP4 is Marlin-emulated and buggy in vLLM here — never benchmark it |
| B200 SXM | 180 GB | 8 TB/s | 10.0 | `b200` (sm_100a) | FP8 now; NVFP4 after a port | **Measured 2026-09-05:** Atlas's hand-written W4A4 MoE GEMM uses the warp-level `mma.kind::mxf4nvf4.block_scale`, a consumer-Blackwell (sm_120/121) instruction that ptxas rejects on sm_100a; datacenter Blackwell needs a `tcgen05` path, and the CUTLASS wrappers need `Sm100`. That W4A4 path is now compiled out here (`-DATLAS_NO_WARP_BLOCKSCALE_MMA`), so the W4A16 target builds 173/173 — but Atlas B200 rows stay FP8 until the port; vLLM NVFP4 rows on B200 are reference-only |

## 9. Client and methodology

- One client drives both engines: `bench/ladder38/harness_w55_conc_ladder.py` (`--isl --osl --concs --reps --warmup`), extended by `bench/hopper_ab/` for time-to-ready, coherency and the compare table.
- Warm-up: 1 rep discarded per rung. Reps: 3. Report the raw series, not only the mean.
- Vacuity: a cell where any request returns < 80 % of the output budget is non-comparable (`VACUITY_FLOOR`).
- Thermal/clock provenance: sample `nvidia-smi --query-gpu=clocks.sm,power.draw` inside each rep (the harness already does). Lock clocks if the provider allows (`nvidia-smi -lgc`).
- Time-to-ready measured at 1 s granularity from process start to `/health` 200, then first token.
- Instrument validation (RST): every gate script ships `--selftest` against a stub that must fail; a gate that has never failed has never been tested.

## 10. Artifact schema

One JSON per cell, additive to the repo's `GateRecord` (`crates/atlas-plugin/src/gate/record.rs`):

```json
{
  "schema": 1,
  "campaign": "hopper-atlas-vs-vllm-2026-09",
  "engine": "atlas|vllm",
  "engine_version": {"git_sha": "...", "image_digest": "sha256:...", "binary_sha256": "..."},
  "model": {"hf_id": "...", "revision": "...", "quant": "fp8|nvfp4"},
  "hardware": {"gpu": "NVIDIA H100 80GB HBM3", "gpu_count": 2, "driver": "...", "cuda": "...", "hardware_id": "h100", "sm_clock_mhz": 1980, "nvidia_smi_q_sha256": "..."},
  "topology": {"tp": 1, "ep": 2, "world_size": 2, "matched": true},
  "serve_command": ["spark", "serve", "..."],
  "workload": {"name": "lat", "isl": 1024, "osl": 256, "concurrency": 16, "reps": 3, "warmup": 1, "temperature": 0.0, "seed": 42, "enable_thinking": false, "spec": {"on": true, "k": 4}},
  "boot": {"time_to_ready_s": 0.0, "first_token_s": 0.0, "pass": true},
  "coherency": {"determinism_ok": true, "toolcall_ok": true, "think_leak_ok": true},
  "metrics": {"tok_s_series": [], "tok_s_mean": 0.0, "ttft_p50_ms": 0.0, "ttft_p99_ms": 0.0, "tpot_p50_ms": 0.0, "e2e_p50_s": 0.0, "vacuous": false},
  "ptx_gate_ledger_sha256": "...",
  "verdict": "CERTIFIED|NO-GO|PARTIAL",
  "notes": ""
}
```

## 11. Cost control

- Boot cap 30 min; PTX gate and binary build happen off the GPU clock.
- Rent in the §5 order; an 8-GPU node only after two 2-GPU cells certify.
- Weights prefetched to persistent storage; images pre-pulled.
- Budget line (fill at kickoff): GPU-hours per SKU × rate; abort a SKU at 150 % of its line.

## 12. Bring-up plan (Phase 0, test-driven, no GPU needed for most of it)

The companion PR is built RST-style: every check names its oracle and has a demonstrated red before green.

| Step | Test written first | Implementation | Runs where |
|---|---|---|---|
| Target dirs | `crates/atlas-kernels/tests/hopper_target.rs`: HARDWARE.toml parses (`sm_90a`, `sm_100a`); every gb10 common file has a non-dangling symlink; model dirs mirror gb10; negative fixture with a dangling link fails | `kernels/hopper/`, `kernels/b200/` (symlink inheritance from gb10, real MODEL.toml copies) | Mac / CI, `ATLAS_SKIP_BUILD=1` |
| Arch string handling | `kernel_target_arch("sm_90a") == "sm_90"`, `"sm_100a" → "sm_100"`, `"sm_121f" → "sm_121"` | `build_codegen.rs` | Mac / CI |
| Compile gate | `scripts/hopper_ptx_gate.sh --selftest` (known-bad sm_120-only kernel must fail) | nvcc `--ptx -arch=<arch>` + `ptxas` per kernel, JSON ledger | Spark 1 (nvcc, CPU only) |
| Device preflight | `ptx_arch_runs_on_device` truth table (`sm_121f` on 9.0 → Err, `sm_90a` on 10.0 → Err, `sm_90` on 12.1 → Ok, …) | `CudaBackend::new` queries CC and fails fast with an actionable message; `--check-kernels` reports `compiled_arch`/`device_cc` | Mac / CI; message verified on GB10 with the hopper binary (negative case) |
| Side-object arch | build-script fallback test | `ATLAS_CUDA_ARCH` / `ATLAS_PREDICTOR_ARCH` default from HARDWARE.toml | Mac / CI |
| Bench ids | `h100`/`h200`/`b200` resolve; `h800` refused; GPU-name → id mapping incl. B200 ≠ h100 | `bench_resolve`, `hardware_id_from_gpu_name`, `gpu_count` in records | Mac / CI |
| Campaign driver | each script `--selftest` | `bench/hopper_ab/` | Mac; then the box |

Gate results (2026-09-05): Nemotron Super, Nano, DeepSeek V4-Flash and Qwen3-Next compile completely for both sm_90a and sm_100a. Qwen3.6-35B-A3B failed one kernel on each on the FIRST pass (Hopper: no `cvt.e2m1x2`; B200: no warp-level `mma.block_scale`) — the W4A4 tail of its MoE grouped GEMM, now compiled out on both by `-DATLAS_NO_WARP_BLOCKSCALE_MMA`, taking it to **173/173 under `--strict` on both**, with GB10's PTX for that file byte-identical. That unblocks the W4A16 path, which is what these targets serve; W4A4 itself still wants an Sm90 grouped GEMM and a tcgen05 one, and neither exists. Qwen3-Next-80B keeps its P0 slot as the GDN + MoE model. Register pressure: `gated_delta_rule_persistent` spills 124 B on sm_90a vs 2256 B on sm_100a — first thing to profile on silicon.

Open engineering items surfaced by the gate, in likely order: kernels using sm_121-specific SMEM/tile assumptions (ptxas spills on sm_90), CUTLASS Sm120 wrappers compiled out (fine for FP8/BF16; blocks NVFP4 rows), FlashInfer/CuTe-DSL side objects pinned to `sm_121a`, `.benchmarks` perf-gate records invalidated by touching `kernels/` (CI `pr-benchmark-gate` needs a GB10 re-measure before merge).

## 13. Publishing rules

Allowed: "Nemotron 3 Super FP8 on 2×H100 and 2×H200, Atlas vs vLLM recipe, workloads lat/agent, C=1 and C=16, spec-matched, coherency passed" — with the cell table and artifact hashes.

Not allowed: "faster than vLLM" without SKU, C, quant and spec matching; calling GB10 or B200 numbers Hopper data; listing Flash-Next / Max / K3 / Pro / M3 / GLM as Atlas-tested unless an Atlas cell certified; quoting a Kimi K3 Hopper number without the "Hopper emulate" label, or any K3 number from a requant that is not `moonshotai/Kimi-K3` MXFP4; writing "GLM 3.5" anywhere; reusing the README 3.6× figure (superseded by `bench/ladder38/RESULTS.md`).

## 14. Risks

| Risk | Mitigation |
|---|---|
| Atlas sm_90a / sm_100a kernels do not compile or spill | PTX gate before any rental; shadow per-kernel copies under `kernels/<hw>/<model>/nvfp4/` |
| Intra-node NCCL never exercised | Start with NCCL defaults, `NCCL_DEBUG=INFO`, 2 GPUs first; the GB10 env block is documented as pessimization |
| V4-Flash EP=8 bring-up eats the box | 30-min boot cap; run last; B200 EP=4 as the fallback SKU |
| Super think-off degrades output | Think-on is the primary row; think-off reported with its coherency result |
| Recipe drift (MODEL.toml vs recipe yaml) | Follow MODEL.toml where it documents a failure mode; record the flag set in the artifact |
| Spec mismatch flatters one engine | Compare tool refuses unmatched spec/isl/osl/seed |
| Autotune / compile burns hours | Atlas `--warmup-prompt`; vLLM `--no-enable-flashinfer-autotune`, bounded compilation config |
| Weight download on GPU hourly | Prefetch to persistent volume; verify sha before renting |
| Perf-gate CI red on the PR | Expected: `kernels/` is a PERF_PATH; re-measure on GB10 before merge, do not lower thresholds |

## 15. Decision

- Run: Nano (plumbing) → Qwen3.6-35B → Super → Qwen3-Next-80B → V4-Flash, on H100 → H200 → B200 in that order. Single-GPU cells before any multi-GPU cell (see §16).
- A/B: vLLM using §7 only, spec-matched, same client.
- Skip: Qwen3.8-Max, V4-Pro, B300. Flash-Next, M3, GLM and Kimi K3 are vLLM-reference rows only until Atlas ports land; K3 is its own 16×B200 (2×8, TP8+PP2) booking and is rented only if Atlas loads it or a customer asked for the vLLM receipt.
- Next artifacts: the companion PR (targets, preflight, gate, driver) and `RESULTS-TEMPLATE.md` in this directory.

## 16. Sequencing input from the team (2026-09-04) and how this PRD absorbs it

A team developer proposed a different order: (1) two-node DGX Spark cluster to build and measure speculative decoding across ranks (bit-exact sharded verify, expert dispatch over the fabric, decode all-reduce latency), (2) one H200 for a 27B head-to-head against a published H200 number, (3) one node with GLM 5.3 and speculation on. Their reading of the tree matches ours: EP=2 today replicates compute and all-reduces, EP=4 is not a runnable recipe, and no speculative multiplier under EP has ever been measured.

What this PRD takes from it:

- **Single-GPU cells first, multi-GPU cells last.** Every multi-GPU Atlas cell inherits the all-reduce-bound EP=2 design; a loss there is expected and is a development finding, not a benchmark finding. The certified receipts this campaign can honestly produce today are 1×H100 / 1×H200 / 1×B200 cells (Nano, Qwen3.6-35B, Super on H200/B200, Qwen3-Next on H200/B200).
- **The 1×H200 27B head-to-head is adopted as the first paid cell** (`Qwen/Qwen3.8-27B-FP8`, target `qwen3.8-27b`, MTP K matched; NVFP4 excluded on Hopper). It is the cheapest datacenter receipt and reuses the ladder38 methodology unchanged.
- **Cross-rank speculative decoding, expert dispatch and all-reduce work are a development track on the two Sparks, not a campaign gate.** They are prerequisites for publishable 8-GPU cells and are tracked outside this PRD; this PRD reports 8-GPU Atlas cells as NO-GO or PARTIAL if they fail the boot/coherency gates rather than waiting for that work.
- **Kimi K3 is in scope as one 16×B200 booking** (decision 2026-09-04): `moonshotai/Kimi-K3` native MXFP4 QAT, TP8 + PP2 across 2×8 B200, 49152 context, spec off for the scored row. Weights are 1.56 TB, so no 8-GPU node holds it and Hopper only emulates MXFP4 (16×H200 Marlin, labelled "Hopper emulate"). Atlas has no KDA / LatentMoE-K3 loader and no pipeline parallel; if it does not load in 30 minutes the Atlas leg is `ATLAS_UNSUPPORTED` and the node is not rented for it.
- **GLM is in scope as vLLM-reference rows and as an Atlas cell only once it boots** (decision 2026-09-04): no `glm` `model_type` exists in `crates/spark-model/src/factory.rs`, so GLM-5.3-Flash / GLM-5.3 / GLM-4.5-Air are `ATLAS_UNSUPPORTED` until a port lands; the 30-minute boot cap decides whether an Atlas GLM cell exists in this campaign. The sales line after a green cell is "GLM-5.3 FP8 on 8×H200, Atlas vs vLLM recipe, lat/agent, C=1 and C=16" — never "GLM 3.5".

## Appendix A — RST context intake

```yaml
mission: give sales engineering defensible datacenter receipts; decide whether Atlas goes in RFPs
who_matters: enterprise infra buyer comparing against vLLM on hardware they already own
what_is_it: Atlas `spark serve` on H100/H200/B200 vs vLLM recipe, same node/weights/client
change_under_test: new kernel targets (sm_90a, sm_100a) + the campaign methodology itself
workspace_freshness: upstream main 567b5eb (Avarok-Cybersecurity/atlas) fetched 2026-09-04; work in /tmp clone
constraints: no Hopper/Blackwell GPU in hand today; Spark 2 down; Spark 1 GPU busy (nvcc only)
testability: high for build/preflight (GPU-free tests); low for NCCL/NVLink until a box exists
oracles_available: nvcc/ptxas, gb10 tree (symlink source), CUDA compat rules, harness parity pins, vLLM recipes, known-answer probes
prior_information: bench/ladder38/RESULTS.md, docs/campaigns/gb10-*, MODEL.toml gotchas, DEPLOYMENT.md NCCL env
out_of_scope: multi-node, 1M ctx, disaggregation, B300 — no hardware, no recipe
danger: do not touch ~/dev/atlas checkouts; do not run pkill -f over ssh; do not lower .benchmarks thresholds
```

Stopping heuristic per phase: the gate table in §4 (pass/fail), the 30-min boot cap, and the budget line — not "tests passed".
