Follow-up from the same H100 and original `Qwen/Qwen3.8-27B-FP8` revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, source `dfc45a185fc36ee84a8351eef21ae1dfc56d527a` and binary SHA256 `da3e60000d55a2aaca67c04b09cd0400553444e45653d911ae828f06103cf606`:

The parallel16/context8192 serving profile booted and passed determinism, tools, think-off, arithmetic and Tokyo again. The frozen gate still fails the same reversal question, with the explicit rental exception recorded separately.

**The intended latency ladder did not run.** Its prerequisite16-request long-prompt capacity burst, using the unchanged frozen prompt generator at nominalISL1024/max_tokens1 with unique nonces, failed to finish within the180-second budget. We stopped there. Free memory stayed at least16,211MiB in45 samples; server stderr contains no CUDA error or OOM. This is a reproducible timeout in the long-prefill/scheduling path, not a valid throughput number or a proven memory-capacity failure. The W8A32 correctness baseline has not yet demonstrated competitive end-to-end latency.

Reproduction: `butter serve-local --model <original pinned snapshot> --max-context 8192 --parallel 16 --host 127.0.0.1 --port 8890`, then16 concurrent frozen essay prompts with `max_tokens:1`, temperature0, seed42, think-off and exact snapshot path as the API model ID. The saved driver captures exact requests/policy and aborts after180s. No flags or source were tuned afterward.

GPU cleanup and fresh empty occupancy passed at2026-09-06T01:06:41.392915UTC.44 raw files are retained and export-hash-verified locally under `/Users/tom/Documents/New project/atlas-campaign-evidence/rental-live/butter-iron-followon/h100/results/butter-block-fp8-lat-20260906T010244Z/`; manifest `butter-block-fp8-lat-sha256.json`.

One log-only finding: the shared loader prints `NVFP4 language load` even though this execution retains the original block-FP8 checkpoint. The tensor/source/binary identities in the preceding report establish the actual format; the log label should be corrected later.
