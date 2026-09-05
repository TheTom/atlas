# Rental readiness and Claude plan audit — CPU evidence only

Code published at `05475310694ef0469824813e62282eb0c33d3873`, perf tag `gate-tip-05475310`.
No H100 GPU execution or weight download has occurred. SSH and activation time are pending.

- [Validation](validation/receipt.json): Linux campaign78, local campaign80; renderer/launcher/assembler/validator/PTX checks. Linux optional setproctitle case is separately covered by [real red/green](process-title/SET-PROCESS-TITLE.md).
- [Inventory fix](claude-plan/REPORT.md): expected inventory omitted both Hopper Qwen27B targets. Real red exit101, then932 Rust tests and workspace rustdoc pass. Test-only `crates/` change invalidates the previous perf identity.
- [Claude kit audit](claude-plan/AUDIT.md): offline false-success reproductions for failed occupancy/network/install, deferred downloads and incomplete token agreement. Sources and raw outcomes are retained byte-for-byte. Its absolute local source links identify original files; corresponding copies are under [source](claude-plan/source/). These are simulated failures, not rented-node measurements.
- [Qwen executable receipt](qwen-binary/receipt.json): exact downloaded binary hash and dependencies; executable is retained locally outside Git.

Process mode derives existing recipe argv, pins the local checkpoint path and preserves actual Linux ownership/launch evidence. Audit and serve now use the same declared environment. vLLM immutable build identity is still missing until the actual instance environment is inspected; no certificate is inferred from a Python interpreter hash.

Oracle: negative ownership, environment and inventory cases must fail before the corresponding positive cases are trusted. Stopping rule: required CPU regressions pass, evidence is retained, owned Spark1 worktrees are removed; real-host checks wait for connection details.
