> Historical preparation receipt. The initial range-ratio interpretation was wrong: 1.0 allowed zero-length inputs and the first live attempt failed before HTTP. The installed-dataset red/green proved 0.0 is the fixed-length setting. Use [FRESH-RETRY.md](FRESH-RETRY.md) for the corrected procedure; earlier plan/failed-run files remain preserved.

# Prepared vLLM client cross-check

Prepared only; **no benchmark was started by this agent**. Installed vLLM0.28 CLI help exited0 with CUDA hidden. Its complete help and stderr are preserved alongside source excerpts/hashes. All26 planned flags appear in the installed help. The helper's known-bad request count0 exited2 before filesystem or endpoint access; this proves its8–16 request bound, not a benchmark quality gate.

After the next vLLM server is ready, frozen measurements have finished, and the parent grants a measurement window, verify the Atlas destination before uploading/executing the helper. Run on the rental with the actual session directory and a new output directory:

```sh
python3 /workspace/atlas-rental/run_vllm_crosscheck.py \
  --session-dir /workspace/atlas-rental/results/READY_VLLM_SESSION \
  --out /workspace/atlas-rental/results/crosscheck.qwen38.vllm.random.lat01 \
  --execute
```

The session must contain the live server's `owner.json`, served alias `Qwen/Qwen3.8-27B-FP8` on localhost8000, and the already-staged tokenizer at revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`. The existing campaign endpoint ownership check runs before and after the requests. CUDA is hidden from the benchmark client only. This helper does not start, alter, or stop the server. It refuses an existing output directory.

The generated command is in `plan.json`: backend `openai`, endpoint `/v1/completions`, random input/output1024/256 with range ratio1, eight measured requests, C1, request rate infinity, seed42, temperature0 and zero presence/frequency penalties. The installed source performs one endpoint readiness request and the explicit warmup adds one more, making ten planned requests in total. `--save-result --save-detailed` retains the raw vLLM JSON; stdout/stderr, exact argv, selected environment, ownership checks and GPU/disk snapshots are separate files. The entire client run is capped at180 seconds.

This is a cross-check of the independently implemented measurement client. Random completion content and `ignore_eos=true` differ from the frozen essay chat ladder, so its throughput must not be substituted into the ladder comparison. vLLM reports percentiles over this single eight-request run; those are different estimands from the frozen ladder's mean of three per-repetition percentiles. Read actual input/output token counts and request errors in raw JSON before interpreting rates. Nothing here changes the original failed coherency result or certifies a cell.

`source-reference.json` preserves installed parser/benchmark excerpts: `benchmarks/serve.py` SHA256 `999939debed5ccebaa2e31d5a196c494c9b0ccac993dc85191737324c0bee497`; CLI entry SHA256 `6825a4c145d1a6210f3b104407bfc22feabb5f627912b34f545f4be2ab8d0729`. Initial request setup is near line825, warmups near876, max concurrency argument1589, warmup count1693, detailed output1709, result path1728/1735, and output percentiles1770. Help preparation finished before the native Atlas ladder window beginning00:06:49UTC; no further remote package imports were performed during that window.

`SECTION10-SUPPLEMENT.json` records the completed raw sessions per rung: exact serve argv, selected environment, GPU/driver/query hash, harness checkout and ladder-source hashes, workload, existing engine identity, and original verdict. It is a separate report structure, not a fabricated campaign artifact. Native vLLM engine identity remains null; neither the Python interpreter hash nor the available Atlas binary hash is substituted. The earlier distribution/version/RECORD inventory remains supplemental because it is not bound to each exact process lifetime. Original artifacts and schemas were not changed.
