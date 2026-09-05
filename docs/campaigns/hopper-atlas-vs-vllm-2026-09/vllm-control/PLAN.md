# vLLM control execution plan

Base: `f547486667dc95f65fb0d043402c1131148283c4` from fork branch `hopper/sm90-target-tdd-2026-09`. Work branch: `campaign/vllm-control-gb10-2026-09`. Read AGENTS.md, CONTRIBUTING.md, the campaign PRD and VLLM-RECIPES.md before execution.

1. Inspect Spark 2 GPU processes, running containers, memory, disk, cached image layers and Nano cache. Preserve all existing workloads and files. Stay below 40,000,000,000 bytes of new disk use. Spark 1 is excluded from GPU work.
2. Run the existing CPU selftests. For each discovered gate bug, extend the actual --selftest first, capture the failing result, then implement and verify the smallest logical fix. Keep ladder measurement semantics unchanged.
3. If the resource preflight allows it, prefetch only the pinned Nano checkpoint and official image, record launch command, immutable digests and driver evidence, then run readiness and coherency in order. Stop on failed boot/coherency gates.
4. If gates pass, run the frozen lat/agent shapes with C=1,16, 1 discarded warmup and 3 measured reps twice; preserve raw JSON, validate A/A and reject an OSL mutation. Cross-check one cell using vLLM bench serve and document prompt/endpoint differences.
5. Assemble per-cell PRD section 10 artifacts from observed evidence. Missing or inapplicable fields are explicit gaps; never invent latency, a provenance SHA, a successful gate or an unexecuted cell. Record blocked steps in machine-readable status artifacts.
6. Independently verify published model/SKU commands and build an HF API revision/size manifest using metadata only. Propose exact changes to owner documents without editing them.
7. Review diffs and relevant selftests, commit logical changes with red evidence in bug-fix commit bodies, push to the fork and open a draft PR targeting the fork campaign branch. Remove only this task’s remote model/container/storage when finished.

Oracles: campaign gates and frozen workloads; ladder source/parity pins and raw request token counts; known-bad HTTP/JSON/SSE fixtures; current recipe JSON and official model cards; Hugging Face blobs API file sizes/revisions; Docker registry layer metadata and host hardware observations.
