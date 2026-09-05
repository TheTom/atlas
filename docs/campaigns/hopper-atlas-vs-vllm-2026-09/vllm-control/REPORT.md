# vLLM control report

**Status: CPU instrument validation and source research complete; GB10 engine
execution blocked by the 40 GB new-storage cap.** No vLLM server, model load,
real-engine A/A, or vLLM benchmark cross-check ran. Consequently there are no
measured section 10 cell artifacts and no certified performance claims.

Work occurred on 2026-09-05 UTC, still 2026-09-04 in Chicago. The fresh checkout
is `/tmp/atlas-vllm-control`, base `f547486667dc95f65fb0d043402c1131148283c4`,
branch `campaign/vllm-control-gb10-2026-09`. Only `bench/hopper_ab/` and this
`vllm-control/` directory changed. The ladder, PRD, VLLM-RECIPES.md and off-limits
checkouts/engine directories were left unchanged. Spark 1 was not accessed.

## What ran, where, and with which oracle

| Work | Host | Observation / oracle |
|---|---|---|
| Hardware and storage preflight | `pidtom@spark2.local` / `192.168.50.36` | SSH succeeded. `docker ps` empty; NVIDIA GB10 showed 0% utilization and only Xorg/GNOME graphics processes. `df -h /` initially showed 82 GB available. Raw commands, timestamps, outputs and hashes are in [hardware-preflight.json](gb10-dryrun/hardware-preflight.json). |
| Driver inventory | Spark 2 | Driver **580.173.02**, driver-advertised CUDA **13.0**, one NVIDIA GB10. Memory query reports N/A on this unified-memory device; it was not treated as zero usage. [nvidia-smi -q](gb10-dryrun/nvidia-smi-q.txt) SHA256: `ac32b795cf20d7766197dc4e5e95c9f4e46f8c1c955d6028a22c64b77e804983`. |
| Readiness/coherency/comparator selftests | Local Mac CPU, loopback HTTP stubs and synthetic ladder fixtures | Known-bad cases fail before each fix and pass the regression assertions afterwards. [Validation index](tool-evidence/validation.json) records commands, interpreter, source hashes, exits and transcripts. |
| Recipe verification | Local Mac, public HTTPS metadata/docs/source/cards | **29 verbatim command fields** checked; known-bad command substitution rejected. URLs, dates, source hashes and exact proposed owner diffs are in [RECIPE-VERIFICATION.md](RECIPE-VERIFICATION.md). |
| Weight inventory | Local Mac, HF blobs API metadata only | All **12 explicit §3 IDs** resolved; **15 total pinned commands** include concrete NVFP4 variants and §16's 27B. Four bad metadata fixtures rejected, all 15 saved responses audited. [Manifest](WEIGHTS-MANIFEST.md). |

Prospective official image: `vllm/vllm-openai:v0.28.0-ubuntu2404`.
The [Docker tag metadata](gb10-dryrun/docker-tag.json) resolved manifest-list
`sha256:f8fe15a8039343336945db10494eaad80ef941fe2b2a5fa6649fa38636051a65`
and arm64 manifest
`sha256:41b54fb42c66a670a8b27e613ebef05898f24b9ab1bdab28bd00c877bd4935f4`.
These identify a **planned, unpulled image**, not an observed running engine.
Its runtime CUDA version and vLLM version were not measured. The current Nano
recipe has no verified GB10 entry, so this user-specified image is a GB10
campaign adaptation, not a verbatim Nano GB10 recipe.

Nano HF revision: `9bee19446c0dfd01f356e10979d225b2a6621944`.
The unchanged ladder file's Git revision is
`60370b9532a7af5319c99d6c2b93972d4f046d56` and source SHA256 is
`1f10d4887b39a86ee946bc2aa0395e31c43ce1b3dfac778f51abbad11832d880`.
These are client provenance, not vLLM provenance.

## Storage stop and execution status

Observed from API/registry metadata:

- Nano whole-repository payload: **32,703,351,602 bytes**.
- New compressed image blobs, deduplicated and compared with all three existing
  images' uncompressed layer identities: **9,701,486,720 bytes**.
- Combined planning inventory: **42,404,838,322 bytes**, versus the user's
  **40,000,000,000-byte** new-storage cap. Only two tiny layer identities were
  already present. Normal image expansion and compilation/runtime caches need
  additional storage; installed allocation was not measured.

The observation is the byte inventory. The operational inference is that this
combination cannot be provisioned within the current cap using the existing
local storage/cache arrangement. Free space alone does not authorize exceeding
the cap. No weights or image were downloaded, and no new remote workload,
container or scratch directory was created. Nothing remote needed cleanup, and
no existing process/container/model was removed to make space. See
[storage-preflight.json](gb10-dryrun/storage-preflight.json).

[execution-status.json](gb10-dryrun/execution-status.json) and the four stage
status JSONs record **NOT_RUN / BLOCKED_STORAGE_CAP**. They are deliberately
separate from the section 10 measured-cell schema. [planned-cells.json](gb10-dryrun/planned-cells.json)
contains eight requested cells (four shapes/concurrencies × A/A passes), with
null results and explicit plan-only typing.

## Requested cell table

ISL below means the frozen **nominal ladder argument**; actual tokenizer lengths
were not measured. Each row was planned for temperature 0, seed 42, penalties
0, thinking off, speculation off, one discarded warmup batch and three timed
reps, repeated as passes A and B.

| Workload | Nominal ISL / OSL | C | A / B TTFT p50 / p99 ms | A / B TPOT p50 ms | A / B tok/s series | Determinism / tool call / think leak | Status |
|---|---|---:|---|---|---|---|---|
| lat | 1024 / 256 | 1 | — | — | — | NOT_RUN / NOT_RUN / NOT_RUN | BLOCKED_STORAGE_CAP |
| lat | 1024 / 256 | 16 | — | — | — | NOT_RUN / NOT_RUN / NOT_RUN | BLOCKED_STORAGE_CAP |
| agent | 4096 / 512 | 1 | — | — | — | NOT_RUN / NOT_RUN / NOT_RUN | BLOCKED_STORAGE_CAP |
| agent | 4096 / 512 | 16 | — | — | — | NOT_RUN / NOT_RUN / NOT_RUN | BLOCKED_STORAGE_CAP |

There are no live raw series to report. Synthetic fixtures are stored only as
instrument evidence. The comparator's identical-fixture A/A produced ratios
**1.0 and TIE at C=1 and C=16**; the deliberately different OSL fixture was
refused with exit **2** and no output file. The [CLI transcript](tool-evidence/compare-cli-green.log)
contains the command and output. Exact identity does not establish that two
independent hardware runs will tie or define a statistical equivalence band.

The `vllm bench serve --backend openai --random-range-ratio 0.0 --ignore-eos
--percentile-metrics ttft,tpot,itl,e2el` cross-check was **NOT_RUN**. Its TTFT/TPOT
differences from the ladder therefore remain unmeasured. Source review found
that the vLLM OpenAI-completions backend times choices-bearing chunks, whereas
the ladder times nonempty content. Their prompt construction, endpoint and EOS
policy also differ. See [SCHEMA-GAPS.md](SCHEMA-GAPS.md) for the exact formulas
and versioned source links.

## Tooling fixes and red evidence

Each logical fix has its own commit with a `red:` body line. The source changes
are confined to the campaign gates and synthetic fixtures. The final two rows
were found during independent review, including a bug in the expanded selftest
itself; they were corrected before delivery.

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

## Recipe-verification verdicts

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

## Schema gaps and what remains

[SCHEMA-GAPS.md](SCHEMA-GAPS.md) records every missing/ambiguous field without
inventing a value. The most consequential gaps are:

- Nominal ISL is a word-based prompt builder; actual token lengths require
  server usage. Saved latency values are per-rep percentiles, not pooled cell
  percentiles. Raw warmup results and per-request latency series are discarded.
- The nonce restarts across client processes; repeated A/A processes can reuse
  prefixes. An explicit cache reset or consistent disabled-cache adaptation is
  necessary. `W55_PROMPT_MODE` is also absent from the ladder header.
- The bare ladder record cannot verify server speculation, model revision,
  engine image/version, node/topology or the 24-hour pairing window. It omits
  the harness Git SHA and explicit penalties. A source hash is not a vLLM hash.
- Clock/power sampling happens before the rep timer, on the client host. Empty
  output may still count as `n_ok`; missing TPOT is unavailable, not zero. An
  all-error rung can crash on console formatting before saving its JSON; this
  is written up for the ladder owner and left unchanged.
- §10 needs defined nullability and percentile reducers, a vLLM binary-hash
  meaning, non-applicable Atlas PTX handling, BF16/MXFP4 quant vocabulary and
  PP/node topology for Kimi.

The [weights manifest](WEIGHTS-MANIFEST.md) is complete for concrete §3 IDs.
The sole unresolved selection is the nonspecific `nvidia/*-NVFP4` Qwen3.6 P0
expansion, which has no permitted explicit HF ID to pin. API payload sizes are
logical bytes; allocated and peak disk usage remain unmeasured.

To finish the live deliverables, provide a storage arrangement that fits the
model, expanded official image and runtime caches, or explicitly revise the
40 GB cap. Then recheck Spark 2 occupancy, prefetch only Nano at its pinned
revision, verify image digest/parser provenance, and execute boot → coherency
→ both frozen ladders twice → OSL refusal → one vLLM cross-check. Capture the
actual serve argv/environment and raw results, stop on a failed gate, and
remove only the task-created model/container afterward. Resolve the recorded
schema and cache-state limits before calling any resulting row certified.
No hardware rental, future monitor or deferred GPU workload was started.
