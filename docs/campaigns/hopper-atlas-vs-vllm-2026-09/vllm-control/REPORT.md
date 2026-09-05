# GB10 rehearsal report — vLLM control and Atlas attempt

**GB10 rehearsal data only. This is not Hopper data and must never be quoted as Hopper performance.**

The live rehearsal finished on 2026-09-05 UTC (2026-09-04 Chicago). vLLM passed boot and all three coherency checks, completed both frozen ladders twice, and completed one native benchmark cross-check. **Seven of eight ladder cells passed; B/agent/C16 failed the per-request 80% output-length floor.** The real A/A comparisons did not produce an exact TIE. Atlas booted with the same pinned checkpoint but **failed tool-call coherency**; its four ladder cells and both Atlas/vLLM comparisons were therefore not run. No engine was retried or tuned after a failed gate.

All task-created Spark 2 containers, images, checkpoint files, environments and scratch directories were removed after verified evidence export. Root free space was **82 GiB before and 82 GiB after**. The peak observed increase in root usage was **54.20 GB**, below the revised 70 GB cap; minimum observed free space was **33.11 GB**, above the 12 GB floor.

The initial 40 GB storage stop is preserved in [REPORT-INITIAL.md](REPORT-INITIAL.md). Its plan-only status artifacts predate this authorized follow-on. The current [execution status](gb10-dryrun/rehearsal-20260905/execution-status.json), [run notes](gb10-dryrun/rehearsal-20260905/RUN-NOTES.md), and [cell records](gb10-dryrun/rehearsal-20260905/cells/) describe what actually ran.

## Gate outcomes

| Gate / step | vLLM | Atlas |
|---|---|---|
| Immutable checkpoint verification | PASS: 38 files, 32,703,351,602 bytes | PASS: same files and hashes rechecked before boot |
| Boot within 1800 seconds | PASS: health 369.239 s; one-token response 1.123 s; total 370.362 s | PASS: observed health 216.743 s; one-token response 0.096 s; total 216.839 s, with endpoint caveat below |
| Determinism | PASS: identical answer content | PASS for equality only; identical degenerate prime-number output, not a semantic correctness pass |
| Structured tool call | PASS | **FAIL:** malformed markup, no structured tool calls, `finish_reason=length` |
| Think-tag leak | PASS | PASS |
| Frozen ladder validity | 7 PASS, 1 FAIL / NO-GO | NOT_RUN after coherency failure |
| Real A/A exact TIE | NOT ACHIEVED: 3 LOSS rows and 1 INVALID row | Not applicable |
| Deliberate OSL mismatch refusal | PASS: exit 2, no comparison output written | Not applicable |
| Native cross-check | PASS: 3/3 timed requests, all 256 tokens | Not requested |
| Atlas/vLLM performance pair | NOT_RUN: no valid Atlas ladder input | NOT_RUN after coherency failure |
| Resource guard and cleanup | PASS at every observed sample; owned objects removed | PASS at every observed sample; owned objects removed |

Readiness raw JSON: [vLLM](gb10-dryrun/rehearsal-20260905/vllm-boot.json), [Atlas](gb10-dryrun/rehearsal-20260905/atlas-boot.json). Coherency request/response envelopes: [vLLM](gb10-dryrun/rehearsal-20260905/vllm-coherency.json), [Atlas](gb10-dryrun/rehearsal-20260905/atlas-coherency.json). The Atlas [engine-attempt artifact](gb10-dryrun/rehearsal-20260905/atlas-engine-attempt.json) preserves the failed result with null performance metrics.

Atlas's recipe defaults bound to `127.0.0.1`, whereas the initial readiness client used the LAN address used for vLLM. Only the readiness client was cancelled and redirected to Spark 2 loopback; the same container, server flags and original launch clock were retained. The observed **216.839 seconds includes this correction delay** and is not a cold-boot speed comparison. Atlas's expected loading-503 transition was not observed; the successful probe saw ready-200. The server log's earlier ready milestone is separate evidence, not a replacement for the measured timer. See [endpoint correction](gb10-dryrun/rehearsal-20260905/atlas-endpoint-correction.json) and [server log](gb10-dryrun/rehearsal-20260905/atlas-server.log).

## Measured cells

Every ladder cell used the unchanged client, `W55_PROMPT_MODE=essay`, C=1 or 16, one discarded warmup batch and three timed reps. Sampling was temperature 0, seed 42, penalties 0, thinking off and speculation off. Prefix caching was enabled for both engines. The eight ladder cells contain **24 measured reps / 204 requests** with no transport errors. Coherency verdicts below are the shared pre-ladder gate result, not fresh checks per row.

Ladder TTFT/TPOT columns are **arithmetic means of the three per-rep percentiles**, not percentiles pooled across requests. At C=1 each rep contains one request, so the reported mean p50 and p99 coincide. Ladder tok/s is the mean of three per-rep aggregate rates. The native cross-check uses its own percentiles over three requests and total-output/benchmark-duration throughput. Preserve these distinct reducers when reading the table.

| Engine / pass / shape | Nominal ISL/OSL | C | TTFT p50 ms | TTFT p99 ms | TPOT p50 ms | tok/s | Determinism / tool / think | Cell result |
|---|---:|---:|---:|---:|---:|---:|---|---|
| [vLLM a-lat](gb10-dryrun/rehearsal-20260905/cells/vllm-a-lat-vllm-lat-c1.json) | 1024/256 | 1 | 247.82 | 247.82 | 20.41 | 46.96 | PASS / PASS / PASS | PASS |
| [vLLM a-lat](gb10-dryrun/rehearsal-20260905/cells/vllm-a-lat-vllm-lat-c16.json) | 1024/256 | 16 | 1750.09 | 2941.66 | 69.72 | 208.19 | PASS / PASS / PASS | PASS |
| [vLLM a-agent](gb10-dryrun/rehearsal-20260905/cells/vllm-a-agent-vllm-agent-c1.json) | 4096/512 | 1 | 850.85 | 850.85 | 20.52 | 45.16 | PASS / PASS / PASS | PASS |
| [vLLM a-agent](gb10-dryrun/rehearsal-20260905/cells/vllm-a-agent-vllm-agent-c16.json) | 4096/512 | 16 | 6137.20 | 11064.70 | 76.25 | 177.74 | PASS / PASS / PASS | PASS |
| [vLLM b-lat](gb10-dryrun/rehearsal-20260905/cells/vllm-b-lat-vllm-lat-c1.json) | 1024/256 | 1 | 242.61 | 242.61 | 20.37 | 47.08 | PASS / PASS / PASS | PASS |
| [vLLM b-lat](gb10-dryrun/rehearsal-20260905/cells/vllm-b-lat-vllm-lat-c16.json) | 1024/256 | 16 | 1750.57 | 2944.29 | 69.65 | 208.35 | PASS / PASS / PASS | PASS |
| [vLLM b-agent](gb10-dryrun/rehearsal-20260905/cells/vllm-b-agent-vllm-agent-c1.json) | 4096/512 | 1 | 181.37 | 181.37 | 20.41 | 48.25 | PASS / PASS / PASS | PASS |
| [vLLM b-agent](gb10-dryrun/rehearsal-20260905/cells/vllm-b-agent-vllm-agent-c16.json) | 4096/512 | 16 | 841.73 | 1386.67 | 68.02 | 226.61 | PASS / PASS / PASS | FAIL / NO-GO: vacuity |
| [vLLM bench-crosscheck](gb10-dryrun/rehearsal-20260905/cells/vllm-bench-crosscheck-vllm-lat-c1.json) | 1024/256 | 1 | 281.49 | 305.47 | 20.32 | 46.93 | PASS / PASS / PASS | PASS |
| Atlas lat | 1024/256 | 1 | — | — | — | — | PASS* / FAIL / PASS | NOT_RUN: coherency |
| Atlas lat | 1024/256 | 16 | — | — | — | — | PASS* / FAIL / PASS | NOT_RUN: coherency |
| Atlas agent | 4096/512 | 1 | — | — | — | — | PASS* / FAIL / PASS | NOT_RUN: coherency |
| Atlas agent | 4096/512 | 16 | — | — | — | — | PASS* / FAIL / PASS | NOT_RUN: coherency |

*Atlas determinism passes equality only: both prime replies were identical repeated sequences and ended at the 256-token cap. It did not return exactly five primes. Atlas rows have no performance metrics and no synthetic section 10 cells.

Observed vLLM ladder prompt usage was **1209 tokens for nominal ISL 1024** and **4646 for nominal ISL 4096**. The B/agent/C16 failure contains a **403-token request in rep index 1**, only 78.71% of OSL 512; its displayed throughput is retained raw evidence and is **invalid for performance scoring**. Each measured cell links to its full rate series, raw rung, gate evidence, actual serve argv/environment, image digest, driver, `nvidia-smi -q` SHA and client source SHA. Unknown provenance remains null. Passing rehearsal rows remain `PARTIAL` under campaign certification; no row is certified Hopper data.

Raw ladders: [A lat](gb10-dryrun/rehearsal-20260905/vllm-a-lat.json), [A agent](gb10-dryrun/rehearsal-20260905/vllm-a-agent.json), [B lat](gb10-dryrun/rehearsal-20260905/vllm-b-lat.json), [B agent](gb10-dryrun/rehearsal-20260905/vllm-b-agent.json).

## A/A, refusal and native cross-check

The actual `compare.py` outputs are [lat JSON](gb10-dryrun/rehearsal-20260905/aa-lat.json) / [Markdown](gb10-dryrun/rehearsal-20260905/aa-lat.md) and [agent JSON](gb10-dryrun/rehearsal-20260905/aa-agent.json) / [Markdown](gb10-dryrun/rehearsal-20260905/aa-agent.md). Its legacy `atlas` input/columns hold **vLLM pass A**, and its `vllm` input/columns hold **vLLM pass B** in these A/A files; no Atlas performance was measured. Invocation receipts explicitly record that mapping.

Lat A/B throughput ratios were **0.997387 at C=1** and **0.999207 at C=16**, both `LOSS` under the comparator's exact arithmetic rule. Agent C=1 was **0.935837 / LOSS**; C=16 was `INVALID`, with no scored ratio. These are observed repeatability findings. Exact-identity fixtures still produce `TIE`; the tool has no statistical equivalence band. No tolerance was invented to force the real runs to tie.

The nonce restarts across ladder processes while prefix caching stays on. Agent TTFT fell sharply on pass B (C=1: 850.85 → 181.37 ms). Cache reuse is a plausible confound supported by the execution design, not an isolated causal result. Pass A was fixed as the planned Atlas control before inspecting B. The ladder owner proposals in [SCHEMA-GAPS.md](SCHEMA-GAPS.md) cover unique process nonces, explicit cache-state control, pooled versus per-rep statistics, discarded warmup series and missing provenance; the ladder was not edited.

The [OSL refusal receipt](gb10-dryrun/rehearsal-20260905/osl-mismatch-refusal.json) records a deliberate 256 → 257 header mutation in a separate copy, exit **2**, and no output file. Original ladder files remain unchanged. Atlas/vLLM [lat](gb10-dryrun/rehearsal-20260905/atlas-vs-vllm-lat.status.json) and [agent](gb10-dryrun/rehearsal-20260905/atlas-vs-vllm-agent.status.json) status records say `NOT_RUN`; they do not masquerade as comparator outputs.

The native [raw benchmark](gb10-dryrun/rehearsal-20260905/vllm-bench-crosscheck.json), [exact command](gb10-dryrun/rehearsal-20260905/control-vllm-bench-crosscheck.json), and [comparison note](gb10-dryrun/rehearsal-20260905/crosscheck-comparison.json) record one C=1 cell: three timed requests, one warmup and the tool's preliminary probe, tokenizer-exact 1024-token random prompts, OSL 256, `--ignore-eos`. It completed **3/3** requests. Relative to A/lat/C1, native TTFT p50 was **+33.67 ms**, and TPOT p50 was **−0.0879 ms**. Different prompts, actual input lengths, completion endpoint, EOS policy and first-chunk semantics prevent attributing that delta solely to timing implementation. Raw `max_concurrent_requests=2` is vLLM's one-second activity-bucket statistic, not evidence that its configured C=1 semaphore launched two simultaneous requests; source references and replay limitations are in SCHEMA-GAPS.

## Engine and checkpoint provenance

Both legs ran on Spark 2 (`192.168.50.36`), one NVIDIA GB10, driver **580.173.02**, with driver-advertised CUDA compatibility **13.0**. This is a unified-memory device; unsupported memory query fields were not interpreted as zero. The full launch argv, Docker inspection and environments are captured in [vLLM provenance](gb10-dryrun/rehearsal-20260905/vllm-provenance.json) / [launch](gb10-dryrun/rehearsal-20260905/vllm-launch.json) and [Atlas provenance](gb10-dryrun/rehearsal-20260905/atlas-provenance.json) / [launch](gb10-dryrun/rehearsal-20260905/atlas-launch.json).

| Engine | Observed identity | Pulled digest |
|---|---|---|
| vLLM | 0.28.0; build `2cf0a6915ce544dc493a0990f2ea38d81601128a` | `sha256:f8fe15a8039343336945db10494eaad80ef941fe2b2a5fa6649fa38636051a65` |
| Atlas | `spark 1.0.0-beta-preview`; image Git label unknown, stored as null | `sha256:faa6e5820c42dd86d0ae9e12cbaf2a2e9f32d0f7a9ab348a75ee54d4253929a6` |

vLLM's arm64 platform manifest is `sha256:41b54fb42c66a670a8b27e613ebef05898f24b9ab1bdab28bd00c877bd4935f4`. Atlas's `/usr/local/bin/spark` SHA256 is `df41bf3aea2a1c21c8c98c39979ab4bc84659d37604068297d351153ebdbba31`. Image CUDA environment values are 13.0.2 / 13.0.0 respectively; they are not runtime library probes.

The only downloaded checkpoint was `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8` at **`9bee19446c0dfd01f356e10979d225b2a6621944`**. All 38 repository files were checked against sizes plus LFS SHA256 or Git-blob SHA1, then rechecked before Atlas: [initial verification](gb10-dryrun/rehearsal-20260905/nano-verification.json), [same-checkpoint verification](gb10-dryrun/rehearsal-20260905/nano-verification-before-atlas.json). Both engines used this task-owned offline HF snapshot. Atlas's log confirms its pinned path. The existing user HF cache was not used or altered.

Atlas used the repository's [Nano fixture copy](gb10-dryrun/rehearsal-20260905/atlas-recipe-fixture.yaml) with the user-specified FP8 checkpoint, context 8192, FP8 KV, memory utilization 0.88, SLAI and prefix caching on; speculation remained off. Its log selected the nvfp4 kernel bundle and recorded MoE FP8→NVFP4 requantization while other tensors retained a mixture of FP8/BF16. This is the same checkpoint, not identical runtime arithmetic. The warning about missing FP8 KV scale tensors/default 1.0 is preserved as a finding, without claiming it caused the coherence failure. No calibration or tuning retry was made.

The ladder source SHA256 remains **`1f10d4887b39a86ee946bc2aa0395e31c43ce1b3dfac778f51abbad11832d880`**, file Git revision `60370b9532a7af5319c99d6c2b93972d4f046d56`. The execution checkout source receipt is `1f7bf76a957ef543c14d263995f0f275406cef18`; later commits package evidence and documentation. `nvidia-smi -q` SHA256: vLLM **`9ea61dd57d2f0fa3bc1fe7263365b75e640c3a0d1e0036921941843cee58af64`**; Atlas **`01ddaaeaa8c1460ac91f5cd6109432b5bb4e5b2dcf8bf1c280283ff4b8ed589e`**.

## Storage and cleanup

[Resource summary](gb10-dryrun/rehearsal-20260905/resource-cleanup-summary.json), [before df](gb10-dryrun/rehearsal-20260905/df-before.txt), [after df](gb10-dryrun/rehearsal-20260905/df-after.txt), and [cleanup receipt](gb10-dryrun/rehearsal-20260905/cleanup-remote.json) preserve exact measurements:

| Observation | Used bytes | Available bytes |
|---|---:|---:|
| Before task | 845,513,351,168 | 87,306,461,184 |
| Highest observed task-period usage | 899,711,713,280 | 33,108,099,072 |
| After cleanup | 845,532,073,984 | 87,287,738,368 |

There were **9,114 resource samples**, with 0.5-second guards and soft stops at 65 GB new / 17 GB free, reserving 5 GB against the user limits. No observed sample crossed either limit. These are sampled observations, not a continuous allocation trace. `df -h /` was captured before and after each dependency, checkpoint and image download. vLLM's container and image were removed before the Atlas pull; the checkpoint stayed in place until both legs ended.

The verified [remote export](gb10-dryrun/rehearsal-20260905/remote-export-verification.json) contains **166 files / 1,667,090 bytes**, with a SHA256 manifest in [remote-evidence](gb10-dryrun/rehearsal-20260905/remote-evidence/remote-export-manifest.json). The export includes orchestration, raw logs/results, resource samples and copied client sources; weights and environments were excluded from export and deleted. `/home/pidtom/atlas-vllm-control-20260905` is absent. Docker has zero containers and exactly the three original image IDs. The GPU returned to 0% utilization with the original graphics processes. The final root-used delta is **18,722,816 bytes**; root `df` includes host activity and filesystem/Docker metadata, so that delta is not attributed to a surviving task file. No existing model, image or workload was removed.

## Tooling fixes and validation


Each logical fix has its own commit with a `red:` body line. The initial source changes are confined to campaign gates and synthetic fixtures. Their regression evidence remains preserved.

| Commit | Bug / corrected behavior | Red line and evidence |
|---|---|---|
| `a446bb41` | Require a valid nonempty one-token completion and health within one launch deadline; pin first-request sampling | `red: --selftest accepted HTTP500, error JSON, empty or invalid replies and expired or slow boots as ready, without the sampling pins.` [red](tool-evidence/readiness-red.txt), [green](tool-evidence/readiness-green.txt) |
| `203d5fa7` | Validate completion envelopes and every tool call's declared function name, type and required argument types | `red: --selftest accepted missing or wrongly typed arguments, wrong tool names and types, and extra invalid calls; malformed choices crashed the gate.` [red](tool-evidence/coherency-red.txt), [green](tool-evidence/coherency-green.txt) |
| `e60f3c63` | Preserve exact TIE and unpaired rungs from either file | `red: --selftest labelled identical A/A inputs LOSS and silently dropped vLLM-only rungs.` [red](tool-evidence/compare-01-red.log), [green](tool-evidence/compare-01-green.log) |
| `4e8d97fc` | Exclude errors, vacuity, missing usage/reps, invalid metrics and >10% spread from scoring | `red: --selftest scored errors, vacuity, incomplete reps and invalid metrics, and accepted empty or duplicate rungs.` [red](tool-evidence/compare-02-red.log), [green](tool-evidence/compare-02-green.log) |
| `ae40fe9a` | Require matching valid rep count, warmup count and client source hash | `red: --selftest accepted mismatched or missing reps, warmup and client hash, and equally invalid workload headers.` [red](tool-evidence/compare-03-red.log), [green](tool-evidence/compare-03-green.log) |
| `f1224d41` | Propagate readiness artifact write errors | `red: --selftest returned exit 0 when --out pointed into a nonexistent directory and no boot artifact was written.` [red](tool-evidence/readiness-output-red.txt), [green](tool-evidence/readiness-output-green.txt) |
| `7290eaca` | Emit failed-check JSON for truncated HTTP bodies | `red: --selftest crashed on an HTTP200 body shorter than its declared Content-Length instead of emitting failed coherency checks.` [red](tool-evidence/coherency-truncated-red.txt), [green](tool-evidence/coherency-truncated-green.txt) |
| `9f3ab20b` | Make any stub crash fail the selftest oracle | `red: --selftest accepted a clean-stub crash carrying the diagnostic passed sentinel as a successful clean case.` [red](tool-evidence/coherency-oracle-red.txt), [green](tool-evidence/coherency-oracle-green.txt) |

The oracles are explicit: one process-start deadline and valid completion
content; TOOL_SCHEMA's required JSON types/function; arithmetic identity and
rung union; PRD's per-request 80% floor and 10% spread cap; the actual ladder
header; failed filesystem writes; HTTP Content-Length; and an injected crash
sentinel that cannot count as a clean response. The comparator's detailed
validity and exit-code behavior is in [COMPARE-FINDINGS.md](COMPARE-FINDINGS.md).


The follow-on added raw HTTP exchange capture in **`41f36a41`**, after failing selftests proved the gates discarded request/response evidence: [coherency red](tool-evidence/raw-gates-coherency-red.log), [green](tool-evidence/raw-gates-coherency-green.log), [readiness red](tool-evidence/raw-gates-readiness-red.log), [green](tool-evidence/raw-gates-readiness-green.log). It also added the section 10 assembler in **`386a95f1`**, with explicit nulls, reducer semantics, failed-cell retention and source hashes: [red](tool-evidence/assemble-red.txt), [green](tool-evidence/assemble-green.txt), [assembly contract](ASSEMBLY.md).

Final CPU selftests and source/evidence validation are recorded in [final validation](gb10-dryrun/rehearsal-20260905/final-validation.json). The independent evidence audit checked all nine measured cells and 54 source references; raw metrics, labels, gates and the failed 403-token request matched. No Atlas ladder artifacts were created.

## Recipe-verification verdicts retained from initial work


These are source observations from 2026-09-05 UTC, not GPU validation. Every
exact command, SKU, source URL and date is in [RECIPE-VERIFICATION.md](RECIPE-VERIFICATION.md).
A generated hardware command is distinguished from a recipe's verified-hardware
map. The exact proposed PRD/recipe diffs are included at the end of that file
and pass `git apply --check`; they were not applied.

| Model / question | Verdict | Finding |
|---|---|---|
| Qwen3.6-35B-A3B FP8 | verbatim | Dedicated recipe exists; H100/H200/B200 TP1 commands use XML tool parser. Old missing-recipe claim is stale. |
| Qwen3-Next Instruct FP8 | verbatim; 2×H100 reconstructed | H100 TP8; H200/B200 TP1; Hermes, no reasoning parser; Instruct is non-thinking. |
| GLM speculative dotted syntax | verbatim syntax; GLM-5.3 form reconstructed | Dotted syntax is documented and used by the GLM-5.1 feature. GLM-5.3 renders JSON K5. |
| GLM-5.3 | verbatim command; Hopper validation still unverified | H200 TP8 command exists but H200 is absent from the recipe's verified map; thinking always on. |
| GLM-5.3-Flash | verbatim | Per-SKU commands exist; H200 generated but absent from verified map; thinking always on. |
| GLM-4.5-Air FP8 | still unverified | Dedicated twins return 404. HF card's vLLM command serves BF16 Air TP8; requested FP8 SKU lines remain reconstructed. |
| Kimi K3 | verbatim commands; image/speculation gaps remain | Exact B200 TP8+PP2 command includes a headless worker. JSON `latest` conflicts with guide `kimi-k3`; TP8+PP2 DSpark lacks recipe support. |
| DeepSeek V4-Flash | verbatim; KV alias source-resolved in 0.28.0 | `fp8` is normalized to `fp8_ds_mla` for packed MLA. The old DSpark issue is closed; closure alone is not fresh runtime proof. |
| Nemotron Super | verbatim; parser aliases source-resolved in 0.28.0 | XML/Coder names share a class; built-in reasoning parser exists. FP8 hardware builder now H100/H200 TP8, B200 TP1; H200 TP1 card claim unsupported. |
| Nemotron Nano | H100/H200 verbatim; GB10 reconstructed | Recipe includes tool/reasoning plugin flags. GB10 profile missing; user image pin is an adaptation. |
| Qwen3.8-Flash-Next FP8 | verbatim | Current default H100/H200/B200 TP4, H100 adds PLE offload; prior H200 TEP8 line is not the default. |
| MiniMax M3 | verbatim | H200 BF16 TP8 and B200 NVFP4 commands retrieved. |


## Delivery scope

Only `bench/hopper_ab/` and this `vllm-control/` directory changed. The original ladder, PRD, VLLM-RECIPES and off-limits engine directories/checkouts remain unchanged. No cargo build ran and Spark 1 was not accessed.

The branch remains `campaign/vllm-control-gb10-2026-09` in `/tmp/atlas-vllm-control`; no rebase or merge was performed by this task. [TheTom/atlas#1](https://github.com/TheTom/atlas/pull/1) was observed merged externally at 03:43:36 UTC while this follow-on was running; its [recorded state](gb10-dryrun/rehearsal-20260905/fork-pr-observed-state.json) names merge commit `518f5bd16091123c2344a86684ccfaf37650c261`. Follow-on commits are pushed to the same branch for the lead to fold into the campaign.
