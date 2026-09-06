# Why the C1 cross-check reports peak concurrency2

The completed eight-request cross-check has configured `max_concurrency=1` and reported `max_concurrent_requests=2`. The latter is a one-second bucket statistic, not an instantaneous overlap count.

Installed vLLM0.28 `benchmarks/serve.py:694–700` floors each successful request's start and end times relative to the first start into integer seconds, then increments every bucket from start through end inclusive. Line706 takes the maximum of those bucket counts. For example, non-overlapping intervals[0.0,0.4] and[0.5,0.9] both increment bucket0, yielding2 while actual overlap is1. The printed label `Peak concurrent requests` therefore supports an easy misinterpretation.

Replaying the same formula from the raw saved start_times, TTFTs and ITLs reproduces the reported peak2. The reconstructed last-token intervals have positive adjacent gaps of187–221µs. This reconstruction differs by a tiny first-token clock-read offset from the exact internal latency field, and it does not reconstruct the entire HTTP response lifetime; no stronger claim is needed. The source at lines963–972 also creates a semaphore from the configured max concurrency and holds it across the complete awaited request function, supporting the configured serial execution.

The raw result stays unchanged:8completed,0failed,8192input and2048output tokens,76.6866278outputtok/s. Report both configuration and bucket statistic with this definition. Do not interpret the2 as proof that the C1 workload ran two simultaneous inference requests or retry the benchmark on that basis.

Evidence: `installed-concurrency-metric-source.json` contains exact source lines and SHA256 for serve.py and the endpoint client; `concurrency-metric-reconstruction.json` contains the raw-data reconstruction and explicit non-overlap counterexample. No vLLM source was edited and no additional engine requests were made.
