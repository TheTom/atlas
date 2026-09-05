# Weight-prefetch manifest

Observed 2026-09-05 02:40:54–02:40:56 UTC (2026-09-04 in America/Chicago), using unauthenticated HTTPS requests from the local Mac. All 15 concrete IDs below returned HTTP 200. No checkpoint files or model cards were downloaded for this manifest; only API metadata was fetched. These are storage observations, not GPU fit or model-support results.

The inventory covers every explicit checkpoint ID in PRD §3.1 and §3.2, counting Kimi K3 once. It also covers the concrete Super NVFP4 and MiniMax M3 NVFP4 IDs named in the companion recipes, and includes the §16 27B checkpoint as an extra. The remaining `nvidia/*-NVFP4` ambiguity is recorded below. Names explicitly excluded by §3.3 have no prefetch rows.

## Meaning of size and evidence

**Whole-repository payload bytes** is the exact sum of `siblings[].size` in `https://huggingface.co/api/models/<id>?blobs=true`, once per repository path at the response's full `sha` revision. Every file in every response has a nonnegative integer size. Where `lfs` metadata exists, its payload size equals `size`; Git LFS pointer-file sizes are not used. **Safetensors bytes** sums only paths ending in `.safetensors`, including any auxiliary or draft tensors. It excludes tokenizer files, configuration, indexes, code and other assets. The full-repository commands below therefore correspond to the larger whole-repository sum, not the tensor-only sum.

These are exact logical file lengths, not measured allocated disk space. No weight download was performed, so `du` and actual peak storage are unmeasured. Filesystem allocation, metadata, incomplete downloads, any Xet cache, other revisions, container images and runtime compilation caches require additional capacity. Whole-repository GiB is a rounded display conversion (`bytes / 2^30`); the integer byte columns are authoritative. GPU memory figures in recipes have a different meaning.

The [evidence index](weight-evidence/index.json) records URL, exact request and completion timestamps, HTTP status, selected response headers, complete revision and SHA256 of each raw response. The `.response.json.gz` files are lossless gzip copies of the exact response bodies; `response_sha256` hashes the decompressed bytes and `compressed_sha256` hashes the stored gzip. The [readable file ledger](weight-evidence/file-ledger.json) is derived directly from their `siblings` arrays for review. Raw API responses are the source of truth; the index and ledger are verified derivatives.

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

These commands are a menu for the chosen rental cell, **not a script to download the whole inventory onto the owned Sparks**. The owned-machine limit permits no checkpoint larger than Nano. Nano's payload alone is 32,703,351,602 bytes, leaving at most 7,296,648,398 bytes of the user's decimal 40 GB new-usage cap for all additional storage. The image, download overhead and logs must also fit; the manifest does not certify that they do.

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

Run the verifier from this directory without network access or weights. The negative fixtures must reject missing sizes, LFS size disagreement, a wrong total and a mismatched revision before the real metadata is trusted:

```bash
python3 weight-evidence/verify.py --selftest
python3 weight-evidence/verify.py
```

Observed results: all four negative fixtures rejected, the positive 13-byte fixture passed, and all 15 saved responses passed hash, revision, file-ledger and byte-total checks. The [verification transcript](weight-evidence/verification.txt) records the commands and output. The oracle is the captured raw API response, not the PRD's approximate parameter count or memory estimate.

- Nano's exact repository payload is 32.703 GB, while the recipe's roughly 35 GB figure describes memory planning.
- Kimi K3's exact repository payload is 1,560,998,988,078 bytes (1.561 decimal TB), consistent with the PRD's rounded 1.56 TB weight claim.
- Qwen3.8-Flash-Next's exact repository payload is 185,563,783,577 bytes (185.564 decimal GB). The PRD's 250 GB figure must not be copied into the disk manifest; a disk/VRAM difference alone is not a contradiction or a demonstrated fit.
- All concrete checkpoint queries succeeded. The only missing revision/size/command is the unresolved wildcard expansion described above.
