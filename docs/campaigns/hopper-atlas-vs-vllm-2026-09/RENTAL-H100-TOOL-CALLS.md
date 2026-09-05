# H100 tool-call audit — September 5, 2026

These are single-H100 diagnostic observations from Vast instance 49994640,
not GB10 rehearsal or certified campaign scores. Both original Qwen3.6
coherency gates failed the same word reversal, so no scored ladder ran.
[Raw exchanges, builds, red/green tests and file hashes](evidence/rental-h100-20260905/tool-call-audit/MANIFEST.json)
are retained. All listed diagnostic servers stopped with no GPU tenant left.

## What changed

Published code `f66a262048ac0a6aee4c67444fd0ea5740b46b30`, tag
`gate-tip-f66a262`, contains these changes on PR #895:

- `d1322aa`: supported native Qwen templates render tools once. The production
  CPU regression observed two tool instruction blocks and 1,135 prompt tokens
  before the fix. Explicit required/named choice remains present; custom
  templates, fallback paths and other parsers retain their behavior.
- `5578439`: scheduler service TTFT starts before grammar preparation in both
  prefill paths. This fixes missing time; it does not make grammar compilation
  faster. The clock still excludes HTTP and queue time.
- `3c866ce`: register the chat regression under the server binary, preserving
  the thin library's compilation boundary.
- `f66a262`: the owned process launcher allows and records the existing
  `ATLAS_DECODE_TIMING=1` diagnostic. Unknown environment keys still refuse.
- `3de7d20`, `57d9c1c`: add the pinned Qwen3.8-27B H100 pair and update the
  expected pinned-command inventory from 37 to 38. Spec-on still refuses.

The new tag invalidates older perf records over the changed crate tree. No
new perf certification at this tag is claimed. Exact binary source and hashes
are recorded per session; the first live fix checks used 5578439, while the
subsequent timing session used a fresh f66a262 build (39.01 seconds).

## Observed tool behavior

Oracle: exactly one `get_weather` call, arguments decoding to
`{"city":"Reykjavik","days":3}`, `finish_reason=tool_calls`, and complete
stream usage/terminal structure. Auto, required and named choice, each in
streaming and blocking mode, repeated twice: **12/12 pass** after the fix.
A later timing session also passed all four typed tool calls and its plain
text stream. The post-fix full coherency check still fails only word reversal.

| Diagnostic | Prompt tokens | First tool data | Whole response | Qualification |
|---|---:|---:|---:|---|
| Atlas original cold | 1,135 | 4.964 s | 5.660 s | Duplicate native/parser instructions |
| vLLM original | 320 | 0.164 s | 0.292 s | Same wire request, one observation |
| Atlas fixed cold, 5578439 | 298 | 4.935 s | 5.613 s | Grammar remains cold |
| Atlas fixed repeat, 5578439 | 298 | 0.115 s | 0.801 s | Compiled grammar cache warm |
| Atlas diagnostic cold, f66a262 | 298 | 4.824 s | 5.506 s | Decode timing enabled |
| Atlas diagnostic first repeat, f66a262 | 298 | 0.111 s | 0.798 s | Decode timing enabled |

Atlas's existing compact JSON formatting accounts for the remaining 298
versus 320 token difference; this is not byte-identical prompt rendering.
Every row emitted 41 completion tokens. These are individual diagnostics,
not pooled percentiles or frozen throughput measurements. Role-event time,
first tool-data time and engine service TTFT remain distinct.

## Remaining findings

**P1: tool decoding spends most of its recurring time on the host.** On the
fresh f66a262 binary, the existing trace reports:

```text
DECODE_TIMING (last 100 host-path tokens): copy+fwd-wait=4.11ms/tok sample(248k host)=13.78ms/tok
```

The copy measurement includes GPU forward wait; it is not a pure transfer
benchmark. The sample measurement includes CPU grammar masking, expansion,
penalties and selection. Tool calls force this host path; ordinary neutral
greedy text can use GPU argmax. Warm grammar-mask work is being isolated on
CPU before an optimization is chosen. Ties must retain existing last-wins
sampling behavior. No mask/threshold or grammar constraint is disabled.

**P1: cold grammar preparation remains about 4.5–4.8 seconds.** The compiler
prewarms up to 512 ranked token masks serially. A bounded parallel same-work
implementation is being tested independently; no performance win is claimed.
The TTFT fix now exposes that time (4,890 ms on the first corrected call),
where the old value omitted it (448 ms on the original call).

**P1: cached token counts do not establish saved computation.** Later repeats
report a full prefix match yet logs describe absent SSM snapshots/recompute.
In the timing session, repeats two/three returned first tool data at about
0.347/0.349 seconds despite cached_tokens=298. Preserve the raw usage and logs.

## Validation and stopping rule

Observed negatives cover duplicate prompt injection, grammar excluded from
service time, missing H100 recipes, the thin-library registration failure and
rejected diagnostic environment. Corrected default-feature spark-server tests:
**2,454 passed, 0 failed, 18 ignored**, no filters. Rustdoc passes on the same
crate tree, verified against 1,982 files. Campaign85, Atlas346, vLLM258,
launcher30, Docker17, PTX7, validator26, assembler16 and formatting/lints pass.
The process environment suite passes13 tests with one optional skip.

The tool-call correctness check is complete. Bound further performance work
to demonstrated bottlenecks and correctness-preserving experiments, then
advance to the staged Qwen3.8 pair. Do not weaken coherency to create a score.

## Next model and independent Iron work

Qwen/Qwen3.8-27B-FP8 revision
`017b9c7af6b5689d5dd426a76e0bc077eb5ca20a` finished staging at
21:23:28 UTC: 81 files, 30,890,049,597 bytes verified. Remote and Mac proof
SHA256 match `6074590b1089e054afc8a4c2a23ca5e8a4184e4ff2c8ccb7898fa722cf812479`.
A distinct Hopper qwen3.8-27b binary is required. No Qwen3.8 boot/coherency
pass is claimed by this report.

In an exclusive side-agent GPU window, Iron PR299 passed six CUDA runtime
smokes and 16 numerical GEMM cases. Its four standalone 4096-cubed GEMM
ABBA cells showed only about 0.1–1.4% between inline MMA and WMMA. These
are kernel measurements, not a Butter/Atlas/vLLM serving comparison. Two
attention tests completed before a bounded CPU-reference timeout; the full
attention suite is incomplete. Butter's separate Q4 checkpoint/build work
continues in its own cache and is not the FP8 control dataset.
