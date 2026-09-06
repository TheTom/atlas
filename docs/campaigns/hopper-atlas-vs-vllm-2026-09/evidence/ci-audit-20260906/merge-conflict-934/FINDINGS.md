# PR #895 integration conflict after #934

Observed September 6, 2026. PR head `201a1368e16dddf6174c4b6be25ee2d0c875dbf1`; upstream main `136520b4f54b4d681718c0a6fc2770e5d07e1513`.

Upstream [#934](https://github.com/Avarok-Cybersecurity/atlas/pull/934) merged at 16:17:19 UTC. GitHub reports `CONFLICTING` / `DIRTY` on [#895](https://github.com/Avarok-Cybersecurity/atlas/pull/895). This is an integration blocker; no new runtime failure has been observed.

## Reproduction and oracle

The oracle is Git's three-way conflict detection on the two pinned commits. A mergeable result exits 0 with no conflict paths. The actual conflicting pair was run first and exits 1. A same-head positive control then exits 0. Both commands and full output are retained in [merge-conflict-evidence.json](merge-conflict-evidence.json). `git merge-tree` writes preview objects only; it does not merge a branch or change the index or working tree.

```sh
git merge-tree --write-tree --name-only 201a1368e16dddf6174c4b6be25ee2d0c875dbf1 136520b4f54b4d681718c0a6fc2770e5d07e1513
```

Observed exit 1 and exactly these five paths:

| File | Resolution required during integration |
| --- | --- |
| `.github/workflows/ci.yml` | The conflicting hunk is explanatory prose. Retain upstream's guard explanation and the executable `ATLAS_SKIP_BUILD: "0"` setting. Preserve the upstream hosted compilation/advisory device split. |
| `crates/atlas-kernels/tests/nvfp4_mmq_capability.rs` | Preserve the campaign's combined Hopper/GB10 test. It covers both dense models, all 13 excluded Hopper exports and their `BLACKWELL_MMA_AVAILABLE` / `W4A16` reasons, while requiring GB10 to retain the exports. Taking upstream's GB10-only version would drop Hopper coverage. |
| `crates/spark-server/src/scheduler/lifecycle_tests.rs` | The difference is a four-line doc comment; both versions already declare `pub(super) struct StubModel;`. Preserve the shared visibility. No runtime implementation differs in this file between the pinned tips. |
| `crates/spark-server/src/scheduler/mod.rs` | Register both `prefill_fifo_tests` from upstream and `prefill_timing_tests` from the campaign, each with its own `#[cfg(test)]`. Selecting one side would silently omit the other suite. |
| `docs/HARDWARE.md` | Preserve the campaign paragraph identifying the Hopper and B200 targets. Upstream's GB10-only wording predates those targets and would misdescribe the integrated tree. |

The scheduler registration must read:

```rust
#[cfg(test)]
mod prefill_fifo_tests;
#[cfg(test)]
mod prefill_timing_tests;
```

## Integration constraint and stopping rule

The lead handoff explicitly requires "rebase-only history, no merges, no force-push" on the published campaign branch. A standard rebase onto the new main would rewrite published commits and require a force-push. No shared history was rewritten, no merge commit was created, and no source or test was removed to hide a conflict. These are reviewed resolution instructions, not a tested integrated tree.

Stopping rule for this audit: capture the real conflict and a positive diagnostic control, identify the exact overlapping behavior and retained tests, then report the integration constraint to the maintainer. Any integrated tree must run the required CPU suites and obtain appropriate performance-tree certification; the rental is destroyed and there is no fresh H100 measurement.

## Other audit results

There are no new review replies or comments since 16:03:47 UTC. Current-head checks remain 36 successful, seven skipped and three previously reported failures: maintainer Seal, certification held pending stamp, and the advisory Metal device runner missing its compiler. Prior green checks do not validate the prospective integration. The code branch remains `201a1368e16dddf6174c4b6be25ee2d0c875dbf1`. The Atlas/vLLM PDF and its measured baseline remain unchanged.


## Publication checks

These checks ran at unchanged code head `201a136`; they validate the existing campaign tooling, not a proposed combined runtime tree. Full commands, exits and output are in [prepush/summary.json](prepush/summary.json) and [ptx-and-cleanup.log](ptx-and-cleanup.log).

| Check | Observed result |
| --- | --- |
| Campaign | 85 assertions passed |
| Launcher | 30 assertions passed |
| PTX gate | 7 assertions passed, including the known-bad two-entry fixture |
| Datacenter Docker recipes | 17 assertions passed |
| Atlas renderer | 346/346 checks passed |
| vLLM renderer | 258/258 checks passed |
| Artifact validator | 26/26 checks passed, seven known-bad fixtures |
| Cell assembler | 16/16 methods passed |
| PR-body sanitizer | Six methods passed |
| Formatting, code-tree typos, workflow parser | Exit 0 |
| PTX shellcheck on the Mac | Exit 0 at warning severity |

The PTX fixture ran on Spark 1's CPU in an owned temporary directory, which was removed. No GPU or warm checkout was touched. Disk before/after: 916G total, 797G used, 73G available, 92%. Spark 1 lacks shellcheck; the same two scripts passed it on the Mac. No crate source changed, so no new crate or GPU test is claimed.

The full docs-tree typo scan exits 2 on retained raw model-card text, hashes and hardware logs; those source artifacts are not rewritten. The new findings prose passes its targeted typo scan. The code-tree typo scan passes.
