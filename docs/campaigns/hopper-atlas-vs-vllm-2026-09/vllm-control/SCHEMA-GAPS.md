# Schema and instrument gaps

Reviewed against campaign PRD §§4, 9 and 10 and the unchanged
`bench/ladder38/harness_w55_conc_ladder.py` at Git file revision
`60370b9532a7af5319c99d6c2b93972d4f046d56`. These are source observations,
not hardware performance measurements. Hardware execution was blocked by the
40 GB storage cap; see [the report](REPORT.md) and
[storage evidence](gb10-dryrun/storage-preflight.json).

No complete section 10 cell artifact was fabricated. The files in
`gb10-dryrun/` are explicitly typed preflight or blocked-execution records.
A missing measurement is null or NOT_RUN, never zero, false-as-a-measurement,
CERTIFIED, or an invented hash. The following gaps also apply when hardware
execution becomes possible.

| Field or claim | What the instrument actually provides | Required treatment |
|---|---|---|
| `engine_version.git_sha` | Ladder has no server Git revision | Capture installed vLLM version/source metadata from the pinned image. If absent, leave null and identify the image digest as the immutable deployment identity. |
| `engine_version.image_digest` | Ladder records neither image nor digest | Capture Docker RepoDigests and the platform manifest digest before launch. This dry run resolved a prospective digest but did not run it; it belongs under `planned_image`, not observed engine version. |
| `engine_version.binary_sha256` | vLLM is a Python package with multiple native libraries, not one `spark` binary | The schema needs a defined hash target or a nullable/not-applicable representation. Do not substitute the client hash or invent a binary SHA. |
| Harness Git SHA | Not present in §10 or ladder header; `driver_sha256` is the ladder source file SHA256 | Add a `client` provenance block with checkout SHA, file Git revision, file SHA256, Python/aiohttp versions, and exact invocation. Keep these distinct from the engine's Git SHA. |
| `model.revision`, `quant` | Ladder's `model` can be a served alias | Record the pinned HF snapshot revision and model configuration. A manifest proves an API revision exists; it does not prove those bytes were loaded. |
| `hardware` identity/driver/CUDA | Ladder only saves an unstructured `nvidia-smi` clock/power string | Capture `nvidia-smi -q`, its SHA256, GPU UUID/count and driver on the server. Distinguish the driver's advertised CUDA compatibility from the container's CUDA runtime/toolkit version. |
| `hardware.sm_clock_mhz` | One string sampled **before** each measured batch begins, on the client host | Preserve every string with its context; no under-load clock mean can be inferred. The PRD's statement that this sample is inside the rep is contradicted by the call order. An idle 208 MHz reading cannot be a performance clock. |
| `topology.matched` | No topology or paired Atlas run is emitted | Capture server TP/EP/world size and compare provenance. A vLLM-only plumbing run cannot establish matched Atlas topology. Kimi additionally needs PP and node count, which §10 omits. |
| `serve_command` | Not emitted by ladder | Record argv plus environment, Docker argv/mounts, external parser path/hash, effective server configuration and launch time. A reconstructed command must be marked planned, not executed. |
| `workload.isl` | `make_prompt()` uses `isl - 12` **filler words**, then adds nonce and suffix | This is nominal ISL, not tokenizer-exact input length. Preserve nominal ISL alongside observed usage. The unchanged essay builder produces 1,056/4,128 whitespace words for nominal 1,024/4,096; this does not establish token counts. |
| Observed input lengths | Each rep stores total `prompt_tokens` and a sorted **set** of `prompt_tokens_per_req` | Preserve both. Individual multiplicities and request associations are not recoverable. Do not call the workload exactly 1,024/4,096 tokens without usage evidence. |
| Penalties and prompt mode | Request code pins penalties to zero, but JSON omits them; `W55_PROMPT_MODE` changes the suffix without changing the source hash | Capture the environment and inspected source hash. Set `W55_PROMPT_MODE=essay` explicitly. Comparator source-hash equality alone does not establish environment parity. |
| `workload.spec` | No server speculation state, method or draft count in ladder JSON | Record explicit launch configuration/effective state. The comparator cannot enforce spec matching using a bare ladder file. This is still a certification gap. |
| Prefix-cache parity | `_seq = 0` restarts in each new client process | Run A and B can produce identical prompts and reuse prefixes. Within-process nonce uniqueness does not prove cache misses across invocations or shapes. Use a documented identical reset procedure before each process, or explicitly disable prefix caching for both and label the recipe adaptation. See recipe verification's reset endpoint/version caveat. |
| Warmup | One separate warmup batch runs per rung; its entire result is discarded | The first saved `rep: 0` is measured, **not** warmup. Discard the preceding batch as specified, but report that its raw results, errors and vacuity are unavailable. Preserving warmup evidence requires an owner change to the ladder. |
| `boot.pass` | Old readiness output used `status`; repaired output adds `passed` and `total_s` | Map `passed` explicitly. The repaired gate requires health plus a valid nonempty one-token completion within one launch deadline. `first_token_s` is non-streaming one-token response latency including framing, not the ladder's SSE TTFT. |
| `coherency` | Three Boolean checks and explanations; no raw text series/response hashes | Preserve the complete gate JSON. Determinism means equal nonempty content, not semantic correctness; the prime prompt is not validated for correct primes. Tool arguments now satisfy the declared schema, but correctness of a weather result is not measured. |
| `metrics.ttft_p50_ms`, `ttft_p99_ms`, `tpot_p50_ms`, `e2e_p50_s` | A percentile per measured rep; per-request latency values are discarded | Pooled cell percentiles cannot be reconstructed. Comparator exposes the arithmetic mean of per-rep percentiles for continuity; label it exactly that. Add percentile series/reducer metadata to §10, or leave pooled fields null until the owner defines their meaning. |
| `metrics.tok_s_series` and `tok_s_mean` | Emitted from measured batches | Retain the raw series and corresponding batch walls/token counts. Mean throughput is an unweighted mean of rep rates, not total tokens divided by total elapsed time. |
| Vacuity | Per-request completion token counts are retained for successful responses | Repaired comparator checks **every** timed request against the 80% floor, rejects missing usage/counts, and retains INVALID rows. Warmup vacuity and failures that crash the client before writing remain unknown. |
| Spread | Raw rate series exists; PRD gate is ≤10% | Repaired comparator calculates spread from raw rep rates and excludes unstable rows. Do not rerun a bad cell into silence. Exact A/A TIE is arithmetic only; no statistical equivalence tolerance is frozen. |
| Empty/failed streaming responses | `n_ok` means no transport/HTTP exception; absent usage may still be `n_ok`. TTFT falls back to full E2E if no visible content. | Treat missing usage/empty output as a finding. A non-null TTFT alone is not proof of a token. Coherency separately rejects empty replies. |
| TPOT availability | Zero TPOT arises with one content delta or ≤1 token and is excluded from the percentile | Missing TPOT must remain null/unavailable. It is not a zero-time decode result. This also limits comparisons with vLLM's choices-chunk timing boundaries, described below. |
| All-error rung | Console formatting applies `:.0f` to `ttft_p50_ms=None` before saving the rung | The ladder can crash and lose that rung's evidence. Preserve stderr and previously written rungs. This requires a ladder-owner change; its code was left unchanged. |
| `ptx_gate_ledger_sha256` | Atlas custom PTX gate does not apply to official vLLM images | Null with not-applicable rationale; do not copy Atlas's ledger into a vLLM receipt. |
| Quant vocabulary and verdict | §10 sample lists FP8/NVFP4 and CERTIFIED/NO-GO/PARTIAL | Conditional BF16 and native MXFP4 need explicit schema support. BLOCKED/NOT_RUN is not a measured NO-GO. §10 is a JSON example, not a machine-readable JSON Schema with nullability rules. |

The repaired comparator validates recorded client/header parity and excludes
invalid measured rungs. It does **not** certify the same weights, node,
within-24-hour window, topology or server speculation; those require a separate
provenance validation step. Its JSON/Markdown retains INVALID and NO-PAIR rows
with reasons and exit 0 for a successfully generated report. Only header/schema
mismatches return exit 2. An orchestration script must inspect row verdicts,
not interpret exit 0 as a certified campaign.

The cross-check cannot be called the same workload merely because both CLIs
say `1024/256`: the ladder uses chat plus essay prompts, whereas
`vllm bench serve --backend openai` uses random tokenizer-based completion
prompts and `--ignore-eos`. Even if observed ISL/OSL match, endpoint, prompt
content, EOS behavior and timing boundaries differ. Record both raw results
and describe numerical deltas as an instrument cross-check, not an engine A/B.
No such delta was measured in this blocked run.

No edits were made to the ladder, PRD or VLLM-RECIPES.md. The owner can choose
schema additions and any future ladder changes using these findings.

For the pinned vLLM 0.28.0 source, [`calculate_metrics`](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/benchmarks/serve.py#L589) computes TPOT as `(latency - ttft) / (output_len - 1)`. The [`openai` request function](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/benchmarks/lib/endpoint_request_func.py#L227) counts the first choices-bearing chunk for TTFT even if its text is empty, and ends latency at the last choices-bearing chunk. The ladder times first/last **nonempty content**. Neither formula alone guarantees the two values are equivalent.
