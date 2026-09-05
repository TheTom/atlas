# Schema and instrument gaps

Reviewed against campaign PRD §§4, 9 and 10 and the unchanged
`bench/ladder38/harness_w55_conc_ladder.py` at Git file revision
`60370b9532a7af5319c99d6c2b93972d4f046d56`. Instrument observations below are
distinguished from the linked measurements in the completed GB10 rehearsal.
The **historical attempt** was blocked
by the 40 GB storage cap; see [the report](REPORT.md) and
[storage evidence](gb10-dryrun/storage-preflight.json). Those records remain
evidence of that attempt, not the current authorization or execution status.

The authorized **vLLM then Atlas rehearsal ran on the same GB10 box**, under
a 70 GB limit on new disk usage and a requirement to keep at least
12 GB free throughout. Its separate records are under
[`gb10-dryrun/rehearsal-20260905/`](gb10-dryrun/rehearsal-20260905/RUN-NOTES.md).
vLLM passed coherency and produced eight ladder cells; seven passed the
rehearsal checks and one failed vacuity. Atlas passed boot after a client
endpoint correction but failed tool-call coherency. No Atlas ladder or
Atlas/vLLM A/B ran, and no engine retry was made. Prefix caching remained
enabled on both engines with no reset or developer-mode changes, leaving
cross-process prefix reuse as an explicit confound.

The [assembler](ASSEMBLY.md) now accepts raw ladder, boot and coherency JSON
plus external provenance and emits a GB10 rehearsal artifact per saved rung.
It preserves raw inputs and their file hashes, labels its latency reducer,
and records unknown fields as null with explicit gaps. Runtime observations
come from the linked execution artifacts, separately from synthetic tests. A missing measurement
is null or NOT_RUN, never a fabricated zero, Boolean verdict, CERTIFIED label,
or hash. These instrument limits remain relevant to the current rehearsal.

| Field or claim | What the instrument actually provides | Required treatment |
|---|---|---|
| `engine_version.git_sha` | Ladder has no server Git revision; the Atlas image revision label is `unknown` | Preserve actual package/binary versions and image identity separately. The running Atlas container reports `spark 1.0.0-beta-preview`; that version is not a Git SHA. Unknown Git revisions remain null. See [Atlas version](gb10-dryrun/rehearsal-20260905/atlas-running-binary-version.json) and [image labels](gb10-dryrun/rehearsal-20260905/atlas-image-inspect.json). |
| `engine_version.image_digest` | Ladder records neither image nor digest | Capture Docker RepoDigests and the platform manifest digest before launch. The historical attempt resolved a prospective digest without running it, so that receipt belongs under `planned_image`. Current observed engine identity must come from the executed container, supplied separately to the assembler. |
| `engine_version.binary_sha256` | vLLM is a Python package with multiple native libraries, not one `spark` binary | The schema needs a defined hash target or a nullable/not-applicable representation. Do not substitute the client hash or invent a binary SHA. |
| Harness Git SHA | Not present in §10 or ladder header; `driver_sha256` is the ladder source file SHA256 | The assembler now accepts a `client` provenance block with checkout SHA, file Git revision, file SHA256, Python/aiohttp versions, and exact invocation. Supply observed values; omitted external provenance remains null. Keep these distinct from the engine's Git SHA. |
| `model.revision`, `quant` | Ladder's `model` can be a served alias | Record the pinned HF snapshot revision and model configuration. A manifest proves an API revision exists; it does not prove those bytes were loaded. |
| Checkpoint quant versus runtime precision | Atlas loaded the pinned FP8 snapshot, selected `(sm_121, nemotron-3-nano-30b-a3b, nvfp4)`, and logged compatibility `kernel=nvfp4 model=fp8 OK` | Record checkpoint quant and runtime transformations separately. The [server log](gb10-dryrun/rehearsal-20260905/atlas-server.log) records L1 MoE FP8-to-NVFP4 runtime quantization for 128 experts, native FP8 and some BF16 SSM layers, and retained BF16 attention Q/K/V/O. A common source checkpoint does not establish identical runtime precision. The compatibility message is not a coherency result. |
| KV scale provenance | Atlas warned that the FP8 KV path lacked checkpoint `k_scale`/`v_scale` tensors and defaulted to `1.0` | Retain the [warning](gb10-dryrun/rehearsal-20260905/atlas-server.log), effective KV dtype and calibration state. This observation does not establish the cause of the tool-call failure. No calibration or alternate-KV flags were applied during this rehearsal. |
| `hardware` identity/driver/CUDA | Ladder only saves an unstructured `nvidia-smi` clock/power string | Capture `nvidia-smi -q`, its SHA256, GPU UUID/count and driver on the server. Distinguish the driver's advertised CUDA compatibility from the container's CUDA runtime/toolkit version. |
| `hardware.sm_clock_mhz` | One string sampled **before** each measured batch begins, on the client host | Preserve every string with its context; no under-load clock mean can be inferred. The PRD's statement that this sample is inside the rep is contradicted by the call order. An idle 208 MHz reading cannot be a performance clock. |
| `topology.matched` | Ladder emits neither topology nor evidence from the other engine | Capture server TP/EP/world size and compare both executed legs' provenance. Planning two engines on one box does not itself establish a matched topology. Kimi additionally needs PP and node count, which §10 omits. |
| `serve_command` | Not emitted by ladder | Record argv plus environment, Docker argv/mounts, external parser path/hash, effective server configuration and launch time. A reconstructed command must be marked planned, not executed. |
| `workload.isl` | `make_prompt()` uses `isl - 12` **filler words**, then adds nonce and suffix | This is nominal ISL, not tokenizer-exact input length. The unchanged builder produces 1,056/4,128 whitespace words; actual vLLM ladder usage was **1,209/4,646 prompt tokens** for nominal 1,024/4,096. Preserve both nominal and observed values. See [lat A](gb10-dryrun/rehearsal-20260905/vllm-a-lat.json) and [agent A](gb10-dryrun/rehearsal-20260905/vllm-a-agent.json); pass B records the same input counts. |
| Observed input lengths | Each rep stores total `prompt_tokens` and a sorted **set** of `prompt_tokens_per_req` | Preserve both. Individual multiplicities and request associations are not recoverable. Do not call the workload exactly 1,024/4,096 tokens without usage evidence. |
| Penalties and prompt mode | Request code pins penalties to zero, but JSON omits them; `W55_PROMPT_MODE` changes the suffix without changing the source hash | Capture the environment and inspected source hash. Set `W55_PROMPT_MODE=essay` explicitly. Comparator source-hash equality alone does not establish environment parity. |
| `workload.spec` | No server speculation state, method or draft count in ladder JSON | Record explicit launch configuration/effective state. The comparator cannot enforce spec matching using a bare ladder file. This is still a certification gap. |
| Prefix-cache parity | `_seq = 0` restarts in each new client process | Run A and B can produce identical prompts and reuse prefixes. Within-process nonce uniqueness does not prove cache misses across invocations or shapes. This rehearsal left prefix caching enabled on both engines, with no reset or developer-mode changes. The A/A TTFT shift below is observed; its cause was not isolated. A run-unique nonce or separately approved cache-control methodology remains an owner proposal. |
| `usage.prompt_tokens_details.cached_tokens` | Atlas's second determinism reply reported 32 cached tokens; the server simultaneously logged a 32-token prefix match without an SSM snapshot and recomputation of all KV | A reported prefix match is not proof that the hybrid model skipped prefill work. Preserve both [reply usage](gb10-dryrun/rehearsal-20260905/atlas-coherency.json) and [runtime cache log](gb10-dryrun/rehearsal-20260905/atlas-server.log). vLLM's optional prompt-token-details field was null in these gate replies, which is unknown cache detail, not zero cache reuse. |
| Warmup | One separate warmup batch runs per rung; its entire result is discarded | The first saved `rep: 0` is measured, **not** warmup. Discard the preceding batch as specified, but report that its raw results, errors and vacuity are unavailable. Preserving warmup evidence requires an owner change to the ladder. |
| `boot.pass` | Repaired readiness emits `passed`, `total_s` and ordered `http_exchanges` with request JSON, HTTP status, response body and completeness | The assembler maps `passed` explicitly and preserves the entire gate input. The gate requires health plus a valid nonempty one-token completion within one launch deadline. `first_token_s` is non-streaming one-token response latency including framing, not the ladder's SSE TTFT. Retained HTTP bodies provide audit evidence when the gate reaches its JSON-emission path. |
| Readiness cancelled after terminal container exit | The launcher can observe a terminal container state and cancel its readiness process before that process emits JSON | Preserve the launcher failure artifact, container state and logs. Its health/token timings are null and `http_exchanges` is unavailable because the cancelled gate's health polls existed only in memory. An observed terminal exit supports a launcher failure verdict; it does not supply measured readiness or first-token timing. Do not reconstruct polls from elapsed time or claim that every cancelled gate retained its exchanges. |
| Client endpoint correction and loading-state coverage | Atlas listened on `127.0.0.1:8888`; its original LAN-address readiness process was cancelled and the on-box client corrected to loopback | The [correction receipt](gb10-dryrun/rehearsal-20260905/atlas-endpoint-correction.json) keeps the same engine container, serve flags and original start time. [Atlas boot](gb10-dryrun/rehearsal-20260905/atlas-boot.json) passed with `total_s=216.839` including correction delay, `time_to_ready_s=216.743` and one-token response latency `0.096`. The corrected poll saw 200; no loading 503 was captured and cancelled polls are unavailable. This is not a clean engine startup-duration measurement. vLLM used the same host's LAN address; the comparator intentionally permits differing URLs and cannot certify the network path. |
| `coherency` | Three Boolean checks and explanations plus ordered `http_exchanges`, including both determinism replies when both requests complete; each exchange retains request JSON, HTTP status, response body and completeness | Preserve the complete gate JSON, including partial or failed exchanges. The assembler copies it without dropping the raw replies. Determinism means equal nonempty content, not semantic correctness; the prime prompt is not validated for correct primes. A passing tool check validates the declared argument schema, not the correctness of a weather result. |
| Request parity versus effective prompt parity | Corresponding gate request JSONs match, but tool-prompt usage is 329 tokens for vLLM and 1,230 for Atlas; plain gate prompts are one token longer on Atlas | Preserve both engines' request and usage evidence: [vLLM](gb10-dryrun/rehearsal-20260905/vllm-coherency.json), [Atlas](gb10-dryrun/rehearsal-20260905/atlas-coherency.json). Identical client JSON does not prove identical server-rendered prompts. This is an observed rendering/tokenization difference; its mechanism was not isolated and no template or parser workaround was applied. |
| Backend timing extensions and optional fields | Atlas adds `usage.time_to_first_token_ms` and `usage.response_token/s`; vLLM includes optional null fields such as `reasoning` | Preserve the raw protocol shape and distinguish server-reported values from client timings. Do not substitute these usage extensions for ladder SSE TTFT/TPOT or node throughput. Optional null and absent fields do not independently indicate malformed OpenAI-compatible content. |
| `metrics.ttft_p50_ms`, `ttft_p99_ms`, `tpot_p50_ms`, `e2e_p50_s` | A percentile per measured rep; per-request latency values are discarded | Pooled cell percentiles cannot be reconstructed. The comparator and assembler use the arithmetic mean of per-rep percentiles; the assembler also preserves the full series and names the reducer. These labelled scalars are not pooled percentiles. Preserving request-level latencies or changing the underlying measurement semantics remains a ladder-owner proposal. |
| `metrics.tok_s_series` and `tok_s_mean` | Emitted from measured batches | Retain the raw series and corresponding batch walls/token counts. Mean throughput is an unweighted mean of rep rates, not total tokens divided by total elapsed time. |
| Vacuity | Per-request completion token counts are retained for successful responses | Repaired comparator checks **every** timed request against the 80% floor, rejects missing usage/counts, and retains INVALID rows. Warmup vacuity and failures that crash the client before writing remain unknown. |
| Spread | Raw rate series exists; PRD gate is ≤10% | Repaired comparator calculates spread from raw rep rates and excludes unstable rows. Do not rerun a bad cell into silence. Exact A/A TIE is arithmetic only; no statistical equivalence tolerance is frozen. |
| Empty/failed streaming responses | `n_ok` means no transport/HTTP exception; absent usage may still be `n_ok`. TTFT falls back to full E2E if no visible content. | Treat missing usage/empty output as a finding. A non-null TTFT alone is not proof of a token. Coherency separately rejects empty replies. |
| TPOT availability | Zero TPOT arises with one content delta or ≤1 token and is excluded from the percentile | Missing TPOT must remain null/unavailable. It is not a zero-time decode result. This also limits comparisons with vLLM's choices-chunk timing boundaries, described below. |
| All-error rung | Console formatting applies `:.0f` to `ttft_p50_ms=None` before saving the rung | The ladder can crash and lose that rung's evidence. Preserve stderr and previously written rungs. This requires a ladder-owner change; its code was left unchanged. |
| `ptx_gate_ledger_sha256` | Atlas custom PTX gate does not apply to official vLLM images | Null with not-applicable rationale; do not copy Atlas's ledger into a vLLM receipt. |
| Quant vocabulary and verdict | §10 sample lists FP8/NVFP4 and CERTIFIED/NO-GO/PARTIAL | Conditional BF16 and native MXFP4 need explicit schema support. BLOCKED/NOT_RUN is not a measured NO-GO. §10 is a JSON example, not a machine-readable JSON Schema with nullability rules. |

## Observed gate and A/A findings

[Atlas coherency](gb10-dryrun/rehearsal-20260905/atlas-coherency.json) failed:
the weather request returned malformed markup, `finish_reason="length"`,
256 reported completion tokens and no `tool_calls`. Determinism and think-leak
checks passed, but the two deterministic prime replies repeated the same
degenerate sequence instead of returning exactly five numbers. The gate
reported 256 equal characters and Atlas usage reported 256 completion tokens;
no independent token recount is asserted. This demonstrates the equality
oracle's semantic limitation, not a successful known-answer check. No Atlas
latency cells followed the failed gate; the [lat](gb10-dryrun/rehearsal-20260905/control-atlas-ab-lat.json)
and [agent](gb10-dryrun/rehearsal-20260905/control-atlas-ab-agent.json) commands
remain `PLANNED_NOT_EXECUTED`. There is no Atlas/vLLM performance ratio.

The eight vLLM ladder artifacts represent **passes A and B of vLLM itself**,
two shapes and two concurrencies. Seven have rehearsal verdict PASS. In
[B agent C16](gb10-dryrun/rehearsal-20260905/cells/vllm-b-agent-vllm-agent-c16.json),
one request in measured rep 1 returned 403/512 tokens (78.71%), below the
80% floor, so the cell is FAIL/NO-GO. [A agent C16](gb10-dryrun/rehearsal-20260905/cells/vllm-a-agent-vllm-agent-c16.json)
had a minimum of 426/512 (83.20%) and passed. Both observations remain in the
record; the failed cell was not retried or discarded. PASS here is a GB10
rehearsal gate outcome, not campaign certification.

The comparator uses A as its `atlas` input and B as its `vllm` input for this
A/A exercise; those legacy column names do **not** mean Atlas ran the ladder.
Its arithmetic results are retained rather than relabelled TIE:

| vLLM A/A row | Mean of per-rep TTFT p50, A → B (ms) | Comparator result |
|---|---:|---|
| lat C1 | 247.819 → 242.613 | LOSS; A/B throughput ratio 0.997387 |
| lat C16 | 1750.094 → 1750.569 | LOSS; ratio 0.999207 |
| agent C1 | 850.855 → 181.366 | LOSS; ratio 0.935837 |
| agent C16 | 6137.196 → 841.727 | INVALID; no ratio because B is vacuous |

Sources: [lat A/A](gb10-dryrun/rehearsal-20260905/aa-lat.json) and
[agent A/A](gb10-dryrun/rehearsal-20260905/aa-agent.json). The lat throughput
differences are below 0.3%. The larger agent TTFT change does not prove a
particular cache benefit: repeated process-local nonces and enabled prefix
caching leave reuse uncontrolled, and the experiment did not isolate its
contribution. No statistical equivalence tolerance was defined.

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
The completed [vLLM bench cross-check](gb10-dryrun/rehearsal-20260905/vllm-bench-crosscheck.json)
returned 3/3 successful requests with 1,024 input and 256 output tokens each.
Its TTFT p50 was 281.492972 ms versus ladder A lat C1's mean per-rep p50 of
247.819217 ms; TPOT p50 was 20.318700 versus 20.406593 ms. The
[comparison receipt](gb10-dryrun/rehearsal-20260905/crosscheck-comparison.json)
records the +33.673755 ms and −0.087893 ms deltas and different observed input
lengths (cross-check 1,024; ladder 1,209). Those close TPOT values do not make
the instruments equivalent.

The cross-check reports `max_concurrency=1` and `max_concurrent_requests=2`.
The latter is the maximum count of requests touching a one-second time
bucket, which can count sequential requests within the same bucket. It is
not an instantaneous concurrency trace or evidence that the C1 semaphore
failed. The pinned implementation shows the [bucket calculation](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/benchmarks/serve.py#L693)
and the [request semaphore](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/benchmarks/serve.py#L963).

No edits were made to the ladder, PRD or VLLM-RECIPES.md. The owner can choose
schema additions and any future ladder changes using these findings. In
particular, run-unique nonces, request-level latency retention, recoverable
warmup results and additional provenance emitted directly by the ladder
remain written owner proposals. The assembler preserves and labels the
existing observations; it does not implement those measurement changes.

For the pinned vLLM 0.28.0 source, [`calculate_metrics`](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/benchmarks/serve.py#L589) computes TPOT as `(latency - ttft) / (output_len - 1)`. The [`openai` request function](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/benchmarks/lib/endpoint_request_func.py#L227) counts the first choices-bearing chunk for TTFT even if its text is empty, and ends latency at the last choices-bearing chunk. The ladder times first/last **nonempty content**. Neither formula alone guarantees the two values are equivalent.
