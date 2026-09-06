# Qwen3.8 Atlas single-H100 capacity adaptation

The original batch32 profile correctly refused during `--check-kernels`, before normal serve started. The audit loads and constructs the model; its raw log is `remote-results/qwen38.atlas.a.lat.c1/check-kernels.txt`, not `serve.log`. The failed binary is source `f66a262048ac0a6aee4c67444fd0ea5740b46b30`, SHA256 `353d3ca4f8bb288991326f2714b1acb3c6973eeb11132fcc789b703a1810a7c0`. All 17 inspected allocation, reserve, config and scheduler source files are byte-identical between that source and this recipe-change base; see `source-receipt.json`.

A declared rental profile `qwen38-h100-atlas-capacity4` changes only `--max-batch-size 32` to `4` in the existing H100 recipe entry. The entry's notes retain the first refusal, assumptions, and pending runtime gates. The original catalog is retained in `original-catalog.json`. This is a capacity repair derived from allocation size; no throughput search was performed. Prefix snapshots16, rollback depth8, FP32 SSM state, FP8 KV with four BF16 boundary layers, calibration256, spec off, watchdogs, utilization0.90 and context24576 remain unchanged.

## Exact reserve ledger

The actual pinned config has 64 layers, of which48 are GDN SSM and16 attention. Per SSM layer: H =48 value heads ×128 value dimension ×128 key dimension ×4 bytes =3,145,728 bytes; conv =(2×16×128 +48×128) ×4 kernel width ×4 bytes =163,840 bytes. One complete sequence blob is48×(H+conv) =158,859,264 bytes =151.5 MiB. Snapshot pools use FP32 strides even when alternative H modes exist; the failed serve explicitly selected f32.

| Reserve component | Original batch32, GiB | Adapted batch4, GiB |
|---|---:|---:|
| Live SSM slots | 4.734375 | 0.591796875 |
| Eight rollback snapshots per active slot | 37.875 | 4.734375 |
| Sixteen prefix snapshots | 2.3671875 | 2.3671875 |
| GDN prefill at8192 tokens | 0.3466796875 | 0.3466796875 |
| CUDA headroom | 0.5 | 0.5 |
| **Total inference reserve** | **45.8232421875** | **8.5400390625** |

The original total is49,202,331,648 bytes; integer MiB is46923, exactly the observed preflight log. The adapted total is9,169,797,120 bytes. The preflight and runtime snapshot allocator call the same `decode_rollback_ring_slots` decision and allocate the same ring geometry. The state pool additionally allocates one dummy sequence blob (151.5 MiB); the existing512 MiB CUDA headroom covers this standing accounting convention. Prefix hidden snapshots add only16×5120×2 bytes. No reserved ring memory was removed from accounting while still allocated.

Batch16 still needs24.5185546875 GiB reserve. Batch8 needs13.8662109375 GiB, leaving only about0.23 GiB using the rounded log centers; this cannot cover eight simultaneous agent requests. Batch4 is the bounded profile selected for a fresh test.

## What the pre-KV memory contains

The log reports57.2 GiB live in Atlas's allocation ledger, excluding1.6 GiB of other device usage. Its teardown sweep reports61.39 **decimal GB**, the same approximately57.18 GiB, not an additional allocation. Logged site values use **MiB** despite the label `MB`; source units are retained in the receipt.

| Observed live allocation site | MiB | Interpretation |
|---|---:|---|
| fast_weights/mod.rs:413 | 29436.7 | Original1606 uploaded checkpoint tensors retained in WeightStore |
| weight_map/loaders_fp8.rs:229 | 9565.7 |257 NVFP4 packed projections, including runtime requantized FFN/attention/head |
| weight_map/loaders_fp8.rs:230 | 1195.7 | Their NVFP4 scales |
| layers/dense_ffn.rs:653 | 9180.0 |192 persistent FFN MMQ weight repacks |
| weight_loader/qwen35_dense.rs:135 | 3840.0 |48 persistent concatenated native FP8 QKVZ projection buffers |
| Buffer arena (separate log) | 3674.1 |8224-token arena already included in the live ledger |

These rounded buckets explain about55.56 GiB; the remaining approximately1.62–1.64 GiB covers smaller sites, including vision and other model buffers. The failure log only prints the five largest sites, so the remainder is not claimed as an exact subsystem attribution. Layer construction consumed25.85 **decimal GB** (24.08 GiB); it is included in these live allocations, not another additive term.

BF16 dequantization intermediates are explicitly freed by `quantized_from_fp8` after producing the NVFP4 result. FFN transposed twins are also freed after MMQ materialization. The persistent packed NVFP4 projections and MMQ repacks serve decode and prefill respectively; neither can simply be discounted. Original FP8 QKV/Z source weights are explicitly retained as store-owned after their copied concatenation; some original FFN FP8 sources may likewise be redundant for the selected default dispatch, but selective source eviction requires an ownership/alias audit and tests across the native-FP8 and fallback paths. This is future memory-reduction work, not a proven temporary allocation that disappears before inference. A global WeightStore drop would free tensors still referenced by layers. The abandoned-build sweep is expected cleanup on this error path, not evidence by itself of a successful-serve leak.

## KV capacity and C16 semantics

For conservative arithmetic, use the displayed budget's lower rounding endpoint71.25 GiB and the pre-KV live value's upper endpoint57.25 GiB. Do not credit any smaller arena allocation after reducing the batch. Subtracting the8.5400390625 GiB reserve leaves5,862,588,416 bytes =5.4599609375 GiB for KV. This is a bound based on the captured allocation; fresh device memory and allocator behavior still require observation.

Four boundary BF16 attention layers plus twelve FP8 layers, each with4 KV heads and head dimension256, use40,960 bytes per token across K+V. At block size16, one complete block costs655,360 bytes. The conservative budget fits8,945 blocks; excluding the permanent dummy leaves143,104 token positions.

| Frozen cell | Offered requests | Maximum active | Queued when four active | KV bytes for active requests at full output |
|---|---:|---:|---:|---:|
| lat1024/256 C1 |1|1|0|52,428,800 (50 MiB)|
| lat1024/256 C16 |16|4|12|209,715,200 (200 MiB)|
| agent4096/512 C1 |1|1|0|188,743,680 (180 MiB)|
| agent4096/512 C16 |16|4|12|754,974,720 (720 MiB)|

Even four active sequences at the declared24576-token context require98,304 positions =3.75 GiB, inside that bound. Sixteen simultaneous full contexts would require15 GiB and are not what this profile supports. The cache is paged; unused context capacity is not allocated separately per request, and reusable prefix blocks share the same pool subject to eviction/admission.

`--max-num-seqs 128` is already explicit in common args and remains unchanged. Source `serve_load.rs:814` uses it for the request-channel capacity. `scheduler/mod_helpers.rs:202` restricts admissions to max_batch minus active and prefilling counts; pending requests remain queued. Thus the offered-concurrency C16 cells measure queuing behind four active slots and must report that behavior, rather than imply16 simultaneous decoders. No hard global128-request bound is inferred for the internal pending queue.

## CPU proof and stopping rule

`actual_entry_capacity.py` imports the real Atlas recipe renderer, reads the real entry and pinned config, derives the SSOT reserve formula, and checks the conservative paged-KV envelope. Before editing, `original-batch32-red.json` exits1 for zero KV budget and reproduces46923 MiB. The real adapted entry passes (`batch4-green.json`, exit0). A copy using batch8 fails the frozen active-agent KV envelope (`batch8-insufficient-KV-red.json`, exit1). The initial missing import path is retained separately as `initial-harness-import-error.json`; it is not counted as the capacity red.

The oracle is the independently observed original reserve plus the source allocation formulas and paged block sizes. This Python ledger is CPU arithmetic, not execution of Rust/CUDA allocation. Stopping rule: red original and near-capacity control, green declared profile, required recipe/campaign checks, focused commit. The lead must run a fresh accurately labeled audit, boot and coherency gate before measurements; none was launched by this agent.

Validation: Atlas renderer346/346, vLLM renderer258/258, campaign suite ALL85 assertions passed, fmt/typos/diff all exit0. The macOS campaign run skipped48 Linux-only process cases; those are not represented as exercised. The actual agent C16 dry-run exits0 and renders max-batch-size4, max-num-seqs128 and the frozen4096/512 ladder; see `actual-cell-dryrun.json`. Local commit `061d9525bc1c4fff8aec7c96d1b8cb936c9f12f1` contains only the Atlas recipe JSON. Checkout clean; no remote write or GPU action.
