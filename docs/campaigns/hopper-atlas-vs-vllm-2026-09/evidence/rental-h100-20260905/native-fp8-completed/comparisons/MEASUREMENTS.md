# Single H100 Qwen3.8 diagnostic measurements

**Not certified campaign data.** Original NO-GO artifacts and original failed coherency gates remain unchanged. A successful compare.py exit establishes only its workload-header and rung checks; it does not certify engine identity, model revision, precision, or coherency.

All latency headlines below are arithmetic means of the recorded per-repetition percentiles. They are not pooled percentiles. C1 p99 equals the single request in each repetition. Throughput is the harness's mean of timed repetition rates, including prefill. Raw timed repetitions and per-request completion counts are retained verbatim in measurement-summary.json. The harness's prompt_tokens_per_req field is a sorted set of observed counts, not a per-request array.

| Cell | ISL/OSL | Session | C | tok/s mean | TTFT p50 ms | TTFT p99 ms | TPOT p50 ms | Measured prompt counts | Completion counts | Original gate |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| benchmark.qwen38.atlas.native-lat01 | 1024/256 | interrupted_session | 1 | 28.926 | 3409.423 | 3409.423 | 21.333 | [1193] | [256] | coherency-pre=False |
| benchmark.qwen38.atlas.native-lat02 | 1024/256 | finished_ladder | 1 | 39.337 | 1075.969 | 1075.969 | 21.298 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.atlas.native-lat02 | 1024/256 | finished_ladder | 16 | 64.998 | 26260.628 | 51356.432 | 52.838 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.agent01 | 4096/512 | finished_ladder | 1 | 78.451 | 387.335 | 387.335 | 12.011 | [4593] | [512] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.agent01 | 4096/512 | finished_ladder | 16 | 638.758 | 3457.176 | 4675.695 | 18.225 | [4593] | [512] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.lat01 | 1024/256 | finished_ladder | 1 | 76.928 | 285.632 | 285.632 | 11.928 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.lat01 | 1024/256 | finished_ladder | 16 | 790.507 | 1324.001 | 1439.214 | 15.056 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| qwen38.atlas.c.lat.c1 | 1024/256 | finished_ladder | 1 | 51.208 | 932.384 | 932.384 | 15.945 | [1193] | [256] | coherency=True |

Nominal latency shape is ISL 1024 / OSL 256; agent shape is ISL 4096 / OSL 512. Shape appears beside every cell, and only matching workload headers are compared. The actual observed prompt length must be read from the table rather than assumed to be 1024. C16 is offered concurrency; Atlas's capacity profile permits four active decode sequences with the rest queued, whereas vLLM's capacity cap is 512. Warmup outputs are not present in ladder JSON; no warmup percentile series is reconstructed.

## benchmark.qwen38.atlas.native-lat01

Original FP8 overlay; mixed W8A8/W8A16; BF16 head only when captured argv confirms; FP8 KV.

Session status: **interrupted_session**. Unobserved frozen concurrencies: [16]. The presence of a complete rung does not make an interrupted ladder complete.

Captured native flags: `{"--kv-cache-dtype": "fp8", "--lm-head-dtype": "bf16", "--max-batch-size": "4", "--max-num-seqs": "128"}`. Executable: `{"boot_id": "f7dff0ed-70ad-46d4-8961-c7075e4c6f72", "executable": "/workspace/atlas-rental/bin/b3025ab19d30416a3bbef201f34989bf338e1acd/qwen3.8-27b/spark", "executable_sha256": "e4b7468d6f35ce6dde1251142b23eb528fc23df79950b41d33fcef54fc290494", "pid": 117357, "start_ticks": 18440876}`.

Operator budget stop: Native C16 sustained about3 decode tokens/s per active sequence; expected warmup+3reps would exceed1200s measurement cap. Preserve completedC1 rung and partialC16 evidence; prioritize narrow kernel repair. No certification or completedC16 claimed. Full action and process evidence remain in the JSON receipt.

No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.

The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 8.836 | 1193 | 256 | 3407.199/3407.199 | 21.287 | 28.971 | ['length'] |
| 1 | 1 | 8.869 | 1193 | 256 | 3410.986/3410.986 | 21.401 | 28.864 | ['length'] |
| 2 | 1 | 8.845 | 1193 | 256 | 3410.084/3410.084 | 21.311 | 28.942 | ['length'] |

## benchmark.qwen38.atlas.native-lat02

Original FP8 overlay; mixed W8A8/W8A16; BF16 head only when captured argv confirms; FP8 KV.

Session status: **finished_ladder**. Unobserved frozen concurrencies: []. The presence of a complete rung does not make an interrupted ladder complete.

Captured native flags: `{"--kv-cache-dtype": "fp8", "--lm-head-dtype": "bf16", "--max-batch-size": "4", "--max-num-seqs": "128"}`. Executable: `{"boot_id": "f7dff0ed-70ad-46d4-8961-c7075e4c6f72", "executable": "/workspace/atlas-rental/bin/5cde118469d5f623c3e26da3055dd9001b781fc2/qwen3.8-27b/spark", "executable_sha256": "5dadfd4df7902d63a2bf03625c74cfb3d864f266c9f350d56d2ad7d5c5981470", "pid": 133602, "start_ticks": 18607775}`.

Separate arithmetic/protocol diagnostic: C1=True, C16=True; observed client HTTP overlap=16. This does not replace the frozen coherency gate or establish simultaneous GPU rows.

No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.

The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 6.509 | 1193 | 256 | 1073.913/1073.913 | 21.309 | 39.332 | ['length'] |
| 1 | 1 | 6.506 | 1193 | 256 | 1076.860/1076.860 | 21.289 | 39.345 | ['length'] |
| 2 | 1 | 6.509 | 1193 | 256 | 1077.134/1077.134 | 21.297 | 39.332 | ['length'] |
| 0 | 16 | 63.096 | 19088 | 4096 | 26318.459/51400.871 | 51.449 | 64.917 | ['length'] |
| 1 | 16 | 63.030 | 19088 | 4096 | 26232.727/51330.437 | 53.529 | 64.985 | ['length'] |
| 2 | 16 | 62.924 | 19088 | 4096 | 26230.698/51337.989 | 53.536 | 65.094 | ['length'] |

## benchmark.qwen38.vllm.agent01

Original FP8 block weights; dynamic W8A8; auto/BF16 KV.

Session status: **finished_ladder**. Unobserved frozen concurrencies: []. The presence of a complete rung does not make an interrupted ladder complete.

No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.

The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 6.524 | 4593 | 512 | 385.023/385.023 | 12.012 | 78.482 | ['length'] |
| 1 | 1 | 6.528 | 4593 | 512 | 387.487/387.487 | 12.013 | 78.429 | ['length'] |
| 2 | 1 | 6.527 | 4593 | 512 | 389.495/389.495 | 12.010 | 78.440 | ['length'] |
| 0 | 16 | 12.810 | 73488 | 8192 | 3445.008/4663.309 | 18.221 | 639.513 | ['length'] |
| 1 | 16 | 12.826 | 73488 | 8192 | 3461.633/4677.295 | 18.218 | 638.716 | ['length'] |
| 2 | 16 | 12.839 | 73488 | 8192 | 3464.887/4686.479 | 18.237 | 638.046 | ['length'] |

## benchmark.qwen38.vllm.lat01

Original FP8 block weights; dynamic W8A8; auto/BF16 KV.

Session status: **finished_ladder**. Unobserved frozen concurrencies: []. The presence of a complete rung does not make an interrupted ladder complete.

No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.

The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 3.333 | 1193 | 256 | 290.604/290.604 | 11.928 | 76.814 | ['length'] |
| 1 | 1 | 3.325 | 1193 | 256 | 283.029/283.029 | 11.926 | 77.004 | ['length'] |
| 2 | 1 | 3.326 | 1193 | 256 | 283.264/283.264 | 11.931 | 76.967 | ['length'] |
| 0 | 16 | 5.179 | 19088 | 4096 | 1320.416/1437.005 | 15.054 | 790.853 | ['length'] |
| 1 | 16 | 5.179 | 19088 | 4096 | 1324.349/1439.787 | 15.048 | 790.939 | ['length'] |
| 2 | 16 | 5.187 | 19088 | 4096 | 1327.237/1440.850 | 15.067 | 789.728 | ['length'] |

## qwen38.atlas.c.lat.c1

Default Atlas: NVFP4 attention/FFN/head, native FP8 GDN; FP8 KV.

Session status: **finished_ladder**. Unobserved frozen concurrencies: [16]. The presence of a complete rung does not make an interrupted ladder complete.

Original artifact: **NO-GO**, failing stage `serve`. Rental profile qwen38-h100-atlas-capacity4: single-H100 capacity adaptation of the existing H200 27B campaign recipe, not a performance-tuned result. The original batch32 profile and failed qwen38.atlas.a.lat.c1 kernel audit are retained: 57.2 GiB pre-KV plus 45.823 GiB inference reserve exceeded the 71.3 GiB budget. Only max-batch-size changes from 32 to 4; the eight-slot rollback ring, 16 prefix snapshots, watchdogs, numerical flags, TP1/EP1, spec off and context24576 remain unchanged. The resulting reserve is 8.540 GiB. Conservative rounding of that audit leaves at least 5.459 GiB for paged KV, enough in the capacity model for both frozen ladders and four full contexts; a fresh audit/boot/coherency must still prove runtime viability. max-num-seqs128 remains explicit: C16 is offered concurrency with at most four active sequences and the rest queued. Preserve that scheduling distinction in measurements. Retain pinned snapshot proof; target mtp_layers=0. | invalid model launch evidence: actual Atlas process executable and argv must name spark

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 4.999 | 1193 | 256 | 931.120/931.120 | 15.948 | 51.214 | ['length'] |
| 1 | 1 | 4.996 | 1193 | 256 | 932.024/932.024 | 15.933 | 51.244 | ['length'] |
| 2 | 1 | 5.003 | 1193 | 256 | 934.009/934.009 | 15.955 | 51.166 | ['length'] |

## Existing comparison tool receipts

Known-bad input is a derived copy with only OSL increased by1; originals were hash-checked unchanged. Its exit2 and exact stderr are saved before positive comparisons. Output WIN/LOSS/TIE labels are the tool's throughput arithmetic, not a certified or precision-matched campaign conclusion.

- [compare-benchmark.qwen38.atlas.native-lat01-vs-benchmark.qwen38.vllm.lat01](compare-benchmark.qwen38.atlas.native-lat01-vs-benchmark.qwen38.vllm.lat01.stdout): exit 0; atlas_vs_vllm; input status ['interrupted_session', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.vllm.lat01](compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.vllm.lat01.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-qwen38.atlas.c.lat.c1-vs-benchmark.qwen38.vllm.lat01](compare-qwen38.atlas.c.lat.c1-vs-benchmark.qwen38.vllm.lat01.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.atlas.native-lat01](compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.atlas.native-lat01.stdout): exit 0; atlas_native_after_vs_before; input status ['finished_ladder', 'interrupted_session'].
  Both inputs are Atlas. The tool's legacy Atlas column is the later build and its vLLM column is the earlier build. Neither raw input is relabeled or edited. Captured profile checks: `{"both_captured_bf16_head": true, "both_native_fp8_environment": true, "selected_precision_environment_equal": true, "serve_argv_except_executable_equal": true}`. Missing concurrencies on both inputs are still absent even when compare.py has no NO-PAIR row to display.

## Pending exports

- benchmark.qwen38.atlas.native-lat01: interrupted_session; complete exported rungs=[1]; unobserved frozen concurrencies=[16]; post-coherency present=False.

Before native Atlas results can be described as checkpoint-native, its captured environment must show ATLAS_DENSE_FP8=1, argv must preserve the checkpoint BF16 head, and the build must include the multi-row native FFN dispatch repair. Arithmetic remains engine-specific (Atlas W8A8/W8A16, vLLM dynamic W8A8, Butter W8A32). KV precision also differs in the existing profiles. The known source audit is ../tooling-fixes/native-fp8-batched-ffn/PRECISION-AUDIT.md.

Missing rungs stay NO-PAIR. Interrupted sessions retain their original stop reason and missing post-gate; finished_utc is never synthesized. Run this script again after the native ladder and its launch/coherency evidence have been exported; it does not edit or repair missing provenance.
