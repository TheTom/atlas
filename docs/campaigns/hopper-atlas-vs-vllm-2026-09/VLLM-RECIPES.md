# vLLM control recipes (Hopper / Blackwell) — research pack, 2026-09-04

Source of truth is `recipes.vllm.ai` (each recipe has a `.json` twin that renders the exact command per SKU). Confidence per block: **verbatim** = copied from the recipe JSON or the HF model card; **reconstructed** = assembled from secondary sources; **UNVERIFIED** = could not confirm. Re-check the recipe the day of the run; pin the image digest in the artifact.

Client-side pins for every run (both engines): `temperature 0.0`, `seed 42`, `presence_penalty 0.0`, `frequency_penalty 0.0`, `chat_template_kwargs: {"enable_thinking": false}` for think-off rows, per-request nonce, usage from `stream_options.include_usage`.

## Nemotron 3 Super 120B-A12B FP8 — `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8`

Recipe key `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16`, variant `fp8`. `min_vllm_version 0.17.1`, image `vllm/vllm-openai:latest`. FP8 VRAM floor 149 GB. Verified hardware: H100, H200, B200, RTX Pro 6000, GB300, GB10.

```bash
# 4x H100 FP8 (verbatim, recipes.vllm.ai)
vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 \
  --kv-cache-dtype fp8 --tensor-parallel-size 4 --trust-remote-code \
  --enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser nemotron_v3

# 8x H200 FP8 and 8x B200 FP8: identical flags with --tensor-parallel-size 8 (verbatim)
# 2x B200 NVFP4 (verbatim; no --kv-cache-dtype):
vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4 \
  --tensor-parallel-size 2 --trust-remote-code \
  --enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser nemotron_v3
```

```bash
# HF model card variant (verbatim) — fuller flag set, H100 cluster
vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 \
  --served-model-name nvidia/nemotron-3-super --async-scheduling --dtype auto \
  --kv-cache-dtype fp8 --tensor-parallel-size 4 --max-model-len 262144 \
  --enable-expert-parallel --swap-space 0 --trust-remote-code \
  --gpu-memory-utilization 0.9 --max-cudagraph-capture-size 128 --enable-chunked-prefill \
  --mamba-ssm-cache-dtype float32 --reasoning-parser nemotron_v3 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder
# Card: on B200/B300 the FP8 checkpoint fits ONE GPU -> --tensor-parallel-size 1, drop --enable-expert-parallel.
```

NVIDIA cookbook 2×H100 variant adds `--attention-backend TRITON_ATTN --max-num-seqs 512` and a downloaded `super_v3_reasoning_parser.py`.

| Flag | Value | Note |
|---|---|---|
| `--tensor-parallel-size` | H100 4 · H200 8 · B200 8 (recipe) vs B200 1 (card) | conflict: pick one source per cell and cite it |
| `--kv-cache-dtype` | `fp8` | |
| `--mamba-ssm-cache-dtype` | `float32` | Mamba-2 stability (card) |
| `--mamba-cache-mode` | `align` | only mode that supports prefix caching on hybrids (experimental) |
| `--speculative-config` | `'{"method":"mtp","num_speculative_tokens":3}'` | opt-in; required for spec-matched cells |
| `--tool-call-parser` | `qwen3_xml` (recipe) vs `qwen3_coder` (card, cookbook) | conflict |
| `--reasoning-parser` | `nemotron_v3` (built-in) vs `super_v3` plugin | conflict |
| Dynamo recipe | H200: TP4 FP8 `--moe-backend FLASHINFER_CUTLASS`; B200: TP4 NVFP4 `--moe-backend FLASHINFER_TRTLLM`; MTP draft 3 | image `vllm-runtime:1.3.0-nemotron-super-dev.1` |

## Nemotron 3 Nano 30B-A3B FP8 — `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8`

`min_vllm_version 0.17.0` (0.28.0 recommended), VRAM 35 GB, verified H100/H200.

```bash
# 1x H100 / 1x H200 (verbatim)
vllm serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 \
  --trust-remote-code --async-scheduling --kv-cache-dtype fp8 \
  --tensor-parallel-size 1 --moe-backend flashinfer_cutlass
# Card adds: --enable-auto-tool-choice --tool-call-parser qwen3_coder \
#   --reasoning-parser-plugin nano_v3_reasoning_parser.py --reasoning-parser nano_v3 --max-model-len 262144
```

No MTP documented for Nano → spec off on both engines.

## Qwen3.8-Flash-Next FP8 — `Qwen/Qwen3.8-Flash-Next-FP8` (exists)

125B total (6B active + 51B per-layer embedding + 4B MTP), GDN + MoE (512 experts, 10+1), `min_vllm_version 0.29.0` (nightly), image `vllm/vllm-openai:qwen38-flash-next`. FP8 needs 250 GB. Base args: `--max-num-seqs 256 --gpu-memory-utilization 0.90 --enable-prefix-caching --no-enable-flashinfer-autotune`.

```bash
# 4x H100 FP8 — TP4 + PLE CPU offload (verbatim; needs >= 51 GB host RAM)
VLLM_PLE_CPU_OFFLOAD=1 vllm serve Qwen/Qwen3.8-Flash-Next-FP8 \
  --tensor-parallel-size 4 --moe-backend triton --gpu-memory-utilization 0.85 \
  --max-num-seqs 256 --enable-prefix-caching --no-enable-flashinfer-autotune \
  --enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser qwen3

# 8x H200 FP8 — TEP8 (plain TP8 is INCOMPATIBLE with the FP8 checkpoint) (verbatim)
vllm serve Qwen/Qwen3.8-Flash-Next-FP8 \
  --tensor-parallel-size 8 --enable-expert-parallel --moe-backend triton \
  --gpu-memory-utilization 0.85 --max-num-seqs 256 --enable-prefix-caching \
  --no-enable-flashinfer-autotune --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml --reasoning-parser qwen3

# 4x B200 / GB300 FP8 — TP4 (verbatim; default MoE backend, util 0.90)
vllm serve Qwen/Qwen3.8-Flash-Next-FP8 \
  --tensor-parallel-size 4 --gpu-memory-utilization 0.90 --max-num-seqs 256 \
  --enable-prefix-caching --no-enable-flashinfer-autotune \
  --enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser qwen3
```

Recipe states MTP has **negative** throughput impact on H100. MTP flag if used: `--speculative-config '{"method":"mtp","num_speculative_tokens":3}'`. Atlas has no `qwen3.8-flash-next` target; this model stays blocked on a `spark-model` port.

## DeepSeek V4-Flash — `deepseek-ai/DeepSeek-V4-Flash-0731` (FP8 default variant)

284B/13B active, MLA + CSA/HCA, `min_vllm_version 0.20.0`, image `vllm/vllm-openai:v0.28.0`. Base args `--trust-remote-code --kv-cache-dtype fp8 --block-size 256`. **No H100 entry in verified hardware** (H200, B200, GB200, B300, GB300, GB10, RTX Pro 6000 8×, MI3xx).

```bash
# 8x H200 — single_node_tep (recipe default, verbatim)
vllm serve deepseek-ai/DeepSeek-V4-Flash-0731 \
  --trust-remote-code --kv-cache-dtype fp8 --block-size 256 \
  --enable-expert-parallel --tensor-parallel-size 8 \
  --tokenizer-mode deepseek_v4 --tool-call-parser deepseek_v4 --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4 \
  --reasoning-config '{"reasoning_parser":"deepseek_v4","reasoning_start_str":"","reasoning_end_str":""}' \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}'

# 8x B200 — same plus two Blackwell-only flags (verbatim):
#   --attention_config.use_fp4_indexer_cache True --moe-backend deep_gemm_mega_moe
```

Notes: MTP form is `'{"method":"mtp","num_speculative_tokens":2}'`. **DSpark is broken on SM90** (vllm#47648, open) → for Hopper spec-matched cells use MTP or spec-off on both. `--kv-cache-dtype fp8` (recipe) vs `fp8_ds_mla` (LMCache docs): UNVERIFIED which a given vLLM version requires. DP8 proposal (recipes#762) is not the default.

## MiniMax M3 — `MiniMaxAI/MiniMax-M3` (exists; Atlas has M2.7 only)

427B/26B active, VLM, `min_vllm_version 0.24.0`, image `vllm/vllm-openai:minimax-m3`, `--block-size 128` mandatory. Verified H200, B200, B300, MI300X, MI355X (no H100).

```bash
# 8x H200 BF16 (verbatim)
vllm serve MiniMaxAI/MiniMax-M3 --block-size 128 --tensor-parallel-size 8 \
  --tool-call-parser minimax_m3 --enable-auto-tool-choice --reasoning-parser minimax_m3
# 8x B200 NVFP4: nvidia/MiniMax-M3-NVFP4, env VLLM_FLOAT32_MATMUL_PRECISION=high, add --trust-remote-code
# Text-only A/B: add --language-model-only. EAGLE3 draft: Inferact/MiniMax-M3-EAGLE3 (num_speculative_tokens 3).
```

## Kimi K3 — `moonshotai/Kimi-K3` (team spec 2026-09-04; recipe facts from `recipes.vllm.ai/moonshotai/Kimi-K3.json`)

Pick one checkpoint: `moonshotai/Kimi-K3`, **native MXFP4 (QAT from SFT)** — MXFP4 experts + MXFP8 activations, attention / shared experts / lm_head higher precision. It is what Moonshot shipped, what vLLM's day-0 recipe optimizes, and what published numbers use. A VESSL W4AFP8 or Ascend W4A8 requant is a different model for sales purposes; never A/B it against the MXFP4 checkpoint.

| Field | Value |
|---|---|
| Model | 2.8T MoE, 16 of 896 experts active, Kimi Delta Attention + Attention Residuals, 1M ctx, native vision (`--language-model-only` for the text A/B) |
| Weights | 1.56 TB → 8×H200 short by ~430 GB, 8×B200 short by ~120 GB. Single-node is not an option |
| Image | `vllm/vllm-openai:kimi-k3` (CUDA 13 / cu130, r580+ driver), vLLM ≥ 0.27.1 |
| Parsers | `--tool-call-parser kimi_k3 --reasoning-parser kimi_k3` |
| Compare box | **2×8 B200 (16 GPUs), TP8 + PP2** |
| Context cap | `--max-model-len 49152` for the A/B |
| Spec | Off for the scored row; DSpark (`num_speculative_tokens 8`, recipe default) as a second row only |
| Hopper | 16×H200 with `--moe-backend marlin` (MXFP4 emulated) — label the row "Hopper emulate"; the recipe's 8×H200 profile (`--max-model-len 32768 --max-num-seqs 5`) is a bring-up curiosity, not a receipt |

```bash
# vLLM control — run on both nodes with RANK 0/1 (team-supplied; verify against the recipe page day-of)
vllm serve moonshotai/Kimi-K3 \
  --served-model-name kimi-k3 --trust-remote-code --language-model-only \
  --tensor-parallel-size 8 --pipeline-parallel-size 2 \
  --nnodes 2 --node-rank $RANK --master-addr $MASTER --master-port 29501 \
  --moe-backend flashinfer_trtllm --disable-custom-all-reduce \
  --kv-cache-dtype fp8 --enable-prefix-caching --max-model-len 49152 \
  --enable-auto-tool-choice --tool-call-parser kimi_k3 --reasoning-parser kimi_k3
```

Atlas leg: same checkpoint, same GPU count, same max len, thinking + tool parsers on. Atlas has TP and EP but **no pipeline parallel**, so the matched layout is TP8 + EP2 with a footnote. If Atlas cannot load MXFP4 KDA / LatentMoE in 30 minutes: `ATLAS_UNSUPPORTED`, do not rent the 16-GPU node for it.

Sources: https://recipes.vllm.ai/moonshotai/Kimi-K3 · https://recipes.vllm.ai/moonshotai/Kimi-K3.json · https://vllm.ai/blog/2026-07-27-k3

## GLM (Z.ai) — `zai-org/GLM-5.3`, `GLM-5.3-Flash`, `GLM-4.5-Air-FP8` (team-supplied 2026-09-04; **reconstructed — verify on recipes.vllm.ai before the run**)

No "GLM 3.5" enterprise SKU exists; the line is 4.5 → 4.7 → 5 → 5.3. Atlas has no `glm` `model_type` — every GLM cell is vLLM-only until a port boots.

```bash
# GLM-5.3 FP8 — 8x H200 (published Hopper default). Baseline row = no speculative flags; spec row = MTP 5. Never mixed.
vllm serve zai-org/GLM-5.3 --kv-cache-dtype fp8 --tensor-parallel-size 8 \
  --speculative-config.method mtp --speculative-config.num_speculative_tokens 5 \
  --tool-call-parser glm47 --reasoning-parser glm45 --enable-auto-tool-choice --served-model-name glm-5.3

# GLM-5.1 / 5.2 FP8 fallback if the 5.3 image is flaky (same box; image vllm/vllm-openai:glm51|glm52 or v0.28.0 per recipe page)
vllm serve zai-org/GLM-5.1-FP8 --tensor-parallel-size 8 --kv-cache-dtype fp8 \
  --speculative-config.method mtp --speculative-config.num_speculative_tokens 3 \
  --tool-call-parser glm47 --reasoning-parser glm45 --enable-auto-tool-choice --chat-template-content-format=string

# GLM-4.5-Air FP8 — 2x H100 or 1x H200 (cheap canary)
vllm serve zai-org/GLM-4.5-Air-FP8 --tensor-parallel-size 2 --tool-call-parser glm45 --reasoning-parser glm45 --enable-auto-tool-choice
```

| Variant | Size | Hopper fit | Campaign slot |
|---|---|---|---|
| GLM-5.3-Flash | ~320B / 18B active, multimodal | 4–8×H200 | P1, shares the Flash-Next booking |
| GLM-5.3 | ~743B / 39B active | 8×H200 FP8 single node; tight on 8×H100 | Phase D, same rental as V4-Flash |
| GLM-4.5-Air FP8 | 106B / 12B | 2×H100 / 1×H200 | canary only |
| GLM-4.5 FP8 | 358B / 32B | 8×H100 / 4×H200 | skip unless a customer names it |

Hopper uses `--kv-cache-dtype fp8` (not a Blackwell-specific e4m3 spelling). Coherency extras: think-on/off via `glm45`, one `glm47` tool call, same greedy A/A rule.

## Hopper vs Blackwell behaviour in vLLM

- Default attention: SM90 `FLASH_ATTN` (FA3); SM100 `FLASHINFER` (FA4 / trtllm-gen). Override `--attention-backend`.
- FP8 KV: Hopper FA3 needs two-level accumulation; break-even context ~7k (Hopper) vs ~4k (Blackwell). Our `lat` ISL 1024 is below both — FP8 KV rows are about capacity, not speed.
- NVFP4 on Hopper = Marlin emulation, **buggy** (vllm#49070: wrong activations, illegal memory access at C≈8). Never benchmark NVFP4 on H100/H200.
- Warm-up levers: `--no-enable-flashinfer-autotune`, `--kernel-config '{"enable_flashinfer_autotune": false}'`, `-O1`/`-O2` compilation levels, `VLLM_CACHE_ROOT` compile cache, `--kv-cache-memory <bytes>` to skip profiling, `--enforce-eager` to measure how much boot is compile/capture. `vllm bench startup --output-json` measures boot.
- Hybrid prefix caching (Nemotron): block size rises to the Mamba page (e.g. 528 tokens); prompts shorter than a block get 0 % hit rate.

## Single client for both engines

`vllm bench serve` (the old `benchmark_serving.py` is a deprecated stub) works against any OpenAI-compatible server:

```bash
vllm bench serve --backend openai --base-url http://localhost:8888 --endpoint /v1/completions \
  --model <hf-id> --served-model-name <name> --tokenizer <hf-id> \
  --dataset-name random --random-input-len 1024 --random-output-len 256 --random-range-ratio 0.0 \
  --num-prompts 160 --max-concurrency 16 --request-rate inf --ignore-eos --seed 42 \
  --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,90,95,99 \
  --save-result --save-detailed --result-dir ./results --metadata engine=atlas gpu=H100 tp=1
```

`vllm bench sweep serve` launches `vllm serve` itself and cannot drive Atlas. NVIDIA AIPerf (`pip install aiperf`, successor to GenAI-Perf) is a neutral cross-check but reports ITL, not TPOT. The campaign's primary client remains `bench/ladder38/harness_w55_conc_ladder.py` (chat endpoint, parity pins, nonce); `vllm bench serve` is the cross-check.

## llama.cpp and DwarfStar (for the "what do other engines need" question)

- llama.cpp: `CMAKE_CUDA_ARCHITECTURES` defaults include `90-virtual` (PTX JIT on Hopper) but **no `100`/`100a`/`103`**; pass `-DCMAKE_CUDA_ARCHITECTURES=100` for B200. `GGML_CUDA_CC_BLACKWELL = 1200` gates the FP4 path, so B200 (cc 1000) likely gets Hopper-class kernels — verify empirically. No FP8 GEMM/weight type.
- DwarfStar (`antirez/ds4`): arch is a Makefile variable (`make cuda CUDA_ARCH=sm_90`), kernels carry only `__CUDA_ARCH__ >= 700` guards. Same design Atlas is moving to: arch as data, kernels at a portable floor.

## Open conflicts to carry as risks

1. Nemotron Super tool parser `qwen3_xml` vs `qwen3_coder`; reasoning parser `nemotron_v3` vs `super_v3` plugin; B200 GPU count TP8 (recipe) vs TP1 (card).
2. DeepSeek V4-Flash `fp8` vs `fp8_ds_mla`; DSpark broken on SM90; no H100 recipe.
3. MiniMax M3 exists for vLLM; Atlas has M2.7 → M3 is a vLLM-only cell until Atlas ports it.
4. `VLLM_USE_FLASHINFER_MOE_FP4`, `VLLM_USE_TRTLLM_ATTENTION`, `VLLM_ATTENTION_BACKEND` are absent from the official env-var page — UNVERIFIED.

## URLs

recipes.vllm.ai (index, nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16 + .json, NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 + .json, Qwen/Qwen3.8-Flash-Next + .json, deepseek-ai/DeepSeek-V4-Flash + .json, MiniMaxAI/MiniMax-M3 + .json) · github.com/vllm-project/recipes (models/*.yaml, issues/762) · docs.vllm.ai (design/attention_backends, features/quantization, configuration/optimization, configuration/env_vars, cli/bench/serve, cli/bench/startup) · vllm.ai/blog/2026-04-22-fp8-kvcache · vllm.ai/blog/2026-03-11-nemotron-3-super · vllm issues 49070, 47648, 27751, 45238, 40696 · huggingface.co model cards (Nemotron Super FP8/NVFP4, Nano FP8, Qwen3.8-Flash-Next-FP8, MiniMax-M3) · NVIDIA-NeMo/Nemotron vllm_cookbook.ipynb · docs.nvidia.com/dynamo/dev/recipes/nemotron-3-super · docs.nvidia.com/aiperf · ggml-org/llama.cpp ggml-cuda/CMakeLists.txt, common.cuh · docs.lmcache.ai/recipes/deepseek_v4_flash.html
