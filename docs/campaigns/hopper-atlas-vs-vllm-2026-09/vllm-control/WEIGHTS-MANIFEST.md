# Weight-prefetch manifest

## Step D3: recipe identity pins, 2026-09-05 12:52 UTC

**Metadata inventory PASS; recipe pin enforcement FAIL.** The current recipe union contains 10 model keys and 46 profiles (17 Atlas, 29 vLLM), resolving to 15 distinct repositories when GB10 alternatives and external speculative draft models are counted. All 15 returned HTTP 200, `gated: false`, `private: false`, full commit SHAs and complete file sizes. No weights, tokenizer assets or model cards were downloaded. These are metadata observations from the local Mac, not H100/H200/B200 execution or fit results.

Source recipes are frozen at code commit `b2c17cfe30c33c53d28c4fbec35f6204b8cfb14b`; the previous manifest comes from docs commit `0b21f2a5163a739b266fc4d4c5afb61f2fc996e4`. The [machine inventory](../evidence/model-pins-2026-09-05.json) has **one object per model key**, with every engine/SKU profile, actual checkpoint ID, proposed revision, speculative artifact, file ledger, license metadata and raw-response pointer. Recipe snapshots and their SHA256 hashes are in the [source receipt](../evidence/model-pins/source.json).

The collector used `huggingface_hub` 1.8.0, `httpx` 0.28.1 and Python 3.14.6 with `HfApi(token=False).model_info(repo_id, files_metadata=True, token=False, timeout=60)`. Successful observations span 12:52:31.059440–12:52:32.299980 UTC. Each repository directory retains the exact command, stdout, full stderr, exit code, response body, response hash and request timestamps. An omitted `revision` in this metadata call deliberately asks for the current default-branch head. It is not a server launch and not proof of loaded bytes.

**Oracle and stopping rule.** Before any campaign query, a deliberately nonexistent repository produced HTTP 401 / `RepositoryNotFoundError`, exit 2; [full stderr](../evidence/model-pins/known-bad-nonexistent-repo/stderr.txt). The client therefore does not turn a failed lookup into a pin. Before accepting the derived inventory, six known-bad fixtures rejected a missing size, an LFS payload disagreement, a wrong revision, duplicate paths, an unclassified weight format and a wrong response hash; [observed output](../evidence/model-pins/selftest.stdout.txt). The real-data oracle is the SHA256-checked raw Hub response: all paths must have nonnegative payload sizes, LFS sizes must agree, and every full SHA must match the receipt. [Observed output](../evidence/model-pins/assemble.stdout.txt): `15 captured repositories` and `10 model-key objects, 46 profiles`. Stop once every recipe artifact is either recorded with those observations or explicitly unknown after the metadata time box. All 15 were recorded; there are no blocked queries.

### Current primary checkpoint pins

Weight bytes below sum **every `.safetensors` file**, including auxiliary tensors. No other weight format appeared in these 15 inventories. Index/config/tokenizer/code files are excluded from weight bytes and included separately in `repository_payload_bytes`. These are logical payload lengths, not allocated disk or HBM use. Download times are ideal sustained-link lower bounds in seconds: `weight_bytes * 8 / (Gbit/s * 1e9)`, using decimal link rates. They exclude throttling, protocol overhead, filesystem work and retries; whole-repository estimates are also in the JSON.

| Model key | Actual checkpoint / metadata source | Current default SHA | Weight bytes | Gated | License metadata | Seconds at 2 / 10 / 25 Gbit/s |
|---|---|---|---:|---|---|---|
| `deepseek-v4-flash` | [`deepseek-ai/DeepSeek-V4-Flash-0731`](https://huggingface.co/api/models/deepseek-ai/DeepSeek-V4-Flash-0731?blobs=true) | `7872f01b1d1fe23eabc4c98b48bffcef5a386062` | 166,886,535,336 | no | `mit` | 667.546 / 133.509 / 53.404 |
| `glm-5.3` | [`zai-org/GLM-5.3`](https://huggingface.co/api/models/zai-org/GLM-5.3?blobs=true) | `aca966e4e02791568aa6a4ced368624b3d897f42` | 755,632,050,320 | no | `glm-5.3` | 3,022.528 / 604.506 / 241.802 |
| `glm-5.3-flash` | [`zai-org/GLM-5.3-Flash`](https://huggingface.co/api/models/zai-org/GLM-5.3-Flash?blobs=true) | `690b705278a3a58e538fcb37c2ca8b5f9511213c` | 328,337,455,672 | no | `mit` | 1,313.350 / 262.670 / 105.068 |
| `kimi-k3` | [`moonshotai/Kimi-K3`](https://huggingface.co/api/models/moonshotai/Kimi-K3?blobs=true) | `f831ab66814297da540d832a5235f8e904f29d06` | 1,560,936,091,448 | no | `kimi-k3` | 6,243.744 / 1,248.749 / 499.500 |
| `minimax-m3` | [`MiniMaxAI/MiniMax-M3`](https://huggingface.co/api/models/MiniMaxAI/MiniMax-M3?blobs=true) | `f0e1c1e04d40177e4673a22097036854f536e9c0` | 854,176,398,808 | no | `minimax-community` | 3,416.706 / 683.341 / 273.336 |
| `nemotron-3-nano-fp8` | [`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8`](https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8?blobs=true) | `9bee19446c0dfd01f356e10979d225b2a6621944` | 32,682,163,544 | no | `nvidia-nemotron-open-model-license` | 130.729 / 26.146 / 10.458 |
| `nemotron-3-super-fp8` | [`nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8`](https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8?blobs=true) | `744b1880a37996c5d56bf454ae164dfd74d77c4e` | 128,350,001,680 | no | `nvidia-nemotron-open-model-license` | 513.400 / 102.680 / 41.072 |
| `qwen3-next-80b-fp8` | [`Qwen/Qwen3-Next-80B-A3B-Instruct-FP8`](https://huggingface.co/api/models/Qwen/Qwen3-Next-80B-A3B-Instruct-FP8?blobs=true) | `c5f5f263bdd5cc134092897864e8905d8fe7b928` | 82,051,854,384 | no | `apache-2.0` | 328.207 / 65.641 / 26.257 |
| `qwen3.6-35b-a3b-fp8` | [`Qwen/Qwen3.6-35B-A3B-FP8`](https://huggingface.co/api/models/Qwen/Qwen3.6-35B-A3B-FP8?blobs=true) | `95a723d08a9490559dae23d0cff1d9466213d989` | 37,463,662,160 | no | `apache-2.0` | 149.855 / 29.971 / 11.988 |
| `qwen3.8-flash-next-fp8` | [`Qwen/Qwen3.8-Flash-Next-FP8`](https://huggingface.co/api/models/Qwen/Qwen3.8-Flash-Next-FP8?blobs=true) | `236dfdf285828023ca3bcd3f37366c58a3469b13` | 185,523,317,458 | no | `qwen-community-1.0` | 742.093 / 148.419 / 59.367 |

`license: other` is retained with its reported license name/link in the JSON; a metadata license label is not a review of its terms. The metadata returns no license link for Kimi K3 or GLM-5.3, so those fields remain null rather than inventing a URL.

### Atlas alternatives and external speculative artifacts

For **every same-SKU Atlas/vLLM recipe pair in this snapshot, the checkpoint HF ID is identical**: Nano FP8, Super FP8, Qwen3.6 FP8, Qwen3-Next FP8 and DeepSeek V4-Flash. An Atlas `nvfp4` kernel bundle does not, by itself, prove it loads different checkpoint bytes. The JSON compares the actual `hf_id` per SKU.

GB10 is rehearsal only: Atlas Nano, Super and Qwen3-Next recipes name the separate NVFP4 checkpoints below. There is no vLLM GB10 profile for these keys, so same-SKU equality is null, not true. Atlas Qwen3.6 GB10 still names the FP8 checkpoint. GLM-5.3, GLM-5.3-Flash, MiniMax M3, Kimi K3 and Qwen3.8-Flash-Next have no Atlas recipe; no Atlas checkpoint source was inferred for them.

| Artifact role | Actual checkpoint / metadata source | Current default SHA | Weight bytes | Gated | License metadata | Seconds at 2 / 10 / 25 Gbit/s |
|---|---|---|---:|---|---|---|
| `Atlas Nano GB10 NVFP4` | [`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`](https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4?blobs=true) | `6efb4a2a1c1fa277ce7b3df7a1416255011b1c99` | 19,342,796,520 | no | `nvidia-nemotron-open-model-license` | 77.371 / 15.474 / 6.190 |
| `Atlas Super GB10 NVFP4` | [`nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4`](https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4?blobs=true) | `ff433f5493e25d631c9f12b5d55c674229923d02` | 80,317,948,856 | no | `nvidia-nemotron-open-model-license` | 321.272 / 64.254 / 25.702 |
| `Atlas Qwen3-Next GB10 NVFP4` | [`nvidia/Qwen3-Next-80B-A3B-Instruct-NVFP4`](https://huggingface.co/api/models/nvidia/Qwen3-Next-80B-A3B-Instruct-NVFP4?blobs=true) | `8fb2682f136cf94d932a498f18cb1e428832a912` | 50,757,748,320 | no | `apache-2.0` | 203.031 / 40.606 / 16.242 |
| `vLLM MiniMax M3 spec-on draft` | [`Inferact/MiniMax-M3-EAGLE3`](https://huggingface.co/api/models/Inferact/MiniMax-M3-EAGLE3?blobs=true) | `44cafa5ace418d8b22e2958df0c6aa1f2476842c` | 6,527,473,392 | no | `mit` | 26.110 / 5.222 / 2.089 |
| `vLLM Kimi K3 spec-on draft` | [`RedHatAI/Kimi-K3-speculator.dspark`](https://huggingface.co/api/models/RedHatAI/Kimi-K3-speculator.dspark?blobs=true) | `48beb88daae33227c148ea2b78a2ac2f493dbccb` | 9,489,807,826 | no | `apache-2.0` | 37.959 / 7.592 / 3.037 |

The source of each alternate artifact is the explicit HF repository above, at the full SHA shown. Upstream base-model IDs from card metadata are retained where present, but their revisions are not supplied by the cards and remain null. The MiniMax EAGLE3 card names `MiniMaxAI/Minimax-M3-preview` as its base model; the serving recipe names `MiniMaxAI/MiniMax-M3`. That is a provenance difference to check when validating the draft, not an observed incompatibility.

### Findings and exact pin proposals

**P1 — all vLLM recipes leave primary model identity unpinned.** All 29 profiles omit `--revision`; counting multinode workers, that is 36 unpinned serve commands. The evidence probe exits 1 and names each command in [full stderr](../evidence/model-pins/revision-audit.stderr.txt); [exact command](../evidence/model-pins/revision-audit.command.txt), [stdout](../evidence/model-pins/revision-audit.stdout.txt), [exit code](../evidence/model-pins/revision-audit.exit-code.txt). Prefetching a pinned snapshot does not make an unpinned `vllm serve <HF-ID>` select it. Add the following flag to **both the head and every worker command** for the listed model key; no recipe/script/schema was edited in D3.

| Model key | Profiles missing the pin | Exact proposed serve flag |
|---|---|---|
| `deepseek-v4-flash` | h200, b200 | `--revision 7872f01b1d1fe23eabc4c98b48bffcef5a386062` |
| `glm-5.3` | h100, h200, b200 | `--revision aca966e4e02791568aa6a4ced368624b3d897f42` |
| `glm-5.3-flash` | h100, h200, b200 | `--revision 690b705278a3a58e538fcb37c2ca8b5f9511213c` |
| `kimi-k3` | h100, h200, b200 | `--revision f831ab66814297da540d832a5235f8e904f29d06` |
| `minimax-m3` | h100, h200, b200 | `--revision f0e1c1e04d40177e4673a22097036854f536e9c0` |
| `nemotron-3-nano-fp8` | h100, h200, b200 | `--revision 9bee19446c0dfd01f356e10979d225b2a6621944` |
| `nemotron-3-super-fp8` | h100, h200, b200 | `--revision 744b1880a37996c5d56bf454ae164dfd74d77c4e` |
| `qwen3-next-80b-fp8` | h100, h200, b200 | `--revision c5f5f263bdd5cc134092897864e8905d8fe7b928` |
| `qwen3.6-35b-a3b-fp8` | h100, h200, b200 | `--revision 95a723d08a9490559dae23d0cff1d9466213d989` |
| `qwen3.8-flash-next-fp8` | h100, h200, b200 | `--revision 236dfdf285828023ca3bcd3f37366c58a3469b13` |

**P1 — external draft revisions are independently unpinned.** MiniMax M3 and Kimi K3 each reference an external draft in all three SKUs, for six unpinned draft-profile references. Pin the draft separately within the existing `--speculative-config` JSON while retaining every other key. The following are proposals only, with no engine execution. The `revision` field and its forwarding into the draft `ModelConfig` are present in the [official vLLM source at inspected commit `7fbd44cb`](https://github.com/vllm-project/vllm/blob/7fbd44cbe0a90b9c8fd3a94a0f0401ac4b1bc719/vllm/config/speculative.py#L422); [source receipt](../evidence/model-pins/draft-revision-source.json). Verify the selected rental image supports that field before recording it as a working launch.

kimi-k3, all three profiles:

```text
--speculative-config '{"model":"RedHatAI/Kimi-K3-speculator.dspark","num_speculative_tokens":8,"method":"dspark","draft_sample_method":"probabilistic","rejection_sample_method":"block","revision":"48beb88daae33227c148ea2b78a2ac2f493dbccb"}'
```

minimax-m3, all three profiles:

```text
--speculative-config '{"method":"eagle3","model":"Inferact/MiniMax-M3-EAGLE3","num_speculative_tokens":3,"attention_backend":"FLASH_ATTN","revision":"44cafa5ace418d8b22e2958df0c6aa1f2476842c"}'
```

The inventory marks every record `loaded_bytes_proven: false`. Do not copy its SHA into `artifact.model.revision` without evidence that the run actually used that snapshot. The schema already requires this distinction. Current `vllm_render.py` treats an added `--revision` through `--extra` as a recipe adaptation because that flag is absent from its frozen vocabulary; wiring an approved pin into launch and artifact assembly belongs to the lead's follow-on.

### Historical Nano pin and retained prefetch inventory

The rehearsal pin remains `9bee19446c0dfd01f356e10979d225b2a6621944`. The 12:52 UTC default-head query returned the same SHA, but that agreement is a new metadata observation, not a change to the historical run. The JSON records the historical pin separately. The older inventory below is preserved with its original observation time and additional PRD-only repositories; those additional repositories were not re-queried in D3 because they are absent from both current recipe JSON files. In particular, GLM-4.5-Air remains a PRD canary without a current recipe key.

The full previous manifest and verifier remain available at the [immutable docs source](https://github.com/TheTom/atlas/blob/0b21f2a5163a739b266fc4d4c5afb61f2fc996e4/docs/campaigns/hopper-atlas-vs-vllm-2026-09/vllm-control/WEIGHTS-MANIFEST.md). The revised Spark 2 limit is **70 GB of new usage and at least 12 GB free at all times**. The previous 40 GB stop is historical and has been superseded; none of these download commands was executed for D3.

---


Observed 2026-09-05 02:40:54–02:40:56 UTC (2026-09-04 in America/Chicago), using unauthenticated HTTPS requests from the local Mac. All 15 concrete IDs below returned HTTP 200. No checkpoint files or model cards were downloaded for this manifest; only API metadata was fetched. These are storage observations, not GPU fit or model-support results.

The inventory covers every explicit checkpoint ID in PRD §3.1 and §3.2, counting Kimi K3 once. It also covers the concrete Super NVFP4 and MiniMax M3 NVFP4 IDs named in the companion recipes, and includes the §16 27B checkpoint as an extra. The remaining `nvidia/*-NVFP4` ambiguity is recorded below. Names explicitly excluded by §3.3 have no prefetch rows.

## Meaning of size and evidence

**Whole-repository payload bytes** is the exact sum of `siblings[].size` in `https://huggingface.co/api/models/<id>?blobs=true`, once per repository path at the response's full `sha` revision. Every file in every response has a nonnegative integer size. Where `lfs` metadata exists, its payload size equals `size`; Git LFS pointer-file sizes are not used. **Safetensors bytes** sums only paths ending in `.safetensors`, including any auxiliary or draft tensors. It excludes tokenizer files, configuration, indexes, code and other assets. The full-repository commands below therefore correspond to the larger whole-repository sum, not the tensor-only sum.

These are exact logical file lengths, not measured allocated disk space. No weight download was performed, so `du` and actual peak storage are unmeasured. Filesystem allocation, metadata, incomplete downloads, any Xet cache, other revisions, container images and runtime compilation caches require additional capacity. Whole-repository GiB is a rounded display conversion (`bytes / 2^30`); the integer byte columns are authoritative. GPU memory figures in recipes have a different meaning.

The [evidence index](weight-evidence/index.json) records URL, exact request and completion timestamps, HTTP status, selected response headers, complete revision and SHA256 of each raw response. The `.response.json.gz` files are lossless gzip copies of the exact response bodies; `response_sha256` hashes the decompressed bytes and `compressed_sha256` hashes the stored gzip. The [readable file ledger](https://github.com/TheTom/atlas/blob/0b21f2a5163a739b266fc4d4c5afb61f2fc996e4/docs/campaigns/hopper-atlas-vs-vllm-2026-09/vllm-control/weight-evidence/file-ledger.json) is derived directly from their `siblings` arrays for review. Raw API responses are the source of truth; the index and ledger are verified derivatives.

## Inventory

All sources are the live `?blobs=true` API endpoint linked in each row, captured at the UTC date above. Full commit revisions are included again in executable prefetch commands below.

| Campaign slot | HF ID and API source | Revision | All files | Whole-repository payload bytes | Safetensors bytes | Whole-repository GiB |
|---|---|---|---:|---:|---:|---:|
| §3.1 plumbing: Nano FP8 | [`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8`](https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8?blobs=true) | `9bee19446c0dfd01f356e10979d225b2a6621944` | 38 | 32,703,351,602 | 32,682,163,544 | 30.457 |
| §3.1 P0: Super FP8 | [`nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8`](https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8?blobs=true) | `744b1880a37996c5d56bf454ae164dfd74d77c4e` | 45 | 128,379,949,011 | 128,350,001,680 | 119.563 |
| §3.1 blocked P0: Qwen3.6 FP8 | [`Qwen/Qwen3.6-35B-A3B-FP8`](https://huggingface.co/api/models/Qwen/Qwen3.6-35B-A3B-FP8?blobs=true) | `95a723d08a9490559dae23d0cff1d9466213d989` | 56 | 37,493,015,668 | 37,463,662,160 | 34.918 |
| §3.1 P1: Qwen3-Next FP8 | [`Qwen/Qwen3-Next-80B-A3B-Instruct-FP8`](https://huggingface.co/api/models/Qwen/Qwen3-Next-80B-A3B-Instruct-FP8?blobs=true) | `c5f5f263bdd5cc134092897864e8905d8fe7b928` | 18 | 82,082,296,496 | 82,051,854,384 | 76.445 |
| §3.1 P1: DeepSeek V4-Flash | [`deepseek-ai/DeepSeek-V4-Flash-0731`](https://huggingface.co/api/models/deepseek-ai/DeepSeek-V4-Flash-0731?blobs=true) | `7872f01b1d1fe23eabc4c98b48bffcef5a386062` | 74 | 166,898,661,074 | 166,886,535,336 | 155.436 |
| §3.1 vLLM reference: GLM-5.3-Flash | [`zai-org/GLM-5.3-Flash`](https://huggingface.co/api/models/zai-org/GLM-5.3-Flash?blobs=true) | `690b705278a3a58e538fcb37c2ca8b5f9511213c` | 72 | 328,366,172,624 | 328,337,455,672 | 305.815 |
| §3.1 and §3.2 Phase D: Kimi K3 native MXFP4 | [`moonshotai/Kimi-K3`](https://huggingface.co/api/models/moonshotai/Kimi-K3?blobs=true) | `f831ab66814297da540d832a5235f8e904f29d06` | 119 | 1,560,998,988,078 | 1,560,936,091,448 | 1453.794 |
| §3.1 canary: GLM-4.5-Air FP8 | [`zai-org/GLM-4.5-Air-FP8`](https://huggingface.co/api/models/zai-org/GLM-4.5-Air-FP8?blobs=true) | `f9a9c5acf5e543cd24d659a056c5dbcda78ffcfc` | 55 | 112,585,990,794 | 112,562,597,656 | 104.854 |
| §3.2 conditional: MiniMax M2.7 | [`MiniMaxAI/MiniMax-M2.7`](https://huggingface.co/api/models/MiniMaxAI/MiniMax-M2.7?blobs=true) | `d494266a4affc0d2995ba1fa35c8481cbd84294b` | 151 | 230,169,537,355 | 230,134,260,592 | 214.362 |
| §3.2 conditional: Qwen3.8-Flash-Next FP8 | [`Qwen/Qwen3.8-Flash-Next-FP8`](https://huggingface.co/api/models/Qwen/Qwen3.8-Flash-Next-FP8?blobs=true) | `236dfdf285828023ca3bcd3f37366c58a3469b13` | 144 | 185,563,783,577 | 185,523,317,458 | 172.820 |
| §3.2 conditional: MiniMax M3 base checkpoint | [`MiniMaxAI/MiniMax-M3`](https://huggingface.co/api/models/MiniMaxAI/MiniMax-M3?blobs=true) | `f0e1c1e04d40177e4673a22097036854f536e9c0` | 82 | 854,200,504,173 | 854,176,398,808 | 795.536 |
| §3.2 conditional: GLM-5.3 | [`zai-org/GLM-5.3`](https://huggingface.co/api/models/zai-org/GLM-5.3?blobs=true) | `aca966e4e02791568aa6a4ced368624b3d897f42` | 155 | 755,663,689,206 | 755,632,050,320 | 703.767 |
| §3.1 B200 extra: concrete Super NVFP4 expansion | [`nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4`](https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4?blobs=true) | `ff433f5493e25d631c9f12b5d55c674229923d02` | 36 | 80,365,684,262 | 80,317,948,856 | 74.846 |
| §3.2 B200 conditional: MiniMax M3 NVFP4 from companion recipe | [`nvidia/MiniMax-M3-NVFP4`](https://huggingface.co/api/models/nvidia/MiniMax-M3-NVFP4?blobs=true) | `901464083161bf8612a29ff7ad29914cd4ab4a85` | 107 | 250,137,296,832 | 250,103,762,320 | 232.959 |
| §16 additional first paid cell: Qwen3.8-27B FP8 | [`Qwen/Qwen3.8-27B-FP8`](https://huggingface.co/api/models/Qwen/Qwen3.8-27B-FP8?blobs=true) | `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a` | 81 | 30,890,049,597 | 30,866,866,928 | 28.769 |

## Unresolved wildcard and scope boundaries

PRD §3.1 says “Any P0 model” and `nvidia/*-NVFP4` “per MODEL.toml hf_id”. That is not a concrete HF repository ID, and it cannot have a revision, a byte count or a safe download command. The companion `VLLM-RECIPES.md` explicitly identifies `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4`, covered above. It does not identify the corresponding NVIDIA Qwen3.6-35B-A3B NVFP4 repository. That remaining wildcard expansion is **UNRESOLVED: exact checkpoint selection required from the campaign owner**; no repository was guessed and the off-limits kernel registry was not accessed. Once selected, fetch its blobs metadata, add its full revision and sums, and prefetch that identical checkpoint for both engines. This is a checkpoint-selection gap, not an observed HF HTTP failure.

MiniMax M3's B200 NVFP4 ID comes from the explicit companion-recipe line `nvidia/MiniMax-M3-NVFP4`; it is a separate checkpoint from `MiniMaxAI/MiniMax-M3`. Kimi K3 uses only the native `moonshotai/Kimi-K3` checkpoint; no community requant, draft checkpoint, excluded GLM-4.5 or out-of-scope model is silently added. PRD §3.3's excluded Qwen3.8-Max / Qwen3.8-2.4T-A95B and DeepSeek V4-Pro names are intentionally not prefetched.

## Persistent-volume commands

These commands are a menu for the chosen rental cell, **not a script to download the whole inventory onto the owned Sparks**. The original 40 GB rehearsal cap was superseded by 70 GB of new usage with at least 12 GB free at all times on Spark 2. Nano's historical whole-repository payload is 32,703,351,602 bytes. Images, build trees, download overhead and logs also count toward occupancy; this manifest does not certify that a chosen combination fits.

Mount the persistent volume at `/mnt/atlas-campaign` before using this setup. Choose the same container mount path for both engines, record the installed `hf`/`huggingface_hub` version, and retain the exact snapshot path printed by `hf download` in the run artifact. Set cache variables before the CLI starts. [`HF_HOME`, `HF_HUB_CACHE` and `HF_XET_CACHE` are documented cache locations](https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables).

```bash
export HF_HOME=/mnt/atlas-campaign/huggingface
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_XET_CACHE="$HF_HOME/xet"
mkdir -p "$HF_HUB_CACHE" "$HF_XET_CACHE"
```

The commands download the complete repository at an immutable, full commit SHA. The CLI accepts `--revision` and `--cache-dir`, and prints the cached snapshot path. [Hugging Face CLI download documentation](https://huggingface.co/docs/huggingface_hub/en/guides/cli#hf-download).

§3.1 plumbing: Nano FP8:

```bash
hf download nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 \
  --revision 9bee19446c0dfd01f356e10979d225b2a6621944 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.1 P0: Super FP8:

```bash
hf download nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 \
  --revision 744b1880a37996c5d56bf454ae164dfd74d77c4e \
  --cache-dir "$HF_HUB_CACHE"
```

§3.1 blocked P0: Qwen3.6 FP8:

```bash
hf download Qwen/Qwen3.6-35B-A3B-FP8 \
  --revision 95a723d08a9490559dae23d0cff1d9466213d989 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.1 P1: Qwen3-Next FP8:

```bash
hf download Qwen/Qwen3-Next-80B-A3B-Instruct-FP8 \
  --revision c5f5f263bdd5cc134092897864e8905d8fe7b928 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.1 P1: DeepSeek V4-Flash:

```bash
hf download deepseek-ai/DeepSeek-V4-Flash-0731 \
  --revision 7872f01b1d1fe23eabc4c98b48bffcef5a386062 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.1 vLLM reference: GLM-5.3-Flash:

```bash
hf download zai-org/GLM-5.3-Flash \
  --revision 690b705278a3a58e538fcb37c2ca8b5f9511213c \
  --cache-dir "$HF_HUB_CACHE"
```

§3.1 and §3.2 Phase D: Kimi K3 native MXFP4:

```bash
hf download moonshotai/Kimi-K3 \
  --revision f831ab66814297da540d832a5235f8e904f29d06 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.1 canary: GLM-4.5-Air FP8:

```bash
hf download zai-org/GLM-4.5-Air-FP8 \
  --revision f9a9c5acf5e543cd24d659a056c5dbcda78ffcfc \
  --cache-dir "$HF_HUB_CACHE"
```

§3.2 conditional: MiniMax M2.7:

```bash
hf download MiniMaxAI/MiniMax-M2.7 \
  --revision d494266a4affc0d2995ba1fa35c8481cbd84294b \
  --cache-dir "$HF_HUB_CACHE"
```

§3.2 conditional: Qwen3.8-Flash-Next FP8:

```bash
hf download Qwen/Qwen3.8-Flash-Next-FP8 \
  --revision 236dfdf285828023ca3bcd3f37366c58a3469b13 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.2 conditional: MiniMax M3 base checkpoint:

```bash
hf download MiniMaxAI/MiniMax-M3 \
  --revision f0e1c1e04d40177e4673a22097036854f536e9c0 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.2 conditional: GLM-5.3:

```bash
hf download zai-org/GLM-5.3 \
  --revision aca966e4e02791568aa6a4ced368624b3d897f42 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.1 B200 extra: concrete Super NVFP4 expansion:

```bash
hf download nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4 \
  --revision ff433f5493e25d631c9f12b5d55c674229923d02 \
  --cache-dir "$HF_HUB_CACHE"
```

§3.2 B200 conditional: MiniMax M3 NVFP4 from companion recipe:

```bash
hf download nvidia/MiniMax-M3-NVFP4 \
  --revision 901464083161bf8612a29ff7ad29914cd4ab4a85 \
  --cache-dir "$HF_HUB_CACHE"
```

§16 additional first paid cell: Qwen3.8-27B FP8:

```bash
hf download Qwen/Qwen3.8-27B-FP8 \
  --revision 017b9c7af6b5689d5dd426a76e0bc077eb5ca20a \
  --cache-dir "$HF_HUB_CACHE"
```

Use the returned `models--<org>--<name>/snapshots/<sha>` path for both engines and the tokenizer, preserving the HF ID and SHA as artifact provenance. An unpinned server-side HF lookup can select a newer revision even when a pinned snapshot has been prefetched. Prefetch should finish before GPU rental time and before the campaign's 30-minute boot clock begins.

With the standard Hub cache, `blobs/` holds payloads and `snapshots/` holds symlinks to them. Reusing one cache avoids copying payloads for the two engines. Counting dereferenced snapshot files and the blob directory together double-counts data; caching additional revisions may retain additional blobs. [Hugging Face cache layout](https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache).

The commands intentionally use the cache layout. `--local-dir` instead creates a repository-shaped working folder with `.cache/huggingface` download metadata; do not assume that making a separate local directory as well as a full Hub cache has zero storage cost. [Hugging Face local-directory downloads](https://huggingface.co/docs/huggingface_hub/en/guides/download#download-files-to-a-local-folder).

On the rental Linux host, record baseline and post-prefetch allocated bytes without following snapshot symlinks, as well as filesystem free bytes. Include the separately measured Docker image storage and runtime cache locations when enforcing a total usage cap:

```bash
du -s -B1 "$HF_HOME"
df -B1 /mnt/atlas-campaign
```

## Audit and observed differences from planning estimates

The following historical verifier commands apply to the docs-branch checkout containing `weight-evidence/`; they are retained with the original observation and were not rerun for D3. D3 uses the separate verifier and captured responses linked above. The negative fixtures must reject missing sizes, LFS size disagreement, a wrong total and a mismatched revision before the real metadata is trusted:

```bash
python3 weight-evidence/verify.py --selftest
python3 weight-evidence/verify.py
```

Observed results: all four negative fixtures rejected, the positive 13-byte fixture passed, and all 15 saved responses passed hash, revision, file-ledger and byte-total checks. The [verification transcript](https://github.com/TheTom/atlas/blob/0b21f2a5163a739b266fc4d4c5afb61f2fc996e4/docs/campaigns/hopper-atlas-vs-vllm-2026-09/vllm-control/weight-evidence/verification.txt) records the commands and output. The oracle is the captured raw API response, not the PRD's approximate parameter count or memory estimate.

- Nano's exact repository payload is 32.703 GB, while the recipe's roughly 35 GB figure describes memory planning.
- Kimi K3's exact repository payload is 1,560,998,988,078 bytes (1.561 decimal TB), consistent with the PRD's rounded 1.56 TB weight claim.
- Qwen3.8-Flash-Next's exact repository payload is 185,563,783,577 bytes (185.564 decimal GB). The PRD's 250 GB figure must not be copied into the disk manifest; a disk/VRAM difference alone is not a contradiction or a demonstrated fit.
- All concrete checkpoint queries succeeded. The only missing revision/size/command is the unresolved wildcard expansion described above.
