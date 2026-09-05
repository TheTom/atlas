# Night log — 2026-09-05

Running status for the overnight split. Atlas side (this branch) is frozen on
`crates/`, `kernels/`, `Cargo.*` from tip `792579b` so the GB10 gate records
being measured on Spark 2 stay valid. Docs and `scripts/` may still move.

| time (UTC) | who | what |
|---|---|---|
| 03:50 | lead | Tip `792579b` pushed to fork; PR #895 body synced; fork PR #1 (Codex control-leg tooling) merged into the campaign branch; typos excludes verbatim evidence; LoC cap satisfied (lib.rs 433, inherited_targets.rs 373 + 164). |
| 03:55 | lead | Handed Codex the overnight plan: Step A GB10 rehearsal (vLLM + Atlas, Nano FP8, Spark 2, 70 GB cap), Step B the 10 REQUIRED perf-gate records at `792579b`, Step C the inferspark static-smem question. |
| 03:58 | lead | S7 in flight: `scripts/start-node-ep.sh` single-node N-GPU launcher + DEPLOYMENT.md section (scripts/docs only). Watch armed: 10-min poller + 2-hourly review pass. |
