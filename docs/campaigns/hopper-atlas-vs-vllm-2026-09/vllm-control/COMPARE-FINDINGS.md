# Comparator instrument findings

These are CPU-only checks in `/tmp/atlas-vllm-control` on the local Mac, using
hand-written fixtures, not measured GB10/Hopper results. The ladder client was
read as the schema oracle and was not changed.

| Bug observed before the fix | Oracle and corrected behavior | Red / green evidence |
|---|---|---|
| Identical inputs with ratio 1.0 were labelled LOSS; vLLM-only rungs disappeared | Arithmetic identity gives TIE; the union of concurrency values retains NO-PAIR on either side, including its throughput in Markdown | [red](tool-evidence/compare-01-red.log), [green](tool-evidence/compare-01-green.log) |
| Errors, short or missing output, missing reps and invalid metrics could remain scored; empty/duplicate rungs could hide missing coverage | PRD §4/§9: any request below 80% OSL, any error, incomplete reps/counts, missing per-request usage, invalid latency/rate, or raw throughput spread over 10% produces INVALID with reasons and no ratio; empty/duplicate rung identities are refused | [red](tool-evidence/compare-02-red.log), [green](tool-evidence/compare-02-green.log) |
| Rep count, warmup count and client hash were ignored; equally invalid headers were accepted | `harness_w55_conc_ladder.py` header fields and request body: require matching valid `reps`, `warmup`, `driver_sha256` as well as the original shape/sampling/thinking fields | [red](tool-evidence/compare-03-red.log), [green](tool-evidence/compare-03-green.log) |

Run `python3 bench/hopper_ab/compare.py --selftest` from the repository root.
Tests exercise both engine positions, the first passing integer at the 80%
floor (205/256), and one short request hidden among 16 otherwise full replies.
The tiny fixtures now carry synthetic `completion_tokens_per_req` arrays in the
real ladder schema. [CLI evidence](tool-evidence/compare-cli-green.log) also
checks JSON/Markdown TIE output and deliberate OSL refusal with exit 2 and no
new output file. INVALID and NO-PAIR remain visible findings in a successful
report (exit 0); only WIN/TIE/LOSS rows count in `rungs_compared`.

TIE means exact throughput equality. Independent A/A executions can differ
because of timing variation; no equivalence interval is frozen in the PRD, so
this change introduces none. A WIN/LOSS is a throughput ordering, not evidence
of statistical significance, an A/A determinism verdict, or certification.
The report continues to average each rep's latency percentile; it does not
claim that these are percentiles pooled across all requests.

The source hash is the ladder **client** hash. Its emitted record does not
contain server speculation mode/draft count, explicit penalty values, model
revision/weight quantization, image digest, hardware identity or topology.
Hash equality supports running the same client code (whose inspected payload
pins both penalties to 0, a nonce and streaming usage), but cannot verify
server-side speculation or matching weights/box. `model` can be a served alias.
These need the separate campaign provenance artifact and source/serve-command
receipts; the comparator does not infer them from labels or pretend its WIN is
CERTIFIED. Clock samples are strings captured at rep start, not continuous
thermal/clock telemetry. The ladder also retains aggregates rather than raw
per-request latency samples. Carry these limits into SCHEMA-GAPS.md.
