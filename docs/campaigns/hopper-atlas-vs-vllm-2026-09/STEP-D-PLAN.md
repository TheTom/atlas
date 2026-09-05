# Step D rental-day readiness proof

Started 2026-09-05 approximately 12:39 UTC; time box approximately six hours. Code source starts at `b2c17cfe30c33c53d28c4fbec35f6204b8cfb14b`; docs source starts at `0b21f2a5163a739b266fc4d4c5afb61f2fc996e4`. Measurements retain their actual source even if the contribution is rebased before publishing. GB10 observations are rehearsal evidence, never Hopper or B200 performance data.

| Step | Work and oracle | Known-bad first | Stopping rule |
|---|---|---|---|
| D0 | Publish original Step C evidence and truthful A2/B status | Treat absent labelled A2/B outputs as incomplete | Fork PR #3 opened; complete |
| D1 | Build three real release targets; observe JSON architecture/device, early serve refusal, launcher failure and cleanup | Execute genuinely mismatched Hopper/B200 binaries before accepting GB10 control | Four oracles observed, or blocking build failure with full evidence; stop heavy work on foreign GPU tenancy or resource floor |
| D2 | Enumerate PRD cells, capture both dry renderers and compare flags with recipe/PRD | Deliberate missing recipe and invalid spec refusals precede supported renders | Every enumerated cell logged, unsupported/missing coverage explicit; frozen-script defects reported, not patched |
| D3 | Query Hugging Face metadata for all recipe identities and source artifacts | Deliberate nonexistent repository must not produce a usable pin | Every recipe key has a pin or explicit metadata block; no weight downloads |
| D4 | Build Hopper Dockerfile only after D1–D3 complete and disk permits | D1 mismatch demonstrates architecture distinction | Successful build or first blocking failure; remove owned image; aarch64 build proves steps only |

Frozen paths and campaign scripts remain unchanged. Every Spark 2 GPU/disk-heavy step records occupancy, `df -h /` and byte counts; at least 12 GB remains free and task-owned new usage stays below 70 GB. Owned remote build trees and scratch are removed after evidence extraction. Subagents explore D2 and D3 with disjoint evidence ownership while the primary engineer owns D1 and final review. The final new branch is rebased onto the code tip and submitted against it; no shared-branch push.
