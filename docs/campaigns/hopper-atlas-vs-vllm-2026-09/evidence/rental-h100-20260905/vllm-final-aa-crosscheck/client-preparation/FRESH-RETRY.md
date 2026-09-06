# Fresh vLLM cross-check retry (prepared, not executed)

Run only under the parent's exclusive GPU measurement lease, after all Atlas/Butter work and compiler processes have stopped. This is a standalone cross-check, with no frozen ladder or coherency run added. It does not certify the campaign pair.

The current local and remote client helper both hash to `d2334551e4bb0c370cf6a9d8e9c33a3984d75d3891917ebafa344b871e97a1c1`; the server wrapper both hash to `12d7ac339ef15d6ccd1e4bd3d7da59e6448300509099c0e5ba80ccda626c1808`. The new wrapper refuses if these change. The failed range=1.0 attempt remains under `remote-results/benchmark.qwen38.vllm.agent01/crosscheck/` and its source copy is `run_vllm_crosscheck-range1-failed.py`.

## Command

First run the exact destination guard locally before uploading the new wrapper to `/workspace/atlas-rental/run_vllm_crosscheck_fresh.py`. Then, on the rental:

```sh
python3 /workspace/atlas-rental/run_vllm_crosscheck_fresh.py crosscheck02 --execute
```

Omitting `--execute` prints the plan and performs no remote action. `crosscheck02` must be unused; use another fresh label if it already exists. The wrapper delegates exactly:

```sh
bash /workspace/atlas-rental/serve_qwen38_benchmark.sh vllm crosscheck02 off
python3 /workspace/atlas-rental/run_vllm_crosscheck.py --session-dir /workspace/atlas-rental/results/benchmark.qwen38.vllm.crosscheck02 --out /workspace/atlas-rental/results/benchmark.qwen38.vllm.crosscheck02/crosscheck --num-prompts 8 --execute
```

The server wrapper runs the existing idle-GPU and port-ownership admission, uses the pinned capacity-512 vLLM recipe already captured in `qwen38.vllm.b.lat.c1`, and saves engine argv/environment, ownership, boot and process capture. Both inherited offline flags are enabled. No model/tokenizer download, build or recipe change is required.

Outer wall budget is 600 seconds: readiness is capped at 300 seconds, client at at most 240 seconds (its benchmark subprocess has an inner 180-second limit), with 65 seconds reserved for cleanup. The wrapper checks compiler occupancy before starting and before measuring. It signals only Popen groups it created and stops the separately launched engine using the existing owner-aware `process_launch.py stop`. It records cleanup and fresh GPU/disk telemetry. A readiness failure or timeout is retained as the result; there is no flags retry.

Output is under `results/benchmark.qwen38.vllm.crosscheck02/` and `results/crosscheck-control.crosscheck02/`. Export both after completion. The latter records outer start/client/stop outcomes. A zero orchestration exit still requires inspecting the actual benchmark counts below.

## Actual input correction already proven on CPU

The installed vLLM 0.28 RandomDataset rejected ratio=1.0 because it permits a zero-length minimum. The same installed tokenizer and dataset accepted ratio=0.0 and produced eight nominal 1024/256 samples. That red/green receipt is `remote-results/vllm-crosscheck-range-fix/red-green.json`, with no engine requests. This retry uses ratio=0.0.

The exact client is random text completions (`/v1/completions`), C1, seed42, temperature0, zero presence/frequency penalties, repetition penalty1, ignore_eos=true, eight measured requests plus one readiness test and one explicit warmup. These differ from the frozen essay/chat workload and its EOS policy. Do not call this an identical workload or infer quality from random text.

## Summary fields and acceptance checks

The raw output is `crosscheck/vllm-bench-raw.json`. Installed `vllm/benchmarks/serve.py` lines1265–1290 construct the fields below; lines1330–1363 add percentile metrics. `--save-detailed` retains individual request arrays.

| Field | Expected or interpretation |
|---|---|
| `completed`, `failed` | 8 and 0 |
| `input_lens`, `output_lens` | Eight actual values; expect 1024 and 256 respectively, report any difference |
| `total_input_tokens`, `total_output_tokens` | Expect 8192 and 2048 for measured requests only |
| `duration`, `output_throughput` | Measured seconds and generated tokens/second; cross-check ratio total_output_tokens/duration |
| `median_ttft_ms`, `p50_ttft_ms`, `p99_ttft_ms` | Client TTFT distribution, in ms |
| `median_tpot_ms`, `p50_tpot_ms`, `p99_tpot_ms` | Client TPOT, in ms |
| `median_itl_ms`, `p99_itl_ms` | Inter-token latency, in ms |
| `median_e2el_ms`, `p99_e2el_ms` | Request end-to-end latency, in ms |
| `ttfts`, `itls`, `start_times`, `generated_texts`, `errors` | Per-request evidence; expect eight requests and no nonempty errors |
| `max_concurrent_requests` | vLLM's derived observation, recorded alongside configured C1 |

Require `receipt.json` endpoint-before and endpoint-after exits both0, benchmark exit0, expected counts and saved raw hash. Missing fields mean missing evidence; never fill them with inferred zeros. Timing summaries describe this cross-check alone. Original native engine identity remains null in the campaign artifact; package receipts are supplemental, so this cross-check does not remove the certification blocker.

## Local preparation checks only

The new wrapper's invalid-label input returned2 before any execution path, then valid dry planning returned0. The corrected existing helper dry plan returned0. Both files compile with Python's syntax checker. Lifecycle execution and the actual random benchmark have not been run by this agent; parent owns that final validation.

## Optional latency A/A repeat

Upload both the updated `run_vllm_crosscheck_fresh.py` and `run_vllm_lat_aa.py` after the destination guard. The optional command is:

```sh
python3 /workspace/atlas-rental/run_vllm_crosscheck_fresh.py crosscheck02 --lat-aa --execute
```

The same600second budget applies. A/A starts only with at least345seconds remaining after readiness; otherwise `latency_aa_omitted` records the remaining time and reason, and the cross-check proceeds. The A/A child has180seconds and is an owned subprocess group. A failure retains evidence, stops the owned server and suppresses the subsequent cross-check; it is never reported as a completed repeat.

Before engine requests, the child runs its validator known-bad cases. It then runs original pre-coherency plus exact reversal-exception policy, the unchanged essay harness (nominal1024/256, C1/C16, one warmup plus three timed reps), validates both complete rungs and all output counts, and runs post-coherency/policy. All raw prompt-count sets and individual completion counts remain in ladder.json. Afterward it proves the existing compare.py OSL refusal on a derived copy, then saves the genuine comparison against `benchmark.qwen38.vllm.lat01/ladder.json`. Both inputs are vLLM; the tool's legacy Atlas column holds the new repeat. A tie is not presumed.

The wrapper proceeds to the random cross-check only after successful A/A. Export the entire session and outer-control directories. `aa-complete.json` describes completed quality/ladder work; `aa-compare.json` and the outer receipt separately prove the comparison and whole-operation outcome. No schema or certification state is changed.

Preparation evidence: `aa-prep.json` records refusal of actual original-data copies with a missing rung and OSL257, followed by acceptance of the unchanged completed lat01 JSON. The standalone synthetic selftest also refuses a missing output count. Python syntax checks and optional dry-plan rendering passed; this agent launched no engine requests.
