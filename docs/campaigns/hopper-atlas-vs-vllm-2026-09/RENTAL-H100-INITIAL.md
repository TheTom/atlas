# Single H100 rental — in progress

Instance 49994640, one NVIDIA H100 80GB HBM3, CC 9.0, driver 610.57.04,
CUDA toolkit 13.0.48. These are H100 observations, not GB10 rehearsal data.
The working deadline is 2026-09-06 02:25 UTC; export begins by 01:40 UTC.
No result is certified yet. Completed evidence is copied to the Mac every minute.

[Raw evidence and file hashes](evidence/rental-h100-20260905/initial-attempts/MANIFEST.json) include the exact launch arguments, environment, GPU snapshots, boot/coherency JSON, build receipts and red/green tooling tests.

## Proven setup

- Both engines use the same 56-file Qwen/Qwen3.6-35B-A3B-FP8 snapshot,
  revision 95a723d08a9490559dae23d0cff1d9466213d989. All 37,493,015,668
  bytes verified against the download manifest. Download took approximately 12m09s.
- Atlas source 2b49ccdbdc86ebb7e6c5bbd976726092cce1deae was compiled on this
  rental with Rust 1.93.1. The active executable SHA256 is
  1082285233577f72e7dbc3ecc4078e8f953aa066a62e6507f6141254549f94fa.
  Build wall time was 8m30s including a deliberate pause; this is not a pure
  compilation-time measurement. Source, compiler and cache remain for fixes.
- Native vLLM 0.28.0 is installed with its pip report and package freeze retained.
  This does not yet satisfy the immutable engine identity requirement.
- The live filesystem is 500 GiB; our working allocation remains limited to 300 GB.

## Completed attempts

| Attempt | Kernel audit | Boot | Coherency | Ladder | Result |
|---|---|---|---|---|---|
| qwen.vllm.a.lat.c1 | N/A | Failed before weight loading: missing Python.h | Not run | Not run | NO-GO boot |
| qwen.atlas.a.lat.c1 | Pass: 173 modules, 321 lookups, zero unresolved | Pass: 37.939 s | Failed word reversal; prime determinism, tool call, think leakage, 391 and Tokyo passed | Not run | NO-GO coherency |
| qwen.vllm.b.lat.c1 | N/A | Pass: 729.251 s | Same word-reversal failure; all other probes passed | Not run | NO-GO coherency |

The Atlas failure stated **rotarefiger**, where **rotaregirfer** is required.
The later explanation listed the reversed letters correctly but reached the
256-token cap before stating the correct combined answer. The original oracle
and output remain unchanged. This is insufficient to attribute a numerical bug;
vLLM stated the same wrong reversal on the same 78-token prompt. Both engines reached the 256-token cap. This shared wrong answer is not an isolated Atlas numerical defect.

## Tooling findings and fixes

- P0: native boot polling continued after the owned API process exited. A real
  Linux child-exit fixture reproduced the delay red first. The fix pins and
  monitors the proved API process and preserves a failed boot JSON promptly.
- P1: Atlas terminated cleanly, but cleanup bookkeeping raced an exiting
  /proc/PID/environ and raised ESRCH. A deterministic Linux procfs reproduction
  went red; the fix treats only ESRCH/ENOENT as disappearance, retaining
  permission and I/O failures. The owned stop recheck confirmed no GPU tenant.
- Environment prerequisite: the vLLM CPU import check did not exercise Triton's
  lazy model-inspection C helper. Matching Python development headers fixed the
  observed missing Python.h compile error; the second boot loaded the checkpoint.

The two fixes are committed locally at 95debe6 and 231d869, with red/green
receipts under tooling-fixes/boot-process-exit. They are published and were deployed between cells at 231d869; the three completed attempts retain harness provenance 2b49ccd.

## Measurement qualifications under investigation

- Atlas reports cached_tokens=48 on a request whose log says no SSM snapshot
  exists and all KV is recomputed. A cache match is not proof of skipped work.
- Atlas's calibration flag is 256, but current code freezes on first observation;
  the readiness request supplied only 13 tokens. This is observed behavior, not
  yet an isolated cause of the spelling failure.
- Recipes currently resolve maximum model length differently: Atlas 65,536;
  vLLM 262,144. The vLLM log reports its default memory utilization 0.92 while
  Atlas recipe explicitly uses 0.90. Preserve these facts when interpreting any
  comparison; no engine tuning has been applied.
- Single-cell C=1 p99 will be based on only three timed requests. Gate latency
  and log token rates are not substitutes for the frozen ladder metrics.

## New tool-template finding

The exact same get_weather request used 1,135 prompt tokens in Atlas and 320
in vLLM; both generated 41 tokens and returned the correct typed call. Atlas
prepends parser-specific tool instructions and also passes tools to the native
checkpoint template. This duplicate prompt expansion is being reproduced in
the production rendering path before a narrow fix. It is distinct from the
shared spelling failure. No scored ladder ran after either failed gate.

## Completed Atlas protocol session

Both plain and tool SSE streams passed structural completion with terminal usage and [DONE]. Plain role/content times: 5.57/77.50 ms. Tool role/first-tool times: 11.90/4964.22 ms; engine-reported internal TTFT:447.64 ms. These are individual diagnostic requests, not a scored throughput comparison. Text-only /tokenize matched all 78 pinned HF IDs. Raw completions returned the shared wrong spelling, and first-token logprobs were null; no complete logprob-equivalence claim is possible. The updated ownership cleanup completed successfully.
