# Recipe verification — 2026-09-05 UTC

This is source verification, not a GPU boot or performance receipt. Retrieval occurred on 2026-09-05 UTC (2026-09-04 in Chicago); exact timestamps and response SHA-256 hashes are in [recipe-evidence](recipe-evidence/). Only public recipes, documentation, source code, and model cards were fetched; no weights were downloaded for this work.

`verbatim` means the fenced command is copied byte-for-byte from the cited JSON `command`, `head_command`, or `worker_commands` field, or explicitly identified model-card/guide code. `reconstructed` means a campaign adaptation or a card instruction applied to another command. `still unverified` means the requested SKU/configuration lacks a retrieved authoritative command or a source conflict remains. A generated hardware endpoint is not evidence that its SKU was tested: `meta.hardware` is reported separately. Mutable tags are source recommendations, never image digests.

The per-SKU JSON represents the current command builder default. It can differ from a recipe's embedded prose example and from its parent model's default variant. GPU count below comes from the command's parallelism, not the eight-GPU inventory in `hardware_profile`.

| Model / question | Verdict | Resolution |
|---|---|---|
| Qwen3.6-35B-A3B FP8 missing recipe | verbatim | Dedicated recipe exists; H100/H200/B200 render TP1, XML tool parser, Qwen3 reasoning parser, encoder DP. Campaign tuning is an adaptation. |
| Qwen3-Next-80B-A3B Instruct FP8 | verbatim | H100 TP8, H200 TP1, B200 TP1; Hermes parser; no reasoning parser. Instruct checkpoint is non-thinking only. Two-H100 row is reconstructed. |
| GLM dotted speculative syntax | verbatim / reconstructed | Dotted syntax is documented and appears verbatim in GLM-5.1 MTP feature; GLM-5.3 uses a JSON object with K5. The dotted GLM-5.3 form is equivalent syntax, not its rendered default. |
| GLM-5.3 FP8 | verbatim; Hopper validation still unverified | H200 TP8 command exists; recipe's verified-hardware map currently lists B300 and Ascend only. Thinking is always on. |
| GLM-5.3-Flash | verbatim | H100/H200 TP8 omit FP8 KV; B200 TP8 adds FP8 KV. H200 is generated but absent from verified map. Thinking is always on. |
| GLM-4.5-Air FP8 | still unverified | Dedicated recipe twins return 404; its HF card's vLLM command serves BF16 Air at TP8. Requested FP8 H100/H200 commands remain reconstructed. |
| Kimi K3 | verbatim; image conflict still unverified | H200/B200 defaults are TP16 across two nodes; exact B200 TP8+PP2 alternative retrieved. Worker needs `--headless`. JSON image `latest` conflicts with guide `kimi-k3`. |
| DeepSeek V4-Flash FP8 KV | verbatim; source-resolved on v0.28.0 | `fp8` is accepted as alias and normalized to `fp8_ds_mla` for the packed MLA layout. It is not a universal equivalence across backends/releases. |
| Nemotron Super parsers | verbatim; source-resolved on v0.28.0 | `qwen3_xml` and `qwen3_coder` register the same class; built-in `nemotron_v3` exists. The standalone `super_v3` plugin is a separate implementation. |
| Nemotron Super GPU count | verbatim; guide differs | FP8 hardware JSON: H100 TP8, H200 TP8, B200 TP1. Guide retains TP4 example; HF card says B200/B300 TP1. No card support found for H200 TP1. |
| Nemotron Nano FP8 / GB10 | verbatim H100/H200; GB10 reconstructed | Current Nano commands include tool parser and downloaded reasoning plugin. GB10 endpoint is 404; Ubuntu 24.04 v0.28.0 GB10 example belongs to Super NVFP4. |
| Qwen3.8-Flash-Next FP8 | verbatim | Current H100/H200/B200 hardware defaults are TP4; H100 adds PLE offload. The earlier H200 TEP8 line is not the default. |
| MiniMax M3 | verbatim | H200 BF16 TP8 and B200 NVFP4 commands are available; Atlas support is outside this verification. |

## Nemotron 3 Super FP8

Source date: 2026-09-05 UTC. Recipe hardware map marks H100, H200 and B200 verified. The H100 TP4 command in the guide is a separate verbatim example; the hardware builder now emits TP8. The FP8 card's B200/B300 TP1 instruction agrees with the B200 builder. The card does not make that claim for H200.

### 8×H100 / 8×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8/hw/h100.json), [JSON 2](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8/hw/h200.json). Image: `vllm/vllm-openai:latest`.

```bash
vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --tensor-parallel-size 8 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser nemotron_v3
```

### 1×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8/hw/b200.json). Image: `vllm/vllm-openai:latest`.

```bash
vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --tensor-parallel-size 1 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser nemotron_v3
```

The [HF card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8) publishes this distinct command (verbatim; `$MODEL_CKPT` is the card's variable):

```bash
# Optional: --enable-expert-parallel
vllm serve $MODEL_CKPT \
  --served-model-name nvidia/nemotron-3-super \
  --async-scheduling \
  --dtype auto \
  --kv-cache-dtype fp8 \
  --tensor-parallel-size 4 \
  --max-model-len 262144 \
  --enable-expert-parallel \
  --swap-space 0 \
  --trust-remote-code \
  --gpu-memory-utilization 0.9 \
  --max-cudagraph-capture-size 128 \
  --enable-chunked-prefill \
  --mamba-ssm-cache-dtype float32 \
  --reasoning-parser nemotron_v3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder
```

**Resolution:** in [v0.28.0's tool registry](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/tool_parsers/__init__.py#L173), both tool names resolve to `Qwen3EngineToolParser`. Preserve the name in the selected recipe; do not treat the alias as a parser mismatch in this release. [The reasoning registry](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/reasoning/__init__.py#L115) registers `nemotron_v3`. The card's introductory download instructions still mention `super_v3`, while its vLLM command uses the built-in parser and has no plugin flag. Choose the built-in recipe form; equivalence to the custom plugin and end-to-end coherency are **still unverified**, not implied by similar names.

## Nemotron 3 Nano FP8

The root recipe's verified map lists H100/H200 and Intel Arc. B200 below is generated, not marked verified. No speculative feature is declared; scored cells stay spec-off.

### 1×H100 / 1×H200 / generated 1×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8/hw/h100.json), [JSON 2](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8/hw/h200.json), [JSON 3](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8/hw/b200.json). Image: `vllm/vllm-openai:latest`.

```bash
vllm serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 \
  --trust-remote-code \
  --async-scheduling \
  --kv-cache-dtype fp8 \
  --tensor-parallel-size 1 \
  --moe-backend flashinfer_cutlass \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser-plugin nano_v3_reasoning_parser.py \
  --reasoning-parser nano_v3
```

The plugin must exist inside the server's filesystem before launch; the recipe guide links [NVIDIA's `nano_v3_reasoning_parser.py`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8/raw/main/nano_v3_reasoning_parser.py). Pin the model revision when fetching that small file.

**GB10 verdict: reconstructed.** [The GB10 twin](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8/hw/dgx_spark_gb10.json) returned HTTP 404 and GB10 is absent from the root's hardware links. The `v0.28.0-ubuntu2404` GB10 prose example in [the Super recipe](https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16.json) serves **Super NVFP4**, not Nano FP8. Thus a Nano run on that image is a documented campaign adaptation; record its real command/digest rather than calling it a verified Nano GB10 recipe.

## Qwen3.6-35B-A3B FP8

[The dedicated recipe](https://recipes.vllm.ai/Qwen/Qwen3.6-35B-A3B.json) exists, updated 2026-09-02. H100/H200 are marked verified; B200 is generated but absent from that map. Minimum vLLM version is 0.17.0; that minimum does not establish support for every newer parser/feature in the current command.

### 1×H100 / 1×H200 / generated 1×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/Qwen/Qwen3.6-35B-A3B-FP8/hw/h100.json), [JSON 2](https://recipes.vllm.ai/Qwen/Qwen3.6-35B-A3B-FP8/hw/h200.json), [JSON 3](https://recipes.vllm.ai/Qwen/Qwen3.6-35B-A3B-FP8/hw/b200.json). Image: `vllm/vllm-openai:latest`.

```bash
vllm serve Qwen/Qwen3.6-35B-A3B-FP8 \
  --trust-remote-code \
  --tensor-parallel-size 1 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser qwen3 \
  --mm-encoder-tp-mode data
```

The [FP8 card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8) instead demonstrates TP8, `qwen3_coder`, and `qwen3_next_mtp` K2. The XML/coder names are aliases in v0.28.0 as established above. The recipe's MTP feature is `--speculative-config '{"method":"mtp","num_speculative_tokens":3,"moe_backend":"triton"}'`; campaign K2 is **reconstructed**, not the recipe's default K. `--language-model-only` is a declared opt-in feature mutually exclusive with `--mm-encoder-tp-mode data`. The ladder-derived context, concurrency, memory-utilization, prefix-cache and FP8-KV settings are explicit campaign overrides, not part of the command above.

## Qwen3-Next-80B-A3B Instruct FP8

Use the complete HF ID including `Instruct`. Its [card](https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct-FP8) states that only non-thinking mode is supported. The current [recipe](https://recipes.vllm.ai/Qwen/Qwen3-Next-80B-A3B-Instruct-FP8.json) has no reasoning feature. H200 is marked verified; H100/B200 are generated profiles only.

### 8×H100

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/Qwen/Qwen3-Next-80B-A3B-Instruct-FP8/hw/h100.json). Image: `vllm/vllm-openai:latest`.

```bash
vllm serve Qwen/Qwen3-Next-80B-A3B-Instruct-FP8 \
  --tensor-parallel-size 8 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

### 1×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/Qwen/Qwen3-Next-80B-A3B-Instruct-FP8/hw/h200.json). Image: `vllm/vllm-openai:latest`.

```bash
vllm serve Qwen/Qwen3-Next-80B-A3B-Instruct-FP8 \
  --tensor-parallel-size 1 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

### 1×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/Qwen/Qwen3-Next-80B-A3B-Instruct-FP8/hw/b200.json). Image: `vllm/vllm-openai:latest`.

Environment (verbatim JSON values; resolve `$HEAD_IP` / `$IFACE_NAME` on the booked cluster):

```json
{
  "VLLM_USE_DEEP_GEMM": "0"
}
```

```bash
vllm serve Qwen/Qwen3-Next-80B-A3B-Instruct-FP8 \
  --tensor-parallel-size 1 \
  --moe-backend flashinfer_trtllm \
  --attention-backend FLASH_ATTN \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

Optional MTP feature, copied verbatim from recipe arguments:

```bash
--speculative-config '{"method":"qwen3_next_mtp","num_speculative_tokens":2}' --no-enable-chunked-prefill
```

The HF card demonstrates the same method/K without the chunked-prefill override, at TP4. The campaign's two-H100 and added `--reasoning-parser qwen3` flags are **reconstructed**; the latter has no purpose for this non-thinking checkpoint. Do not substitute the separate Thinking checkpoint into an Instruct cell.

## GLM syntax and model-specific constraints

[The CLI documentation](https://docs.vllm.ai/en/latest/cli/serve/#json-cli-arguments) and [v0.28.0 argument parser](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/utils/argparse_utils.py#L118) document dotted JSON keys. The GLM-5.1 FP8 recipe itself emits the following opt-in MTP arguments verbatim:

```bash
--speculative-config.method mtp --speculative-config.num_speculative_tokens 3
```

Thus dotted GLM flags are valid vLLM syntax in this release. GLM-5.3's own [feature JSON](https://recipes.vllm.ai/zai-org/GLM-5.3.json) uses `--speculative-config '{"method":"mtp","num_speculative_tokens":5}'`. Its dotted K5 equivalent is **reconstructed** from the documented syntax. Speculation is opt-in; no speculative flags belong in the spec-off baseline.

### GLM-5.3 FP8

Current image is `vllm/vllm-openai:v0.28.0`, not a confirmed `glm53` pin. The recipe marks B300 and Ascend verified; H100/H200/B200 below are generated profiles. The H200 fit claim appears in variant metadata, not a measured receipt from this work.

### GLM-5.3 16×H100, two nodes

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/zai-org/GLM-5.3/hw/h100.json). Image: `vllm/vllm-openai:v0.28.0`.

Environment (verbatim JSON values; resolve `$HEAD_IP` / `$IFACE_NAME` on the booked cluster):

```json
{
  "GLOO_SOCKET_IFNAME": "$IFACE_NAME",
  "NCCL_SOCKET_IFNAME": "$IFACE_NAME"
}
```

`head_command`:

```bash
vllm serve zai-org/GLM-5.3 \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 0 \
  --master-addr $HEAD_IP \
  --kv-cache-dtype fp8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

`worker_commands[0]`:

```bash
vllm serve zai-org/GLM-5.3 \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 1 \
  --master-addr $HEAD_IP \
  --headless \
  --kv-cache-dtype fp8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

### GLM-5.3 8×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/zai-org/GLM-5.3/hw/h200.json). Image: `vllm/vllm-openai:v0.28.0`.

```bash
vllm serve zai-org/GLM-5.3 \
  --tensor-parallel-size 8 \
  --kv-cache-dtype fp8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

### GLM-5.3 8×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/zai-org/GLM-5.3/hw/b200.json). Image: `vllm/vllm-openai:v0.28.0`.

```bash
vllm serve zai-org/GLM-5.3 \
  --kv-cache-dtype fp8_e4m3 \
  --tensor-parallel-size 8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

**Thinking constraint:** the [recipe](https://recipes.vllm.ai/zai-org/GLM-5.3.json) says thinking is always on; the [card](https://huggingface.co/zai-org/GLM-5.3) offers `reasoning_effort` low/high/max. `enable_thinking=false` is not a supported think-off recipe. The campaign must either define a separate matched thinking workload or leave these cells blocked; parser-separated reasoning does not establish thinking was disabled.

### GLM-5.3-Flash FP8

H100/B200 are marked verified; H200 is generated. The recipe guide explicitly says Hopper does not support FP8 KV for this model and uses BF16 KV. Its omission of `--kv-cache-dtype fp8` on Hopper is intentional. Both GLM-5.3 variants are always-thinking models.

### GLM-5.3-Flash 8×H100 / 8×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/zai-org/GLM-5.3-Flash/hw/h100.json), [JSON 2](https://recipes.vllm.ai/zai-org/GLM-5.3-Flash/hw/h200.json). Image: `vllm/vllm-openai:glm53-flash`.

Environment (verbatim JSON values; resolve `$HEAD_IP` / `$IFACE_NAME` on the booked cluster):

```json
{
  "VLLM_ENGINE_READY_TIMEOUT_S": "3600"
}
```

```bash
vllm serve zai-org/GLM-5.3-Flash \
  --tensor-parallel-size 8 \
  --no-enable-flashinfer-autotune \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

### GLM-5.3-Flash 8×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/zai-org/GLM-5.3-Flash/hw/b200.json). Image: `vllm/vllm-openai:glm53-flash`.

Environment (verbatim JSON values; resolve `$HEAD_IP` / `$IFACE_NAME` on the booked cluster):

```json
{
  "VLLM_ENGINE_READY_TIMEOUT_S": "3600"
}
```

```bash
vllm serve zai-org/GLM-5.3-Flash \
  --tensor-parallel-size 8 \
  --kv-cache-dtype fp8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

### GLM-5.1 / GLM-5.2 fallback rows

These are different checkpoints, not an image-only retry of a GLM-5.3 cell. H200 command snapshots follow. GLM-5.1 marks H200 verified; GLM-5.2 has a generated H200 profile but only B200/B300 and AMD in its verified map. The recipe's opt-in MTP is K3 for 5.1 and K5 for 5.2.

### GLM-5.1 FP8 8×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/zai-org/GLM-5.1-FP8/hw/h200.json). Image: `vllm/vllm-openai:latest`.

```bash
vllm serve zai-org/GLM-5.1-FP8 \
  --trust-remote-code \
  --chat-template-content-format=string \
  --tensor-parallel-size 8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

### GLM-5.2 FP8 8×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/zai-org/GLM-5.2/hw/h200.json). Image: `vllm/vllm-openai:v0.28.0`.

```bash
vllm serve zai-org/GLM-5.2-FP8 \
  --tensor-parallel-size 8 \
  --kv-cache-dtype fp8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm45
```

### GLM-4.5-Air FP8: still unverified for requested SKUs

Both [Air](https://recipes.vllm.ai/zai-org/GLM-4.5-Air.json) and [Air FP8](https://recipes.vllm.ai/zai-org/GLM-4.5-Air-FP8.json) recipe twins returned 404 on 2026-09-05 UTC. [The GLM-4.5 family recipe](https://recipes.vllm.ai/zai-org/GLM-4.5.json) lists only full GLM-4.5 BF16/FP8 variants, not Air. This is evidence of missing dedicated endpoints, not a claim that the model does not exist.

[The Air FP8 card](https://huggingface.co/zai-org/GLM-4.5-Air-FP8) supplies this vLLM command verbatim, but it selects the **BF16 Air ID**, not the FP8 ID:

```bash
vllm serve zai-org/GLM-4.5-Air \
    --tensor-parallel-size 8 \
    --tool-call-parser glm45 \
    --reasoning-parser glm45 \
    --enable-auto-tool-choice \
    --served-model-name glm-4.5-air
```

Requested FP8 2×H100 / 1×H200 / B200: **still unverified**. The team command with `zai-org/GLM-4.5-Air-FP8` and TP2 is reconstructed from family flags. TP2 cannot simultaneously describe a single-H200 run; that proposed cell would require a separately recorded TP1 adaptation. The Air card supports thinking on/off, unlike GLM-5.3.

## Kimi K3 MXFP4

[The HF card](https://huggingface.co/moonshotai/Kimi-K3) confirms native MXFP4 weights and MXFP8 activations from QAT and delegates vLLM deployment to the recipe. It does not supply per-SKU launch commands. The [recipe root](https://recipes.vllm.ai/moonshotai/Kimi-K3.json) is internally stale: metadata still calls the model pre-release and estimated, while the card announces released weights. Weight size must come from the separate HF manifest.

H200/B200 are marked verified. The generated H100 command (32 GPUs, four nodes) is retained in evidence but is not a proposed campaign row. Both two-node hardware defaults use TP16. H200's maxseq5/maxlen32768 values now belong to 16 GPUs, not an eight-H200 profile.

### Kimi 16×H200, TP16, two nodes

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/moonshotai/Kimi-K3/hw/h200.json). Image: `vllm/vllm-openai:latest`.

Environment (verbatim JSON values; resolve `$HEAD_IP` / `$IFACE_NAME` on the booked cluster):

```json
{
  "GLOO_SOCKET_IFNAME": "$IFACE_NAME",
  "NCCL_SOCKET_IFNAME": "$IFACE_NAME",
  "VLLM_ENGINE_READY_TIMEOUT_S": "3600",
  "VLLM_USE_V2_MODEL_RUNNER": "1",
  "VLLM_USE_RUST_FRONTEND": "1",
  "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"
}
```

`head_command`:

```bash
vllm serve moonshotai/Kimi-K3 \
  --trust-remote-code \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 0 \
  --master-addr $HEAD_IP \
  --gpu-memory-utilization 0.97 \
  --max-num-seqs 5 \
  --max-model-len 32768 \
  --moe-backend marlin \
  --disable-custom-all-reduce \
  --no-enable-flashinfer-autotune \
  --max-num-batched-tokens 4096 \
  --attention-backend FLASHMLA \
  --enable-auto-tool-choice \
  --tool-call-parser kimi_k3 \
  --reasoning-parser kimi_k3
```

`worker_commands[0]`:

```bash
vllm serve moonshotai/Kimi-K3 \
  --trust-remote-code \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 1 \
  --master-addr $HEAD_IP \
  --headless \
  --gpu-memory-utilization 0.97 \
  --max-num-seqs 5 \
  --max-model-len 32768 \
  --moe-backend marlin \
  --disable-custom-all-reduce \
  --no-enable-flashinfer-autotune \
  --max-num-batched-tokens 4096 \
  --attention-backend FLASHMLA \
  --enable-auto-tool-choice \
  --tool-call-parser kimi_k3 \
  --reasoning-parser kimi_k3
```

### Kimi 16×B200, TP16, two nodes

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/moonshotai/Kimi-K3/hw/b200.json). Image: `vllm/vllm-openai:latest`.

Environment (verbatim JSON values; resolve `$HEAD_IP` / `$IFACE_NAME` on the booked cluster):

```json
{
  "GLOO_SOCKET_IFNAME": "$IFACE_NAME",
  "NCCL_SOCKET_IFNAME": "$IFACE_NAME",
  "VLLM_ALLREDUCE_USE_FLASHINFER": "1",
  "VLLM_ENGINE_READY_TIMEOUT_S": "3600",
  "VLLM_USE_V2_MODEL_RUNNER": "1",
  "VLLM_USE_RUST_FRONTEND": "1"
}
```

`head_command`:

```bash
vllm serve moonshotai/Kimi-K3 \
  --trust-remote-code \
  --gpu-memory-utilization 0.95 \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 0 \
  --master-addr $HEAD_IP \
  --load-format fastsafetensors \
  --no-enable-flashinfer-autotune \
  --max-model-len 1048576 \
  --kv-cache-dtype fp8 \
  --attention-config '{"use_prefill_query_quantization":true,"mla_prefill_backend":"flashinfer"}' \
  --enable-prefix-caching \
  --prefix-match-unit 128 \
  --enable-auto-tool-choice \
  --tool-call-parser kimi_k3 \
  --reasoning-parser kimi_k3
```

`worker_commands[0]`:

```bash
vllm serve moonshotai/Kimi-K3 \
  --trust-remote-code \
  --gpu-memory-utilization 0.95 \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 1 \
  --master-addr $HEAD_IP \
  --headless \
  --load-format fastsafetensors \
  --no-enable-flashinfer-autotune \
  --max-model-len 1048576 \
  --kv-cache-dtype fp8 \
  --attention-config '{"use_prefill_query_quantization":true,"mla_prefill_backend":"flashinfer"}' \
  --enable-prefix-caching \
  --prefix-match-unit 128 \
  --enable-auto-tool-choice \
  --tool-call-parser kimi_k3 \
  --reasoning-parser kimi_k3
```

### Kimi 16×B200, TP8+PP2 alternative, two nodes

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/moonshotai/Kimi-K3/hw/b200/strategies/multi_node_tp_pp.json). Image: `vllm/vllm-openai:latest`.

Environment (verbatim JSON values; resolve `$HEAD_IP` / `$IFACE_NAME` on the booked cluster):

```json
{
  "GLOO_SOCKET_IFNAME": "$IFACE_NAME",
  "NCCL_SOCKET_IFNAME": "$IFACE_NAME",
  "NCCL_CUMEM_ENABLE": "1",
  "VLLM_ENGINE_READY_TIMEOUT_S": "3600",
  "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS": "1800",
  "VLLM_ALLREDUCE_USE_FLASHINFER": "1",
  "VLLM_USE_V2_MODEL_RUNNER": "1",
  "VLLM_USE_RUST_FRONTEND": "1"
}
```

`head_command`:

```bash
vllm serve moonshotai/Kimi-K3 \
  --trust-remote-code \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 2 \
  --nnodes 2 \
  --node-rank 0 \
  --master-addr $HEAD_IP \
  --gpu-memory-utilization 0.90 \
  --max-num-batched-tokens 8192 \
  --load-format fastsafetensors \
  --no-enable-flashinfer-autotune \
  --max-model-len 1048576 \
  --kv-cache-dtype fp8 \
  --attention-config '{"use_prefill_query_quantization":true,"mla_prefill_backend":"flashinfer"}' \
  --enable-prefix-caching \
  --prefix-match-unit 128 \
  --enable-auto-tool-choice \
  --tool-call-parser kimi_k3 \
  --reasoning-parser kimi_k3
```

`worker_commands[0]`:

```bash
vllm serve moonshotai/Kimi-K3 \
  --trust-remote-code \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 2 \
  --nnodes 2 \
  --node-rank 1 \
  --master-addr $HEAD_IP \
  --headless \
  --gpu-memory-utilization 0.90 \
  --max-num-batched-tokens 8192 \
  --load-format fastsafetensors \
  --no-enable-flashinfer-autotune \
  --max-model-len 1048576 \
  --kv-cache-dtype fp8 \
  --attention-config '{"use_prefill_query_quantization":true,"mla_prefill_backend":"flashinfer"}' \
  --enable-prefix-caching \
  --prefix-match-unit 128 \
  --enable-auto-tool-choice \
  --tool-call-parser kimi_k3 \
  --reasoning-parser kimi_k3
```

**Image still unverified:** those exact JSON fields all say `vllm/vllm-openai:latest`; the same recipe's prerequisites say `vllm/vllm-openai:kimi-k3` and CUDA13/r580+. This source conflict is not resolved by choosing a tag silently. Select and inspect an actual image, capture digest/version, and pass boot/coherency before claiming a validated command.

**Campaign reconstruction:** derive the scored B200 command from the TP8+PP2 pair above, explicitly change maxlen to 49152, add `--language-model-only` and `--served-model-name kimi-k3` on both nodes, and keep the worker's `--headless`. Those edits are not verbatim recipe defaults. The team command omitted the recipe's attention-config needed with FP8 KV and added unverified backend/all-reduce overrides for this layout.

**Speculation:** spec-off is already the rendered default. DSpark is opt-in with external `RedHatAI/Kimi-K3-speculator.dspark`, K8, probabilistic draft sampling and block rejection sampling. Its allowed strategy list excludes `multi_node_tp_pp`; a TP8+PP2 DSpark second row is **still unverified** and must not be described as the published default.

## DeepSeek V4-Flash-0731 FP8

H200/B200 are marked verified; H100 is absent from the verified map and hardware endpoints. Exact recipe commands include DSpark. Campaign spec-off is the explicit removal of the final speculative-config pair; it is a reconstructed baseline derived from these commands.

### DeepSeek 8×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4-Flash/hw/h200.json). Image: `vllm/vllm-openai:v0.28.0`.

```bash
vllm serve deepseek-ai/DeepSeek-V4-Flash-0731 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --block-size 256 \
  --enable-expert-parallel \
  --tensor-parallel-size 8 \
  --tokenizer-mode deepseek_v4 \
  --tool-call-parser deepseek_v4 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4 \
  --reasoning-config '{"reasoning_parser":"deepseek_v4","reasoning_start_str":"","reasoning_end_str":""}' \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}'
```

### DeepSeek 8×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4-Flash/hw/b200.json). Image: `vllm/vllm-openai:v0.28.0`.

```bash
vllm serve deepseek-ai/DeepSeek-V4-Flash-0731 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --block-size 256 \
  --enable-expert-parallel \
  --tensor-parallel-size 8 \
  --attention_config.use_fp4_indexer_cache True \
  --moe-backend deep_gemm_mega_moe \
  --tokenizer-mode deepseek_v4 \
  --tool-call-parser deepseek_v4 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4 \
  --reasoning-config '{"reasoning_parser":"deepseek_v4","reasoning_start_str":"","reasoning_end_str":""}' \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}'
```

**KV resolution, scoped to v0.28.0:** [the sparse MLA backend](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/models/deepseek_v4/sparse_mla.py#L45) accepts `fp8` and `fp8_ds_mla` and labels the former an alias. [The attention resolver](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/models/deepseek_v4/attention.py#L91) normalizes the CLI dtype to `fp8_ds_mla` when the backend uses that packed layout, returning `uint8` storage. Plain-row backends follow another branch. Therefore keep the recipe's `--kv-cache-dtype fp8`; record the effective backend/layout and startup log. [LMCache's recipe](https://docs.lmcache.ai/recipes/deepseek_v4_flash.html) explicitly requests the canonical name with its connector; it is a different integration context, not proof that the vLLM recipe flag is invalid. The [HF card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) links to serving instructions rather than resolving backend layout itself.

**DSpark status:** [issue 47648](https://github.com/vllm-project/vllm/issues/47648) was `closed` in the retrieved API response (updated 2026-07-06). Its discussion contains later failure reports as well as claimed fixes. Neither closure nor source inspection proves fresh H200 correctness. Replace the unconditional “broken on SM90, open” assertion with a version-scoped historical issue and require a GPU check for any spec-on row. The campaign baseline remains spec-off on both engines for parity with Atlas.

## Other recipe-pack models

### Qwen3.8-Flash-Next FP8

Current hardware defaults below are TP4 for all three SKUs. H100/H200 are marked verified; B200 has a generated profile. The older H200 TEP8 command is not the current default. Preserve host PLE offload only where the JSON environment requests it.

### Qwen3.8-Flash-Next 4×H100

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next-FP8/hw/h100.json). Image: `vllm/vllm-openai:qwen38-flash-next`.

Environment (verbatim JSON values; resolve `$HEAD_IP` / `$IFACE_NAME` on the booked cluster):

```json
{
  "VLLM_PLE_CPU_OFFLOAD": "1"
}
```

```bash
vllm serve Qwen/Qwen3.8-Flash-Next-FP8 \
  --max-num-seqs 256 \
  --enable-prefix-caching \
  --no-enable-flashinfer-autotune \
  --tensor-parallel-size 4 \
  --moe-backend triton \
  --gpu-memory-utilization 0.85 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser qwen3
```

### Qwen3.8-Flash-Next 4×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next-FP8/hw/h200.json). Image: `vllm/vllm-openai:qwen38-flash-next`.

```bash
vllm serve Qwen/Qwen3.8-Flash-Next-FP8 \
  --max-num-seqs 256 \
  --enable-prefix-caching \
  --no-enable-flashinfer-autotune \
  --tensor-parallel-size 4 \
  --moe-backend triton \
  --gpu-memory-utilization 0.85 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser qwen3
```

### Qwen3.8-Flash-Next 4×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next-FP8/hw/b200.json). Image: `vllm/vllm-openai:qwen38-flash-next`.

```bash
vllm serve Qwen/Qwen3.8-Flash-Next-FP8 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.90 \
  --enable-prefix-caching \
  --no-enable-flashinfer-autotune \
  --tensor-parallel-size 4 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser qwen3
```

### MiniMax M3

H200/B200 are marked verified. H100 has a generated multi-node BF16 command in evidence but is not marked verified and is not a proposed campaign cell.

### MiniMax M3 BF16 8×H200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/MiniMaxAI/MiniMax-M3/hw/h200.json). Image: `vllm/vllm-openai:minimax-m3`.

```bash
vllm serve MiniMaxAI/MiniMax-M3 \
  --block-size 128 \
  --tensor-parallel-size 8 \
  --tool-call-parser minimax_m3 \
  --enable-auto-tool-choice \
  --reasoning-parser minimax_m3
```

### MiniMax M3 BF16 8×B200 default

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [JSON 1](https://recipes.vllm.ai/MiniMaxAI/MiniMax-M3/hw/b200.json). Image: `vllm/vllm-openai:minimax-m3`.

```bash
vllm serve MiniMaxAI/MiniMax-M3 \
  --block-size 128 \
  --tensor-parallel-size 8 \
  --tool-call-parser minimax_m3 \
  --enable-auto-tool-choice \
  --reasoning-parser minimax_m3
```

### MiniMax M3 NVFP4 8×B200

Verdict: **verbatim**. Retrieved 2026-09-05 UTC. [Hardware JSON](https://recipes.vllm.ai/nvidia/MiniMax-M3-NVFP4/hw/b200.json). Image: `vllm/vllm-openai:minimax-m3`.

Environment:

```json
{
  "VLLM_FLOAT32_MATMUL_PRECISION": "high",
  "VLLM_FLASHINFER_ALLREDUCE_BACKEND": "trtllm"
}
```

```bash
vllm serve nvidia/MiniMax-M3-NVFP4 \
  --block-size 128 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --attention_config.backend FLASHINFER \
  --attention_config.use_trtllm_attention true \
  --attention_config.indexer_kv_dtype fp8 \
  --attention_config.minimax_m3_msa_decode_backend cutlass \
  --tensor-parallel-size 8 \
  --tool-call-parser minimax_m3 \
  --enable-auto-tool-choice \
  --reasoning-parser minimax_m3
```

The [root recipe](https://recipes.vllm.ai/MiniMaxAI/MiniMax-M3.json) names `nvidia/MiniMax-M3-NVFP4` as the NVFP4 variant and requests `VLLM_FLOAT32_MATMUL_PRECISION=high` plus `--trust-remote-code`. Changing the checkpoint creates a separate quantization cell. `--language-model-only` is an explicit text-only adaptation; speculative draft checkpoints must be prefetched separately if enabled.

## Prefix-cache reset between independent ladder runs

The ladder's nonce counter restarts for each new client process, so it does not establish cache independence between A/A launches. Keep the measurement client unchanged and reset the isolated benchmark server before each separate workload/run. In [v0.28.0](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/entrypoints/serve/dev/cache/api_router.py#L20), `POST /reset_prefix_cache` returns `{"success": true|false}`. HTTP 200 alone is insufficient: active requests or asynchronous offload transfers can prevent reset. Drain work, require `success=true`, and retain the raw response as an artifact; do not abort unrelated requests.

[The API server](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/entrypoints/openai/api_server.py#L225) exposes these development routes only with `VLLM_SERVER_DEV_MODE=1`. Add that environment variable explicitly to the isolated control server, then call:

```bash
curl --fail-with-body --silent --show-error -X POST \
  'http://127.0.0.1:8000/reset_prefix_cache?reset_running_requests=false&reset_external=false'
```

This is a source-derived orchestration step, not an executed cache-reset receipt. It is specific to the inspected v0.28.0 Python API server; verify route availability/response on the pinned image. For a server with an external KV connector, local reset alone is insufficient. A separate consistently applied `--no-enable-prefix-caching` experiment is another documented recipe deviation, not an equivalent claim about the prefix-caching recipe.

## Benchmark-client timing boundary

In [v0.28.0 `vllm bench serve`](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/benchmarks/serve.py#L589), TPOT is `(latency - TTFT) / (output_tokens - 1)` for more than one output token. Server-reported usage is preferred, with tokenizer counting as fallback. The [`openai` completions client](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/benchmarks/lib/endpoint_request_func.py#L227) starts TTFT on the first choices-bearing SSE chunk, even when its text is empty, and ends latency at the last choices-bearing chunk; usage-only and DONE events do not advance that timestamp. This differs from the ladder's first/last non-empty visible-content timestamps. A numeric cross-check must report those boundaries and endpoint/workload differences; these formulas alone are not observed TTFT/TPOT agreement.

## Verification method and boundaries

The command oracle is the fetched JSON field, with URL, timestamp and response hash. The 29 rendered recipe command blocks were inserted directly from those fields; card snippets, feature arguments and orchestration adaptations are labeled separately. The field/command equality check and its deliberately altered-command negative case are recorded in [command-check.json](recipe-evidence/command-check.json). This check establishes transcription fidelity only. It does not import vLLM, parse its runtime flags, start containers, download weights, or certify hardware support.

The v0.28.0 source is the oracle for parser aliases, dtype normalization, and dotted JSON syntax. The original recipe documents and PRD were read but not edited. No model was booted as part of this research. Image disagreements, unsupported reasoning modes, reconstructed topologies, and unverified hardware maps remain explicit preflight inputs.

## Proposed exact diffs for the owner

The following patch is a proposal only. It corrects stale claims and points the original files to the full command snapshots above. It does not silently freeze untested image digests or turn reconstructed commands into receipts.

````diff
--- a/docs/campaigns/hopper-atlas-vs-vllm-2026-09/VLLM-RECIPES.md
+++ b/docs/campaigns/hopper-atlas-vs-vllm-2026-09/VLLM-RECIPES.md
@@ -2,6 +2,8 @@
 
 Source of truth is `recipes.vllm.ai` (each recipe has a `.json` twin that renders the exact command per SKU). Confidence per block: **verbatim** = copied from the recipe JSON or the HF model card; **reconstructed** = assembled from secondary sources; **UNVERIFIED** = could not confirm. Re-check the recipe the day of the run; pin the image digest in the artifact.
 
+Verification update (2026-09-05 UTC): [RECIPE-VERIFICATION.md](vllm-control/RECIPE-VERIFICATION.md) contains the exact hardware JSON commands, source hashes, version-scoped resolutions, and remaining gaps. A generated SKU command is not a hardware validation receipt.
+
 Client-side pins for every run (both engines): `temperature 0.0`, `seed 42`, `presence_penalty 0.0`, `frequency_penalty 0.0`, `chat_template_kwargs: {"enable_thinking": false}` for think-off rows, per-request nonce, usage from `stream_options.include_usage`.
 
 ## Nemotron 3 Super 120B-A12B FP8 — `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8`
@@ -9,12 +11,12 @@
 Recipe key `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16`, variant `fp8`. `min_vllm_version 0.17.1`, image `vllm/vllm-openai:latest`. FP8 VRAM floor 149 GB. Verified hardware: H100, H200, B200, RTX Pro 6000, GB300, GB10.
 
 ```bash
-# 4x H100 FP8 (verbatim, recipes.vllm.ai)
+# TP4 FP8 (verbatim recipe guide example; current hardware JSON defaults differ)
 vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 \
   --kv-cache-dtype fp8 --tensor-parallel-size 4 --trust-remote-code \
   --enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser nemotron_v3
 
-# 8x H200 FP8 and 8x B200 FP8: identical flags with --tensor-parallel-size 8 (verbatim)
+# Current FP8 hardware JSON: H100 TP8, H200 TP8, B200 TP1; exact commands in RECIPE-VERIFICATION.md.
 # 2x B200 NVFP4 (verbatim; no --kv-cache-dtype):
 vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4 \
   --tensor-parallel-size 2 --trust-remote-code \
@@ -22,7 +24,7 @@
 ```
 
 ```bash
-# HF model card variant (verbatim) — fuller flag set, H100 cluster
+# HF model card variant (card-derived: MODEL_CKPT substituted) — fuller flag set, TP4
 vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 \
   --served-model-name nvidia/nemotron-3-super --async-scheduling --dtype auto \
   --kv-cache-dtype fp8 --tensor-parallel-size 4 --max-model-len 262144 \
@@ -37,13 +39,13 @@
 
 | Flag | Value | Note |
 |---|---|---|
-| `--tensor-parallel-size` | H100 4 · H200 8 · B200 8 (recipe) vs B200 1 (card) | conflict: pick one source per cell and cite it |
+| `--tensor-parallel-size` | H100 8 · H200 8 · B200 1 (hardware JSON); TP4 guide/card example | choose and cite one complete profile; card does not establish H200 TP1 |
 | `--kv-cache-dtype` | `fp8` | |
 | `--mamba-ssm-cache-dtype` | `float32` | Mamba-2 stability (card) |
 | `--mamba-cache-mode` | `align` | only mode that supports prefix caching on hybrids (experimental) |
 | `--speculative-config` | `'{"method":"mtp","num_speculative_tokens":3}'` | opt-in; required for spec-matched cells |
-| `--tool-call-parser` | `qwen3_xml` (recipe) vs `qwen3_coder` (card, cookbook) | conflict |
-| `--reasoning-parser` | `nemotron_v3` (built-in) vs `super_v3` plugin | conflict |
+| `--tool-call-parser` | `qwen3_xml` (recipe) / `qwen3_coder` (card) | aliases for the same class in vLLM v0.28.0 |
+| `--reasoning-parser` | `nemotron_v3` (built-in recipe/card command) | custom `super_v3` is a separate alternative; equivalence unverified |
 | Dynamo recipe | H200: TP4 FP8 `--moe-backend FLASHINFER_CUTLASS`; B200: TP4 NVFP4 `--moe-backend FLASHINFER_TRTLLM`; MTP draft 3 | image `vllm-runtime:1.3.0-nemotron-super-dev.1` |
 
 ## Nemotron 3 Nano 30B-A3B FP8 — `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8`
@@ -59,7 +61,11 @@
 #   --reasoning-parser-plugin nano_v3_reasoning_parser.py --reasoning-parser nano_v3 --max-model-len 262144
 ```
 
-No MTP documented for Nano → spec off on both engines.
+No MTP documented for Nano → spec off on both engines. Current recipe commands also include `--enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser-plugin nano_v3_reasoning_parser.py --reasoning-parser nano_v3`; fetch the plugin at the pinned model revision. Nano has no GB10 hardware JSON (404). The Super NVFP4 GB10 image example is not a verified Nano FP8 profile.
+
+## Qwen3.6-35B-A3B FP8 and Qwen3-Next Instruct FP8
+
+Dedicated FP8 recipes exist. Qwen3.6 hardware JSON renders TP1 on H100/H200/B200 with `qwen3_xml`, `qwen3` and encoder DP; its opt-in MTP is K3 with Triton draft MoE. Campaign K2/context/cache overrides are reconstructed. Qwen3-Next Instruct FP8 renders H100 TP8, H200 TP1 and B200 TP1, with Hermes tool parsing and no reasoning parser; its card supports only non-thinking mode. Its MTP feature is `qwen3_next_mtp` K2 plus `--no-enable-chunked-prefill`. Exact commands and verified-hardware distinctions are in [RECIPE-VERIFICATION.md](vllm-control/RECIPE-VERIFICATION.md).
 
 ## Qwen3.8-Flash-Next FP8 — `Qwen/Qwen3.8-Flash-Next-FP8` (exists)
 
@@ -72,9 +78,9 @@
   --max-num-seqs 256 --enable-prefix-caching --no-enable-flashinfer-autotune \
   --enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser qwen3
 
-# 8x H200 FP8 — TEP8 (plain TP8 is INCOMPATIBLE with the FP8 checkpoint) (verbatim)
+# 4x H200 FP8 — current hardware JSON default is TP4 (exact rendering in RECIPE-VERIFICATION.md)
 vllm serve Qwen/Qwen3.8-Flash-Next-FP8 \
-  --tensor-parallel-size 8 --enable-expert-parallel --moe-backend triton \
+  --tensor-parallel-size 4 --moe-backend triton \
   --gpu-memory-utilization 0.85 --max-num-seqs 256 --enable-prefix-caching \
   --no-enable-flashinfer-autotune --enable-auto-tool-choice \
   --tool-call-parser qwen3_xml --reasoning-parser qwen3
@@ -106,7 +112,7 @@
 #   --attention_config.use_fp4_indexer_cache True --moe-backend deep_gemm_mega_moe
 ```
 
-Notes: MTP form is `'{"method":"mtp","num_speculative_tokens":2}'`. **DSpark is broken on SM90** (vllm#47648, open) → for Hopper spec-matched cells use MTP or spec-off on both. `--kv-cache-dtype fp8` (recipe) vs `fp8_ds_mla` (LMCache docs): UNVERIFIED which a given vLLM version requires. DP8 proposal (recipes#762) is not the default.
+Notes: MTP form is `'{"method":"mtp","num_speculative_tokens":2}'`. vllm#47648 records historical SM90 DSpark failures; its current API status is closed, which is not fresh hardware validation. Campaign baseline remains spec-off on both. In v0.28.0, the packed DeepSeek MLA backend accepts `fp8` as an alias and normalizes it to `fp8_ds_mla`; record the effective backend/layout. LMCache uses the canonical spelling for its connector. DP8 proposal (recipes#762) is not the default.
 
 ## MiniMax M3 — `MiniMaxAI/MiniMax-M3` (exists; Atlas has M2.7 only)
 
@@ -128,15 +134,16 @@
 |---|---|
 | Model | 2.8T MoE, 16 of 896 experts active, Kimi Delta Attention + Attention Residuals, 1M ctx, native vision (`--language-model-only` for the text A/B) |
 | Weights | 1.56 TB → 8×H200 short by ~430 GB, 8×B200 short by ~120 GB. Single-node is not an option |
-| Image | `vllm/vllm-openai:kimi-k3` (CUDA 13 / cu130, r580+ driver), vLLM ≥ 0.27.1 |
+| Image | Source conflict: hardware JSON says `vllm/vllm-openai:latest`; guide says `kimi-k3` (CUDA 13, r580+). Inspect and pin a real digest before use. |
 | Parsers | `--tool-call-parser kimi_k3 --reasoning-parser kimi_k3` |
 | Compare box | **2×8 B200 (16 GPUs), TP8 + PP2** |
 | Context cap | `--max-model-len 49152` for the A/B |
-| Spec | Off for the scored row; DSpark (`num_speculative_tokens 8`, recipe default) as a second row only |
-| Hopper | 16×H200 with `--moe-backend marlin` (MXFP4 emulated) — label the row "Hopper emulate"; the recipe's 8×H200 profile (`--max-model-len 32768 --max-num-seqs 5`) is a bring-up curiosity, not a receipt |
-
-```bash
-# vLLM control — run on both nodes with RANK 0/1 (team-supplied; verify against the recipe page day-of)
+| Spec | Off is the rendered default. DSpark is opt-in with `RedHatAI/Kimi-K3-speculator.dspark`, K8; its strategy list excludes TP8+PP2, so that second row is unverified. |
+| Hopper | Current JSON: 16×H200 TP16, Marlin, `--max-model-len 32768 --max-num-seqs 5`; label "Hopper emulate". These caps belong to the two-node profile. |
+
+```bash
+# RECONSTRUCTED team proposal — superseded by exact head/worker commands in RECIPE-VERIFICATION.md.
+# Worker requires --headless; FP8 KV requires recipe attention-config. Do not execute this stale sketch.
 vllm serve moonshotai/Kimi-K3 \
   --served-model-name kimi-k3 --trust-remote-code --language-model-only \
   --tensor-parallel-size 8 --pipeline-parallel-size 2 \
@@ -150,12 +157,14 @@
 
 Sources: https://recipes.vllm.ai/moonshotai/Kimi-K3 · https://recipes.vllm.ai/moonshotai/Kimi-K3.json · https://vllm.ai/blog/2026-07-27-k3
 
-## GLM (Z.ai) — `zai-org/GLM-5.3`, `GLM-5.3-Flash`, `GLM-4.5-Air-FP8` (team-supplied 2026-09-04; **reconstructed — verify on recipes.vllm.ai before the run**)
+## GLM (Z.ai) — `zai-org/GLM-5.3`, `GLM-5.3-Flash`, `GLM-4.5-Air-FP8`
+
+Exact GLM-5.3/Flash hardware commands are now in [RECIPE-VERIFICATION.md](vllm-control/RECIPE-VERIFICATION.md). Dotted speculative config is valid vLLM v0.28.0 syntax; GLM-5.3 renders JSON MTP K5 only when opted in. The sketches below are reconstructed. Air FP8 dedicated recipe endpoints return 404; its card command targets BF16 Air TP8, so FP8 H100/H200 sizing remains unverified.
 
 No "GLM 3.5" enterprise SKU exists; the line is 4.5 → 4.7 → 5 → 5.3. Atlas has no `glm` `model_type` — every GLM cell is vLLM-only until a port boots.
 
 ```bash
-# GLM-5.3 FP8 — 8x H200 (published Hopper default). Baseline row = no speculative flags; spec row = MTP 5. Never mixed.
+# GLM-5.3 FP8 — generated 8x H200 profile, absent from verified-hardware map. Baseline removes both speculative flags.
 vllm serve zai-org/GLM-5.3 --kv-cache-dtype fp8 --tensor-parallel-size 8 \
   --speculative-config.method mtp --speculative-config.num_speculative_tokens 5 \
   --tool-call-parser glm47 --reasoning-parser glm45 --enable-auto-tool-choice --served-model-name glm-5.3
@@ -176,7 +185,7 @@
 | GLM-4.5-Air FP8 | 106B / 12B | 2×H100 / 1×H200 | canary only |
 | GLM-4.5 FP8 | 358B / 32B | 8×H100 / 4×H200 | skip unless a customer names it |
 
-Hopper uses `--kv-cache-dtype fp8` (not a Blackwell-specific e4m3 spelling). Coherency extras: think-on/off via `glm45`, one `glm47` tool call, same greedy A/A rule.
+GLM-5.3 uses FP8 KV on Hopper; GLM-5.3-Flash explicitly uses BF16 KV on Hopper and FP8 KV on Blackwell. GLM-5.3 and Flash are always-thinking models controlled by reasoning_effort, so the campaign think-off cells need a separate matched policy or remain blocked. GLM-4.5-Air supports thinking on/off. A parser hiding reasoning from content does not prove thinking was disabled.
 
 ## Hopper vs Blackwell behaviour in vLLM
 
@@ -208,8 +217,8 @@
 
 ## Open conflicts to carry as risks
 
-1. Nemotron Super tool parser `qwen3_xml` vs `qwen3_coder`; reasoning parser `nemotron_v3` vs `super_v3` plugin; B200 GPU count TP8 (recipe) vs TP1 (card).
-2. DeepSeek V4-Flash `fp8` vs `fp8_ds_mla`; DSpark broken on SM90; no H100 recipe.
+1. Nemotron Super tool names alias in v0.28.0; built-in nemotron_v3 exists. Custom plugin equivalence remains unverified. Current B200 FP8 hardware JSON agrees with card TP1.
+2. DeepSeek V4-Flash packed MLA alias resolved on v0.28.0; spec-on runtime and H100 remain unverified. Kimi image/PP speculation conflicts and GLM-5.3 think-off incompatibility remain open.
 3. MiniMax M3 exists for vLLM; Atlas has M2.7 → M3 is a vLLM-only cell until Atlas ports it.
 4. `VLLM_USE_FLASHINFER_MOE_FP4`, `VLLM_USE_TRTLLM_ATTENTION`, `VLLM_ATTENTION_BACKEND` are absent from the official env-var page — UNVERIFIED.
 

--- a/docs/campaigns/hopper-atlas-vs-vllm-2026-09/PRD-atlas-vs-vllm-hopper.md
+++ b/docs/campaigns/hopper-atlas-vs-vllm-2026-09/PRD-atlas-vs-vllm-hopper.md
@@ -98,7 +98,7 @@
 | Compile (Phase 0) | Every kernel in `kernels/<hw>/common` and the model's `nvfp4/` dir emits PTX and passes `ptxas` for the target arch | `scripts/hopper_ptx_gate.sh` ledger; per-arch negative fixture must fail (`redux.sync.max.abs.f32` for sm_90a/sm_12x, `mma.block_scale` for sm_100a). **Result 2026-09-05 (Spark 1, CUDA 13.0.88): sm_90a 870/871, sm_100a 870/871; the one failure is `qwen3.6-35b-a3b/nvfp4/moe_w4a16_grouped_gemm.cu` on both** — receipts in `receipts/` |
 | Preflight | `spark serve --check-kernels` exits 0 on the box; compiled arch matches device CC | `--check-kernels` JSON (`compiled_arch`, `device_cc`); mismatch message is the negative case |
 | Boot | `/health` returns 200 and a 1-token request completes ≤ 30 min after weights are local | `bench/hopper_ab/time_to_ready.sh` JSON; else NO-GO, tear down |
-| Coherency | Two greedy runs, same prompt, byte-identical. Tool-call JSON parses with `finish_reason == "tool_calls"`. No `<think>` in content when thinking is off. GLM rows add: think-on and think-off through the `glm45` reasoning parser, one `glm47`-format tool call | `bench/hopper_ab/coherency_gate.py` (derived from `scripts/test_coherence.py`); known-answer probes from `bench/agentic/coherence_check.py` (391 / Tokyo / rotaregirfer) |
+| Coherency | Two greedy runs, same prompt, byte-identical. Tool-call JSON parses with `finish_reason == "tool_calls"`. No `<think>` in content when thinking is off. GLM-4.5-Air rows add think-on and think-off through glm45. GLM-5.3/Flash are always-thinking: block think-off cells until a separate matched policy is frozen; parser-separated content is not evidence of disabled reasoning. GLM-5.x tool calls use glm47 | `bench/hopper_ab/coherency_gate.py` (derived from `scripts/test_coherence.py`); known-answer probes from `bench/agentic/coherence_check.py` (391 / Tokyo / rotaregirfer) |
 | Latency pack | `lat` and `agent` at C=1 and C=16, 1 warmup + 3 reps, spread ≤ 10 % | `bench/ladder38/harness_w55_conc_ladder.py` output; vacuity floor 0.8 from `crates/atlas-plugin/src/benchmarks/concurrency.rs` |
 | A/B | vLLM leg with §7 flags, same shapes, same box, within 24 h, spec-matched | `bench/hopper_ab/compare.py` refuses mismatched isl/osl/seed/temperature/kwargs |
 | Artifact | JSON per cell + full serve command + `nvidia-smi -q` + image digest + `git sha` + PTX ledger sha | §10 schema; `GateRecord` hardware block |
@@ -159,8 +159,8 @@
 |---|---|---|---|
 | Nemotron 3 Nano FP8 | 1 GPU | `--max-seq-len 32768`; **no MTP** ("No MTP support", recipe fixture) → spec off on both engines | `recipes/nemotron-3-nano*.yaml` |
 | Nemotron 3 Super FP8 | 2×H100: `--world-size 2 --ep-size 2 --tp-size 1` (EP=2 is the only validated Super layout); 1×H200 / 1×B200 may fit at util 0.92 | `--max-seq-len 65536 --ssm-cache-slots 0`; tool parser: MODEL.toml pins `bare_json`, recipe yaml says `qwen3_coder` — **use `bare_json`** (MODEL.toml documents the qwen3_coder token loop). `speculative: true` in the recipe conflicts with `MTP_SUPPORTED_MODEL_TYPES` in `crates/spark-model/src/preflight.rs` — verify on box; default spec **off**. Think-on primary row | `recipes/nemotron-3-super*.yaml`, `kernels/gb10/nemotron-super-120b-a12b/MODEL.toml` |
-| Qwen3.6-35B-A3B FP8 | 1 GPU | `--max-seq-len 65536 --max-batch-size 2 → raise to 32 on HBM; --speculative --num-drafts 2 --mtp-quantization bf16 --tool-call-parser qwen3_coder --lm-head-dtype bf16`; recipe uses `kv_cache_dtype: bf16` — run fp8 KV row too | `recipes/qwen3.6/qwen3.6-35b-a3b-fp8-mtp.yaml`, README Recipe A |
-| Qwen3-Next-80B-A3B FP8 | 1×H200 / 1×B200; 2×H100 EP=2 | `--speculative --mtp-quantization bf16 --tool-call-parser hermes`; GDN state: keep `--ssm-h-dtype` default (f32) for the certified row; `f16-pool` is a perf row only and is incompatible with `--speculative` | `recipes/qwen3-next*.yaml`, `serve_args.rs` |
+| Qwen3.6-35B-A3B FP8 | 1×H100 / 1×H200 / generated 1×B200 | Dedicated FP8 recipe exists: TP1, trust-remote-code, auto tools/qwen3_xml, qwen3 reasoning, encoder DP. Exact commands in `vllm-control/RECIPE-VERIFICATION.md`. | recipe K3/Triton; campaign K2 is an explicit adaptation |
+| Qwen3-Next-80B-A3B Instruct FP8 | 1×H200 / generated 8×H100 / generated 1×B200 | Hermes parser; no reasoning parser; Instruct supports only non-thinking. Requested 2×H100 is reconstructed. | qwen3_next_mtp K2 and no-enable-chunked-prefill, or spec off |
 | DeepSeek V4-Flash FP8 | 8×H200 `--world-size 8 --ep-size 8 --tp-size 1`; 4×B200 EP=4 | TP impossible (MQA). Spec off (public checkpoint ships no usable MTP for Atlas; `docs/deepseek_v4_mtp_support.md` is a design, not shipped). `--kv-cache-dtype fp8`, `--max-batch-size 1 → raise stepwise`, `--oom-guard-mb 512`. Tool parser `deepseek_v4` is accepted by the parser but missing from `flag_values.rs` — rely on auto-resolution, do not pass the flag | `recipes/deepseek-v4/*.yaml`, `docker/gb10/deepseek-v4-flash/nvfp4/Dockerfile` |
 
 ### 6.2 Multi-GPU on one node (never done before — treat as Phase A work)
@@ -183,15 +183,15 @@
 
 | Model | SKU | Recipe line (verbatim source) | Spec-matched form |
 |---|---|---|---|
-| Nemotron 3 Super FP8 | 4×H100 / 8×H200 / 8×B200 | `vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 --kv-cache-dtype fp8 --tensor-parallel-size {4,8,8} --trust-remote-code --enable-auto-tool-choice --tool-call-parser qwen3_xml --reasoning-parser nemotron_v3` (recipes.vllm.ai) | add `--speculative-config '{"method":"mtp","num_speculative_tokens":3}'` on both engines or neither |
-| Nemotron 3 Super FP8 | 1×H200 / 1×B200 | model-card form with `--tensor-parallel-size 1`, `--mamba-ssm-cache-dtype float32`, `--kv-cache-dtype fp8` | same |
+| Nemotron 3 Super FP8 | 8×H100 / 8×H200 / 1×B200 | Current hardware JSON commands in `vllm-control/RECIPE-VERIFICATION.md`; TP4 guide/card example is separate. Tool names qwen3_xml/qwen3_coder alias in v0.28.0. | recipe MTP K3 on both or neither |
+| Nemotron 3 Super FP8 | 1×B200 | model-card form (H200 TP1 unverified) with `--tensor-parallel-size 1`, `--mamba-ssm-cache-dtype float32`, `--kv-cache-dtype fp8` | same |
 | Nemotron 3 Nano FP8 | 1×H100 / 1×H200 | `vllm serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 --trust-remote-code --async-scheduling --kv-cache-dtype fp8 --tensor-parallel-size 1 --moe-backend flashinfer_cutlass` | spec off both |
-| Qwen3.6-35B-A3B FP8 | 1 GPU | no dedicated recipe found — use the ladder38 pattern: `--max-model-len 65536 --max-num-seqs 128 --gpu-memory-utilization 0.90 --enable-prefix-caching --kv-cache-dtype fp8 --tool-call-parser qwen3_coder --reasoning-parser qwen3` (reconstructed) | `'{"method":"mtp","num_speculative_tokens":2}'` to match Atlas `--num-drafts 2` |
-| Qwen3-Next-80B-A3B FP8 | 1×H200 / 2×H100 | vLLM recipe for Qwen3-Next (reconstruct day-of; `--tool-call-parser hermes --reasoning-parser qwen3`) | MTP K matched |
-| GLM-5.3 FP8 | 8×H200 | `vllm serve zai-org/GLM-5.3 --kv-cache-dtype fp8 --tensor-parallel-size 8 --tool-call-parser glm47 --reasoning-parser glm45 --enable-auto-tool-choice --served-model-name glm-5.3` (team-supplied; verify on recipes.vllm.ai day-of; image `vllm/vllm-openai:glm53` or the recipe pin) | `--speculative-config.method mtp --speculative-config.num_speculative_tokens 5` on both or neither |
-| GLM-4.5-Air FP8 | 2×H100 / 1×H200 | `vllm serve zai-org/GLM-4.5-Air-FP8 --tensor-parallel-size 2 --tool-call-parser glm45 --reasoning-parser glm45 --enable-auto-tool-choice` (team-supplied) | spec off both |
-| Kimi K3 MXFP4 | 2×8 B200, TP8 + PP2 | `vllm serve moonshotai/Kimi-K3 --served-model-name kimi-k3 --trust-remote-code --language-model-only --tensor-parallel-size 8 --pipeline-parallel-size 2 --nnodes 2 --node-rank $RANK --master-addr $MASTER --master-port 29501 --moe-backend flashinfer_trtllm --disable-custom-all-reduce --kv-cache-dtype fp8 --enable-prefix-caching --max-model-len 49152 --enable-auto-tool-choice --tool-call-parser kimi_k3 --reasoning-parser kimi_k3` (image `vllm/vllm-openai:kimi-k3`, CUDA 13). Hopper emulate: 16×H200 with `--moe-backend marlin` | scored row spec **off** both; DSpark second row |
-| DeepSeek V4-Flash FP8 | 8×H200 / 8×B200 | `vllm serve deepseek-ai/DeepSeek-V4-Flash-0731 --trust-remote-code --kv-cache-dtype fp8 --block-size 256 --enable-expert-parallel --tensor-parallel-size 8 --tokenizer-mode deepseek_v4 --tool-call-parser deepseek_v4 --enable-auto-tool-choice --reasoning-parser deepseek_v4 --reasoning-config '{...}'`; B200 adds `--attention_config.use_fp4_indexer_cache True --moe-backend deep_gemm_mega_moe` | spec **off** both (Atlas has no V4 MTP; vLLM DSpark is broken on SM90) |
+| Qwen3.6-35B-A3B FP8 | 1×H100 / 1×H200 / generated 1×B200 | Dedicated FP8 recipe exists: TP1, trust-remote-code, auto tools/qwen3_xml, qwen3 reasoning, encoder DP. Exact commands in `vllm-control/RECIPE-VERIFICATION.md`. | recipe K3/Triton; campaign K2 is an explicit adaptation |
+| Qwen3-Next-80B-A3B Instruct FP8 | 1×H200 / generated 8×H100 / generated 1×B200 | Hermes parser; no reasoning parser; Instruct supports only non-thinking. Requested 2×H100 is reconstructed. | qwen3_next_mtp K2 and no-enable-chunked-prefill, or spec off |
+| GLM-5.3 FP8 | generated 8×H200 (not marked verified) | Image v0.28.0; exact JSON commands in `vllm-control/RECIPE-VERIFICATION.md`. Always-thinking; think-off campaign cells blocked until a matched policy is defined. | JSON MTP K5 opt-in; dotted form is valid equivalent syntax |
+| GLM-4.5-Air FP8 | proposed 2×H100 / 1×H200 | Still reconstructed: dedicated twins 404; FP8 card command serves BF16 Air TP8. Single H200 would need TP1, not TP2. | spec off both |
+| Kimi K3 MXFP4 | 2×8 B200, TP8 + PP2 alternative | Exact head/worker JSON in `vllm-control/RECIPE-VERIFICATION.md`; worker headless and FP8 attention-config required. Context49152/text-only are campaign adaptations. JSON latest vs guide kimi-k3 image conflict requires digest validation. Hopper default is 16×H200 TP16/Marlin with maxlen32768/maxseq5. | spec off both; recipe DSpark strategy list excludes TP8+PP2 |
+| DeepSeek V4-Flash FP8 | 8×H200 / 8×B200 | `vllm serve deepseek-ai/DeepSeek-V4-Flash-0731 --trust-remote-code --kv-cache-dtype fp8 --block-size 256 --enable-expert-parallel --tensor-parallel-size 8 --tokenizer-mode deepseek_v4 --tool-call-parser deepseek_v4 --enable-auto-tool-choice --reasoning-parser deepseek_v4 --reasoning-config '{...}'`; B200 adds `--attention_config.use_fp4_indexer_cache True --moe-backend deep_gemm_mega_moe` | spec **off** both (Atlas has no V4 MTP; spec-on still requires hardware verification) |
 
 Fairness pins for the client, both engines (from `bench/ladder38/harness_w55_conc_ladder.py`):
 
@@ -202,7 +202,7 @@
 usage from stream_options.include_usage, not counted deltas
 ```
 
-Known conflicts to resolve before the run and record in the artifact: Super tool parser (`qwen3_xml` recipe vs `qwen3_coder` card), Super reasoning parser (`nemotron_v3` vs `super_v3` plugin), Super B200 GPU count (TP8 recipe vs TP1 card), DeepSeek `fp8` vs `fp8_ds_mla`. Warm-up caps: `--no-enable-flashinfer-autotune`, `VLLM_CACHE_ROOT` compile cache reused across reps, `--max-model-len` no larger than the cell needs. Cross-check client: `vllm bench serve --backend openai ... --random-range-ratio 0.0 --ignore-eos` against both engines (see `VLLM-RECIPES.md`).
+Recipe resolutions and remaining conflicts are recorded in `vllm-control/RECIPE-VERIFICATION.md`: Qwen recipes exist; v0.28.0 aliases the Super tool parsers and DeepSeek packed KV dtype; Kimi image/PP speculation and GLM-5.3 think-off remain unresolved. Treat generated SKU commands separately from verified hardware. Reset prefix cache successfully before each separate ladder process because the nonce counter restarts; in v0.28.0 the isolated benchmark server needs VLLM_SERVER_DEV_MODE=1 and POST /reset_prefix_cache must return success=true. Record this as an orchestration adaptation.
 
 ## 8. Hardware / topology matrix
 
````
