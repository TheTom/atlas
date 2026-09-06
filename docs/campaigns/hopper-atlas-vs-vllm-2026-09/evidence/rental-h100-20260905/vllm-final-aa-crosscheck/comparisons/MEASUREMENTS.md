# Single H100 Qwen3.8 diagnostic measurements

**Not certified campaign data.** Original NO-GO artifacts and original failed coherency gates remain unchanged. A successful compare.py exit establishes only its workload-header and rung checks; it does not certify engine identity, model revision, precision, or coherency.

All latency headlines below are arithmetic means of the recorded per-repetition percentiles. They are not pooled percentiles. C1 p99 equals the single request in each repetition. Throughput is the harness's mean of timed repetition rates, including prefill. Raw timed repetitions and per-request completion counts are retained verbatim in measurement-summary.json. The harness's prompt_tokens_per_req field is a sorted set of observed counts, not a per-request array.

| Cell | ISL/OSL | Session | C | tok/s mean | TTFT p50 ms | TTFT p99 ms | TPOT p50 ms | Measured prompt counts | Completion counts | Original gate |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| benchmark.qwen38.atlas.native-agent01 | 4096/512 | finished_ladder | 1 | 33.129 | 3194.166 | 3194.166 | 23.989 | [4593] | [512] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.atlas.native-agent01 | 4096/512 | finished_ladder | 16 | 55.120 | 63684.249 | 123654.765 | 60.366 | [4593] | [512] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.atlas.native-head-agent01 | 4096/512 | finished_ladder | 1 | 33.131 | 3194.240 | 3194.240 | 23.990 | [4593] | [512] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.atlas.native-head-agent01 | 4096/512 | finished_ladder | 16 | 61.393 | 57992.007 | 112239.304 | 52.932 | [4593] | [512] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.atlas.native-head-lat01 | 1024/256 | finished_ladder | 1 | 39.349 | 1074.195 | 1074.195 | 21.298 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.atlas.native-head-lat01 | 1024/256 | finished_ladder | 16 | 73.807 | 23476.673 | 45680.003 | 45.449 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.atlas.native-lat01 | 1024/256 | interrupted_session | 1 | 28.926 | 3409.423 | 3409.423 | 21.333 | [1193] | [256] | coherency-pre=False |
| benchmark.qwen38.atlas.native-lat02 | 1024/256 | finished_ladder | 1 | 39.337 | 1075.969 | 1075.969 | 21.298 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.atlas.native-lat02 | 1024/256 | finished_ladder | 16 | 64.998 | 26260.628 | 51356.432 | 52.838 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.agent01 | 4096/512 | finished_ladder | 1 | 78.451 | 387.335 | 387.335 | 12.011 | [4593] | [512] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.agent01 | 4096/512 | finished_ladder | 16 | 638.758 | 3457.176 | 4675.695 | 18.225 | [4593] | [512] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.crosscheck02 | 1024/256 | finished_ladder | 1 | 75.313 | 312.211 | 312.211 | 12.107 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.crosscheck02 | 1024/256 | finished_ladder | 16 | 790.533 | 1325.459 | 1440.959 | 15.051 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.lat01 | 1024/256 | finished_ladder | 1 | 76.928 | 285.632 | 285.632 | 11.928 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| benchmark.qwen38.vllm.lat01 | 1024/256 | finished_ladder | 16 | 790.507 | 1324.001 | 1439.214 | 15.056 | [1193] | [256] | coherency-pre=False; coherency-post=False |
| qwen38.atlas.c.lat.c1 | 1024/256 | finished_ladder | 1 | 51.208 | 932.384 | 932.384 | 15.945 | [1193] | [256] | coherency=True |

Nominal latency shape is ISL 1024 / OSL 256; agent shape is ISL 4096 / OSL 512. Shape appears beside every cell, and only matching workload headers are compared. The actual observed prompt length must be read from the table rather than assumed to be 1024. C16 is offered concurrency; Atlas's capacity profile permits four active decode sequences with the rest queued, whereas vLLM's capacity cap is 512. Warmup outputs are not present in ladder JSON; no warmup percentile series is reconstructed.

## benchmark.qwen38.atlas.native-agent01

Original FP8 overlay; mixed W8A8/W8A16; BF16 head only when captured argv confirms; FP8 KV.

Session status: **finished_ladder**. Unobserved frozen concurrencies: []. The presence of a complete rung does not make an interrupted ladder complete.

Captured native flags: `{"--kv-cache-dtype": "fp8", "--lm-head-dtype": "bf16", "--max-batch-size": "4", "--max-num-seqs": "128"}`. Executable: `{"boot_id": "f7dff0ed-70ad-46d4-8961-c7075e4c6f72", "executable": "/workspace/atlas-rental/bin/5cde118469d5f623c3e26da3055dd9001b781fc2/qwen3.8-27b/spark", "executable_sha256": "5dadfd4df7902d63a2bf03625c74cfb3d864f266c9f350d56d2ad7d5c5981470", "pid": 134585, "start_ticks": 18654869}`.

No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.

The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 15.447 | 4593 | 512 | 3194.631/3194.631 | 23.974 | 33.147 | ['length'] |
| 1 | 1 | 15.459 | 4593 | 512 | 3193.201/3193.201 | 24.002 | 33.120 | ['length'] |
| 2 | 1 | 15.458 | 4593 | 512 | 3194.665/3194.665 | 23.992 | 33.122 | ['length'] |
| 0 | 16 | 148.474 | 73488 | 8192 | 63656.280/123592.289 | 60.339 | 55.175 | ['length'] |
| 1 | 16 | 148.776 | 73488 | 8192 | 63763.949/123767.509 | 60.430 | 55.063 | ['length'] |
| 2 | 16 | 148.612 | 73488 | 8192 | 63632.520/123604.497 | 60.330 | 55.123 | ['length'] |

## benchmark.qwen38.atlas.native-head-agent01

Original FP8 overlay; mixed W8A8/W8A16; BF16 head only when captured argv confirms; FP8 KV.

Session status: **finished_ladder**. Unobserved frozen concurrencies: []. The presence of a complete rung does not make an interrupted ladder complete.

Captured native flags: `{"--kv-cache-dtype": "fp8", "--lm-head-dtype": "bf16", "--max-batch-size": "4", "--max-num-seqs": "128"}`. Executable: `{"boot_id": "f7dff0ed-70ad-46d4-8961-c7075e4c6f72", "executable": "/workspace/atlas-rental/bin/7c786cc50455dee52c11c3bf4097de945fbb8f6a/qwen3.8-27b/spark", "executable_sha256": "23efba747b5b309a1750789e1166055e9b4432e0511462da719e626cce01db64", "pid": 183113, "start_ticks": 18896458}`.

No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.

The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 15.443 | 4593 | 512 | 3188.053/3188.053 | 23.980 | 33.154 | ['length'] |
| 1 | 1 | 15.457 | 4593 | 512 | 3194.275/3194.275 | 23.996 | 33.125 | ['length'] |
| 2 | 1 | 15.461 | 4593 | 512 | 3200.390/3200.390 | 23.993 | 33.115 | ['length'] |
| 0 | 16 | 133.294 | 73488 | 8192 | 57981.634/112079.504 | 52.926 | 61.458 | ['length'] |
| 1 | 16 | 133.486 | 73488 | 8192 | 58017.527/112327.139 | 52.933 | 61.370 | ['length'] |
| 2 | 16 | 133.525 | 73488 | 8192 | 57976.861/112311.269 | 52.938 | 61.352 | ['length'] |

## benchmark.qwen38.atlas.native-head-lat01

Original FP8 overlay; mixed W8A8/W8A16; BF16 head only when captured argv confirms; FP8 KV.

Session status: **finished_ladder**. Unobserved frozen concurrencies: []. The presence of a complete rung does not make an interrupted ladder complete.

Captured native flags: `{"--kv-cache-dtype": "fp8", "--lm-head-dtype": "bf16", "--max-batch-size": "4", "--max-num-seqs": "128"}`. Executable: `{"boot_id": "f7dff0ed-70ad-46d4-8961-c7075e4c6f72", "executable": "/workspace/atlas-rental/bin/7c786cc50455dee52c11c3bf4097de945fbb8f6a/qwen3.8-27b/spark", "executable_sha256": "23efba747b5b309a1750789e1166055e9b4432e0511462da719e626cce01db64", "pid": 182276, "start_ticks": 18862069}`.

Separate arithmetic/protocol diagnostic: C1=True, C16=True; observed client HTTP overlap=16. This does not replace the frozen coherency gate or establish simultaneous GPU rows.

No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.

The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 6.508 | 1193 | 256 | 1075.434/1075.434 | 21.301 | 39.335 | ['length'] |
| 1 | 1 | 6.503 | 1193 | 256 | 1071.352/1071.352 | 21.297 | 39.367 | ['length'] |
| 2 | 1 | 6.507 | 1193 | 256 | 1075.799/1075.799 | 21.294 | 39.345 | ['length'] |
| 0 | 16 | 55.351 | 19088 | 4096 | 23445.516/45530.189 | 46.149 | 74.001 | ['length'] |
| 1 | 16 | 55.554 | 19088 | 4096 | 23487.113/45742.760 | 44.053 | 73.731 | ['length'] |
| 2 | 16 | 55.586 | 19088 | 4096 | 23497.390/45767.059 | 46.145 | 73.688 | ['length'] |

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

## benchmark.qwen38.vllm.crosscheck02

Original FP8 block weights; dynamic W8A8; auto/BF16 KV.

Session status: **finished_ladder**. Unobserved frozen concurrencies: []. The presence of a complete rung does not make an interrupted ladder complete.

No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.

The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.

| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 0 | 1 | 3.472 | 1193 | 256 | 322.253/322.253 | 12.351 | 73.728 | ['length'] |
| 1 | 1 | 3.377 | 1193 | 256 | 312.395/312.395 | 12.016 | 75.808 | ['length'] |
| 2 | 1 | 3.351 | 1193 | 256 | 301.985/301.985 | 11.954 | 76.402 | ['length'] |
| 0 | 16 | 5.183 | 19088 | 4096 | 1325.306/1441.862 | 15.059 | 790.277 | ['length'] |
| 1 | 16 | 5.178 | 19088 | 4096 | 1323.521/1437.632 | 15.043 | 791.090 | ['length'] |
| 2 | 16 | 5.183 | 19088 | 4096 | 1327.551/1443.385 | 15.050 | 790.232 | ['length'] |

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

- [compare-benchmark.qwen38.atlas.native-agent01-vs-benchmark.qwen38.vllm.agent01](compare-benchmark.qwen38.atlas.native-agent01-vs-benchmark.qwen38.vllm.agent01.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-head-agent01-vs-benchmark.qwen38.vllm.agent01](compare-benchmark.qwen38.atlas.native-head-agent01-vs-benchmark.qwen38.vllm.agent01.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-head-lat01-vs-benchmark.qwen38.vllm.crosscheck02](compare-benchmark.qwen38.atlas.native-head-lat01-vs-benchmark.qwen38.vllm.crosscheck02.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-head-lat01-vs-benchmark.qwen38.vllm.lat01](compare-benchmark.qwen38.atlas.native-head-lat01-vs-benchmark.qwen38.vllm.lat01.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-lat01-vs-benchmark.qwen38.vllm.crosscheck02](compare-benchmark.qwen38.atlas.native-lat01-vs-benchmark.qwen38.vllm.crosscheck02.stdout): exit 0; atlas_vs_vllm; input status ['interrupted_session', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-lat01-vs-benchmark.qwen38.vllm.lat01](compare-benchmark.qwen38.atlas.native-lat01-vs-benchmark.qwen38.vllm.lat01.stdout): exit 0; atlas_vs_vllm; input status ['interrupted_session', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.vllm.crosscheck02](compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.vllm.crosscheck02.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.vllm.lat01](compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.vllm.lat01.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-qwen38.atlas.c.lat.c1-vs-benchmark.qwen38.vllm.crosscheck02](compare-qwen38.atlas.c.lat.c1-vs-benchmark.qwen38.vllm.crosscheck02.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-qwen38.atlas.c.lat.c1-vs-benchmark.qwen38.vllm.lat01](compare-qwen38.atlas.c.lat.c1-vs-benchmark.qwen38.vllm.lat01.stdout): exit 0; atlas_vs_vllm; input status ['finished_ladder', 'finished_ladder'].
- [compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.atlas.native-lat01](compare-benchmark.qwen38.atlas.native-lat02-vs-benchmark.qwen38.atlas.native-lat01.stdout): exit 0; atlas_native_after_vs_before; input status ['finished_ladder', 'interrupted_session'].
  Both inputs are Atlas. The tool's legacy Atlas column is the later build and its vLLM column is the earlier build. Neither raw input is relabeled or edited. Captured profile checks: `{"both_captured_bf16_head": true, "both_native_fp8_environment": true, "selected_precision_environment_equal": true, "serve_argv_except_executable_equal": true}`. Missing concurrencies on both inputs are still absent even when compare.py has no NO-PAIR row to display.
- [compare-benchmark.qwen38.atlas.native-head-lat01-vs-benchmark.qwen38.atlas.native-lat01](compare-benchmark.qwen38.atlas.native-head-lat01-vs-benchmark.qwen38.atlas.native-lat01.stdout): exit 0; atlas_native_after_vs_before; input status ['finished_ladder', 'interrupted_session'].
  Both inputs are Atlas. The tool's legacy Atlas column is the later build and its vLLM column is the earlier build. Neither raw input is relabeled or edited. Captured profile checks: `{"both_captured_bf16_head": true, "both_native_fp8_environment": true, "selected_precision_environment_equal": true, "serve_argv_except_executable_equal": true}`. Missing concurrencies on both inputs are still absent even when compare.py has no NO-PAIR row to display.
- [compare-benchmark.qwen38.atlas.native-head-lat01-vs-benchmark.qwen38.atlas.native-lat02](compare-benchmark.qwen38.atlas.native-head-lat01-vs-benchmark.qwen38.atlas.native-lat02.stdout): exit 0; atlas_native_after_vs_before; input status ['finished_ladder', 'finished_ladder'].
  Both inputs are Atlas. The tool's legacy Atlas column is the later build and its vLLM column is the earlier build. Neither raw input is relabeled or edited. Captured profile checks: `{"both_captured_bf16_head": true, "both_native_fp8_environment": true, "selected_precision_environment_equal": true, "serve_argv_except_executable_equal": true}`. Missing concurrencies on both inputs are still absent even when compare.py has no NO-PAIR row to display.
- [compare-benchmark.qwen38.atlas.native-head-agent01-vs-benchmark.qwen38.atlas.native-agent01](compare-benchmark.qwen38.atlas.native-head-agent01-vs-benchmark.qwen38.atlas.native-agent01.stdout): exit 0; atlas_native_after_vs_before; input status ['finished_ladder', 'finished_ladder'].
  Both inputs are Atlas. The tool's legacy Atlas column is the later build and its vLLM column is the earlier build. Neither raw input is relabeled or edited. Captured profile checks: `{"both_captured_bf16_head": true, "both_native_fp8_environment": true, "selected_precision_environment_equal": true, "serve_argv_except_executable_equal": true}`. Missing concurrencies on both inputs are still absent even when compare.py has no NO-PAIR row to display.
- [compare-benchmark.qwen38.vllm.crosscheck02-vs-benchmark.qwen38.vllm.lat01](compare-benchmark.qwen38.vllm.crosscheck02-vs-benchmark.qwen38.vllm.lat01.stdout): exit 0; vllm_after_vs_before; input status ['finished_ladder', 'finished_ladder'].
  Both inputs are vLLM: legacy Atlas column is the later run and vLLM column the earlier run. These actual WIN/LOSS/TIE verdicts are preserved. TIE requires exactly ratio1.0; the identical-input selftest is not a noise-tolerance oracle for independent repeats. Captured profile checks: `{"immutable_engine_identity_proven": false, "selected_precision_environment_equal": true, "serve_argv_except_executable_equal": true}`. No immutable vLLM implementation identity is inferred.

## Pending exports

- benchmark.qwen38.atlas.native-lat01: interrupted_session; complete exported rungs=[1]; unobserved frozen concurrencies=[16]; post-coherency present=False.

Before native Atlas results can be described as checkpoint-native, its captured environment must show ATLAS_DENSE_FP8=1, argv must preserve the checkpoint BF16 head, and the build must include the multi-row native FFN dispatch repair. Arithmetic remains engine-specific (Atlas W8A8/W8A16, vLLM dynamic W8A8, Butter W8A32). KV precision also differs in the existing profiles. The known source audit is ../tooling-fixes/native-fp8-batched-ffn/PRECISION-AUDIT.md.

Missing rungs stay NO-PAIR. Interrupted sessions retain their original stop reason and missing post-gate; finished_utc is never synthesized. Run this script again after the native ladder and its launch/coherency evidence have been exported; it does not edit or repair missing provenance.
