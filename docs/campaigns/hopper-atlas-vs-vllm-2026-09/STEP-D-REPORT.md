# Step D rental-day readiness result

**Not rental-ready.** D0 was published and folded by the lead; D2 and D3 are complete audits with findings. D1 produced a real Hopper release binary on GB10 but stopped on a foreign GPU tenant before runtime probing. D4 was skipped because D1 was incomplete. No H100, H200 or B200 was used, and no new inference performance result is claimed.

| Step | Observed result | Evidence |
|---|---|---|
| D0 | [Fork PR #3](https://github.com/TheTom/atlas/pull/3) opened after rebase; lead folded it into docs `783fd19a` and code `c7db4dd4`, then closed it. Step C complete; A2/B not started in available records. | PR description and closing handoff |
| D1 | Hopper Nano release build exit 0 in 208.46 s; 171 PTX modules emitted, 1.15 GB target tree. Runtime oracles A/B/C/D all **unobserved/blocked**, not passed. B200/GB10 builds not started after occupancy stop. | [Architecture report](ARCH-PREFLIGHT-GB10.md) |
| D2 | 1,088 driver cells and 544 direct vLLM renders, 1,632 total commands. Coverage separates 552 scoring candidates, 472 policy probes and 64 conditional alternatives. Full output retained per cell. | [Matrix report](DRYRUN-MATRIX.md), [machine summary](evidence/dryrun-matrix/summary.json) |
| D3 | 10 model keys, 46 recipe profiles, 15 repositories queried through `huggingface_hub`; all returned full SHAs, weight sizes and `gated=false`. Metadata identity inventory passes; launch pin enforcement fails. | [Canonical manifest](vllm-control/WEIGHTS-MANIFEST.md), [machine pins](evidence/model-pins-2026-09-05.json) |
| D4 | Not started: D1 runtime prerequisite failed to become available. No Docker image created. | D1 occupancy stop and cleanup receipts |

The D2 output has 164 render-pass rows, 500 blocked rows, 64 expected speculative refusals, 272 expected unsupported rows and 88 failed expectations. Those 88 comprise 24 masked renderer failures and 64 model-policy refusal gaps. These are readiness verdicts, not engine quality or speed verdicts. PRD topology and spec/think conflicts are recorded explicitly rather than replaced with an invented frozen matrix.

Findings ranked by the task's rental-day impact definition:

| Impact | Finding | Reproduction / status |
|---|---|---|
| P0: paid booking blocked | The adopted Qwen3.8-27B H200 first paid cell has no recipe allocation in either engine. Named smaller bookings also map to larger or unmatched GPU counts. | Matrix D2-F04/F05: exact exit-3 commands, complete outputs, topology table. Recipe allocation/policy decisions left to lead. |
| P0: existing launch gap | Nano's vLLM custom parser file is named without provisioning it into the image. | Matrix D2-F08; already [reported on PR #895](https://github.com/Avarok-Cybersecurity/atlas/pull/895#discussion_r3939764399), no duplicate comment. |
| P1: false dry-render success | Nano spec-on driver returns 0 after nested renderer exit 4. | Matrix D2-F01; known-bad input observed first, exact stdout/stderr/exits preserved. |
| P1: wrong coherency policy | Think-on ladder cells receive a coherency verdict based entirely on think-off requests. | Matrix D2-F02; real local HTTP stub, wrong-answer gate red first, seven recorded request bodies and broken think-on control. |
| P1: unsupported policy accepted | GLM-5.x think-off and Qwen3-Next Instruct think-on render successfully despite PRD restrictions. | Matrix D2-F03; policy errors, not model behavior measurements. |
| P1: model identity unpinned | All 29 vLLM profiles / 36 head-worker commands lack `--revision`; six external-draft profiles also lack independent revisions. | D3 pin probe exits 1; manifest and JSON give exact primary/draft proposals. Proposed pins remain distinct from loaded-byte proof. |
| P1: campaign/recipe conflicts | Kimi B200 renders 1,048,576 context versus scored 49,152; MiniMax M3 B200 names BF16 instead of the PRD NVFP4 choice. Multi-node/manual and speculation limits remain explicit. | Matrix D2-F06/F07. Rendered argv matches JSON; no recipe or flag was improvised. |
| P2 | Launcher CPU suite depends on inherited `RUST_LOG`; README describes an older thinking limitation. | D1 suite red with `warn`, then 30 assertions pass after unsetting it; matrix D2-F09. |

Additional D1 contract risk, source-only: the current check JSON serializes `device_cc` as `"12.1"`, while the task expects `[12,1]`. Early-mismatch JSON emission remains unobserved. This is not presented as a reproduced GPU defect.

Validation observed: D2 rejects corrupted TP, missing Atlas calibration and wrong ISL before accepting 816 complete vLLM render-set comparisons, 144 Atlas recipe/calibration checks, 552 ladder checks and 40 paired draft-depth checks. D3 rejects a nonexistent repository and six corrupted metadata fixtures before verifying all 15 real response hashes and inventories. The existing launcher CPU suite passes 30 assertions in the controlled environment. No recipe JSON was edited, so the conditional recipe-edit suites were not required. Frozen code, campaign scripts, the ladder, schema and benchmark thresholds were not edited.

Spark 2 cleanup is complete. `df -h /`: **62 GiB free initially → 57 GiB immediately before cleanup → 60 GiB afterward** (63,965,319,168 bytes). The task-owned tree was 2,564,610,699 apparent bytes before deletion, below the 70 GB cap; captured disk samples stayed well above the 12 GB floor. All owned remote clone/cache/build/binary/scratch files were removed after 39 build-evidence hashes matched the local copies. No checkpoint, container or image was created, and no other tenant was signalled. [Cleanup receipt](evidence/arch-preflight-gb10/cleanup/stdout.jsonl) also shows the foreign GPU workload still active at 96% utilization.

Code measurements and renders remain tied to `b2c17cfe30c33c53d28c4fbec35f6204b8cfb14b`; docs policy is pinned to `0b21f2a5163a739b266fc4d4c5afb61f2fc996e4`. The contribution is rebased before publication, while preserving these actual observation identities. Outstanding rental-day work is an exclusive GPU window for D1 A/B/C/D, then D4 if eligible, plus lead-owned fixes/policy decisions followed by fresh readiness renders. No automatic GPU retry is scheduled by this report.
