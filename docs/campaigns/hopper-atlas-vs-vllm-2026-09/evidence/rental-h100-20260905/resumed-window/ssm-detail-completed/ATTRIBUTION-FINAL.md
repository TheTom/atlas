# Qwen3.8 native FP8 SSM detail attribution — diagnostic only

The existing 7c786cc binary completed the C1 plus C16 arithmetic diagnostic: all 17 responses passed, client HTTP-attempt overlap reached 16, wrapper exit was 0, and the owned process stopped. Raw recorded time is 2026-09-06 02:10:50–02:11:20 UTC. This is single-H100 data. It is an instrumented short diagnostic, not a frozen throughput result.

All three profile switches were explicitly recorded. `ATLAS_MS_PROFILE=1` forces eager execution without CUDA graphs; the inner switches synchronize around phases. Timings include device work, CPU launches and synchronization overhead. The outer total is the sum of measured transformer-layer and head regions, not full request or scheduler elapsed time.

## Actual four-row steps

The summary grouped by inner `n=4` contains 624 SSM layer invocations. Matching each group of 48 inner records to its following outer step proves that 576 belong to twelve actual n=4 steps and 48 belong to a final n=3 step padded to four. The table below uses only the 576 actual four-row samples. Every step has exactly 48 phase rows and 48 detail rows; no trailing records remain. The raw bytes and row assignment are retained in [ATTRIBUTION-BY-ACTUAL-BATCH.json](ATTRIBUTION-BY-ACTUAL-BATCH.json).

| Region | Median per layer invocation (µs) | Median of per-step sums across 48 SSM layers (ms) |
|---|---:|---:|
| SSM mixer, including its norms and projections | 396 | 19.041 |
| Dense FFN plus residual | 281 | 13.536 |
| QKVZ projection | 87 | 4.191 |
| GDN recurrence | 98 | 4.6885 |
| BA projection/gates | 45 | 2.1285 |
| Convolution/update | 40 | 1.900 |
| Gated recurrent output norm | 36 | 1.7195 |
| SSM output projection | 43 | 2.0655 |
| Input norm | 10 | 0.5035 |
| Post-mixer residual/norm | 11 | 0.5305 |
| Recurrent function return tail | 1 | 0.048 |

The four recurrent subregions together have a median per-step sum of 10.421 ms. The GDN number is accumulated across all four sequence calls in each SSM layer; it is not 98 µs per request. The legacy log label `moe_residual` refers to the dense FFN in this model, which has no routed experts.

Outer per-step medians: total **44.738 ms**, 48 whole SSM layers **32.952 ms**, 16 whole attention layers **10.8275 ms**, final normalization/head **0.9405 ms**. Median per-step shares are 73.62%, 24.27%, and 2.11%. Independently computed medians need not sum exactly.

The single padded-three step had mixer/FFN per-layer medians 489/297 µs; the single two-row drain step had 297/216 µs. One drain sample cannot establish batch scaling.

## What to pursue

The native dense FFN is a substantial remaining cost: 13.536 ms across the SSM layers alone. The recurrent series is also substantial, spread across GDN, BA, convolution and norm launches. These measurements do not justify treating GDN alone as the dominant kernel bottleneck, nor do they determine how much time graph-enabled production can save by batching launches. Nested instrumentation increased whole-SSM wall time versus the earlier outer-only diagnostic; that difference is not a model slowdown measurement.

An existing experimental batched recurrence path is a reasonable separate experiment. `ssm_batched_recurrent_enabled()` defaults false, and the path checks compatible, contiguous per-sequence state storage before selecting batched operators. Before a default change it needs equality/quality tests against the scalar path plus fragmented-slot, padded-row and rollback/state isolation cases proving the fallback and lifecycle behavior. No new flag was enabled and no extra GPU work was run for this analysis. Keep the existing recipe and frozen measurements separate from that experiment.

The attention O projection fix is a distinct source-based dispatch issue. Pinned config establishes hidden size 5120, 24 attention heads and head dimension 256, hence original O weight shape **[5120,6144]**. The existing batch4 example is fixed at N512/K2048 and M4/8/16, so it cannot prove that actual shape or M2 through extra command arguments. Volta owns the narrow example extension and production fix.

## Source bounds

- `crates/spark-model/src/model/trait_impl/decode_a2.rs:261`: outer profiling disables graphs; lines 502–593 bracket whole layers and final normalization/head, and pass padded_n into each layer.
- `crates/spark-model/src/layers/qwen3_ssm/trait_decode_multi_seq.rs:89`: mixer phase starts before the batched mixer, followed by dense FFN/residual; final log is at line 405.
- `crates/spark-model/src/layers/qwen3_ssm/trait_decode_multi_seq/ssm_batched.rs:167`: detailed synchronized timer; projection and normalization scopes are marked by `detail_step!`.
- `crates/spark-model/src/layers/qwen3_ssm/trait_decode_multi_seq/ssm_batched_recurrent.rs:389`: current recurrent path loops over sequences, accumulates its four subtimers, and resets detail_t0 at line 593. Consequently `recurrent_total_tail` is a post-return tail, not a duplicate total recurrence measurement.

Binary SHA-256: `23efba747b5b309a1750789e1166055e9b4432e0511462da719e626cce01db64`. Raw serve-log SHA-256: `6be70f134faefe8828604ff806f291d15f6e3e1bfe62ee44d6c5c48c0f58cda0`. Pinned configuration SHA-256: `74227dd615bf1ea975aa676bdf355a0379858c12f394b5365cd9dfa5fc2c70bc`, HF revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`.
