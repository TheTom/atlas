# Rental preparation fixes — 2026-09-05

Four tooling changes are published on PR #895 at
`2b49ccdbdc86ebb7e6c5bbd976726092cce1deae`. These are CPU orchestration and
protocol observations, **not H100, B200 or GB10 inference results**. The selected
booking remains two H100 SXM GPUs, 300 GB instance disk, no volume, and eight
hours including setup and export. No rental connection or model download has
occurred; SSH endpoint, instance ID and activation time are still pending.

The changes touch `bench/campaign/` only. Perf-path trees, recipes, artifact
schema and the frozen ladder are unchanged from `05475310`;
`gate-tip-05475310` remains the perf-tree reference. No new GPU certification is
claimed. Source commits and complete validation receipts are in the
[evidence directory](evidence/rental-prep-fixes-20260905/commits.json).

## Findings and observed oracles

| Impact | Change | Known-bad observation | Green oracle and stopping rule | Evidence |
|---|---|---|---|---|
| P0: unwanted GPU work after failed admission | `fa37657` prevents all serve dispatch after preflight failure. | Each of four runner paths invoked an audit/engine/container after fake `nvidia-smi` exit 13. | Zero launch commands, runner exit 1, valid `NO-GO/preflight`; successful admission still reaches its selected path. All four negative and four positive subcases pass on Linux. | [Red calls](evidence/rental-prep-fixes-20260905/admission/red.stdout.txt), [red assertions](evidence/rental-prep-fixes-20260905/admission/red.stderr.txt), [initial green](evidence/rental-prep-fixes-20260905/admission/green.stdout.txt), [final integrated Linux output](evidence/rental-prep-fixes-20260905/validation/campaign-linux.log). |
| P1: attributing another process's endpoint to this engine | `98b9dce` checks a free port before process launch, then proves listener and accepted-socket ownership after readiness and before the ladder. | The actual runner entered its fake kernel audit while a foreign listener occupied the port. The new helper's absent implementation also produced expected red tests. | Occupied or unproved endpoints refuse; real owned IPv4/IPv6 listeners and accepted connections pass. Foreign processes survive. 13 endpoint tests and 2 existing runner tests pass on Linux. | [Red](evidence/rental-prep-fixes-20260905/endpoint/red.log), [green and actual runner proof](evidence/rental-prep-fixes-20260905/endpoint/endpoint-green.log), [combined green](evidence/rental-prep-fixes-20260905/endpoint/combined-green.log). |
| P1: incomplete streams or inconsistent first-event timing hide protocol differences | `f005d7f` adds an independent streaming diagnostic. | Missing implementation failed first; a forced-success mutation then failed all ten malformed-stream subcases. A trickling-header server exceeded the initial socket-only timeout. | Exact request/raw chunks retained, split UTF-8/SSE handled, role/reasoning/content/tool arrival times distinct; incomplete, empty, malformed or late streams refuse. Seven tests pass, including total network deadline. | [Mutation red](evidence/rental-prep-fixes-20260905/stream/red-forced-success.log), [header deadline red](evidence/rental-prep-fixes-20260905/stream/red-deadline.log), [green](evidence/rental-prep-fixes-20260905/stream/green.log). |
| P0: a trickling response consumes the rental window | `2b49ccd` adds optional whole-cell deadline and preserves cleanup when expiry interrupts finalization. | Original coherency HTTP timeout 0.12 s accepted a body after 0.5447 s. Early watchdog cancellation killed a valid but unrelated PID from a forged receipt; early finalization skipped cleanup when deadline arrived during cleanup, including operator-triggered cleanup. | Deadline records expiry before TERM to the exact runner; cancellation proves actual watchdog identity/command/parent. Normal and interrupted cleanup, trickling input, hard-grace refusal and both cleanup races pass. Twelve Linux tests pass. | [Original timeout red](evidence/rental-prep-fixes-20260905/deadline/original-trickle-red.json), [operator-cleanup red](evidence/rental-prep-fixes-20260905/deadline/operator-cleanup-red.json), [green](evidence/rental-prep-fixes-20260905/deadline/green.json). |

The original admission green receipt predates the final endpoint integration:
its two test methods became three, with the successful process-mode case
requiring Linux `/proc`. Final integrated Linux output is authoritative for all
eight subcases. The existing failed-kernel-audit launch refusal remains covered.
The preflight review thread was answered with the fix and reproduction:
[review reply](https://github.com/Avarok-Cybersecurity/atlas/pull/895#discussion_r3941713084).

## Rental invocation and limits

Add `--cell-timeout-s 2700` to each live rental cell: 45 minutes after arming,
plus 60 seconds for the existing cleanup path. The option is explicit, Linux
only, accepts 1–28800 seconds, and remains omitted by default. It bounds audit,
boot, coherency, ladder and normal finalization. Dry-run prints the budget.

The watchdog uses pidfds and signals its recorded runner, not an inferred
engine group. If cleanup exceeds its grace, `cell-deadline.json` records
`cleanup_unconfirmed`; the artifact and engine cleanup may be incomplete.
Inspect retained owner records and provider state. A final file-only amendment
that records a cancellation failure or expiry racing cancellation occurs after
the watchdog is canceled. No engine work launches there. This runner deadline
does **not** stop provider billing: keep the eight-hour provider deadline and
final export reserve.

Process endpoint proof requires readable current-network-namespace TCP tables
and owned `/proc/PID/fd` links. It verifies all matching listeners and the
process accepting a fresh TCP connection. It is a point-in-time observation,
not a port reservation or proof of every future HTTP request. The second proof
replaces the earlier endpoint JSON; retained JSON describes the latest check.

For a separate owned diagnostic boot, prepare a chat JSON request with
`stream: true` and `stream_options.include_usage: true`, then run:

```bash
python3 bench/campaign/stream_probe.py \
  --url http://127.0.0.1:8000/v1/chat/completions \
  --request-json request.json --out out/stream-diagnostic --timeout-s 30
```

The output directory must be new. Exit 0 requires structurally complete SSE,
supported finish reason, positive prompt/completion usage, generated payload
and `[DONE]`; tool calls require complete identity and JSON object arguments.
It retains `request.json`, raw base64 chunks with monotonic timestamps and
`report.json`. Exit 1 records a failed response. Exit 2 reports an invocation, setup or output failure; partial files may remain after an I/O error.
The 30-second total network deadline includes trickling headers/body. This is
not semantic correctness, tokenizer truth or certification of scored requests.
Do not run auxiliary requests during measured ladders. The current cell runner
tears down after each cell, so a diagnostic needs a separate owned boot.

## Final validation

| Check | Observed result |
|---|---|
| Full campaign | 84 assertions macOS; 82 Linux. Remote shellcheck/typos unavailable; both pass locally. |
| Launcher | 30 assertions. |
| PTX CPU suite with real nvcc/ptxas | 7 assertions, including rejection of both invalid entries. No GPU execution. |
| Dockerfiles | 17 assertions. |
| Atlas/vLLM renderer selftests | 329/329 and 253/253. |
| Artifact validator/assembler | 26/26 and 16/16. |
| Formatting/lints | `cargo fmt --all -- --check`, shellcheck, typos, Python compilation and `git diff --check` pass. |

[Full logs](evidence/rental-prep-fixes-20260905/validation/final-suites.json)
retain exact commands in adjacent receipts. The initial Linux staging attempt
failed because `bench/agentic/coherence_check.py` was missing from the test copy;
its [output](evidence/rental-prep-fixes-20260905/validation/initial-staging-missing-file.log)
is retained. After staging complete inputs, the full suite passed. All 1,611
transferred source files match the recorded SHA256 manifest. The temporary
fixture Git commit is **not** the campaign commit; its local Git repository
exists only for runner identity fixtures. No GPU result uses that identity.

Only the owned Spark 1 CPU test directory was removed: 35 MB before cleanup.
Observed `df` free space was 7.2 GB before and 7.1 GB after; concurrent host
activity prevents attributing that difference to this task. The directory is
confirmed absent; the production GPU and shared checkout were untouched.
[Source verification](evidence/rental-prep-fixes-20260905/validation/linux-source-verification.json),
[cleanup receipt](evidence/rental-prep-fixes-20260905/validation/linux-cleanup.json).

## Remaining rental proof

Native vLLM immutable build identity stays null until supported by actual
environment evidence. A Python hash or an outer image digest after package
changes is not that proof; schema validity does not mean `CERTIFIED`.
Checkpoint verification, H100 driver/kernel execution, first boot/coherency,
NCCL/P2P, telemetry, actual result export and provider shutdown remain unobserved.

Frozen-ladder nonce restart, actual-versus-nominal token counts, discarded
warmups, incomplete-stream acceptance and percentile methodology remain a
written proposal for its owner. Do not silently reinterpret WIN/TIE as proof of
equal work. The stream diagnostic does not repair those scoring limitations.
Kimi K3 remains a separate larger-allocation/support priority; its pinned
1.56 TB native checkpoint cannot fit this 300 GB disk/two-H100 rental.
