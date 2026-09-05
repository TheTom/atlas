# Step D3 metadata evidence

The report is the canonical [WEIGHTS-MANIFEST.md](../../vllm-control/WEIGHTS-MANIFEST.md).
The output is [model-pins-2026-09-05.json](../model-pins-2026-09-05.json), an array
with one object per recipe model key. This is network-only preparation for the
Hopper/B200 campaign; no GPU was used and no model files were downloaded.

## Oracles, observed results and stopping rule

1. A known nonexistent repository must fail before a successful lookup is
   trusted. The first request, captured under
   [known-bad-nonexistent-repo](known-bad-nonexistent-repo/request.json), returned
   HTTP 401 / `RepositoryNotFoundError`, exit 2. This API intentionally obscures
   missing/private repositories; the negative oracle is rejection, not HTTP 404.
2. A recorded SHA and byte sum must agree with the exact captured response.
   Six bad metadata fixtures went red first, then the positive fixture passed;
   [output](selftest.stdout.txt). All 15 real responses then passed SHA256,
   repository/revision identity, file uniqueness, payload-size and LFS-size
   checks; [output](assemble.stdout.txt). The inventories contain safetensors
   weights only; indexes and tokenizer files are separately classified.
3. Every recipe model and external draft must map to an observed artifact.
   The completed inventory has 10 model keys, 46 profiles and 15 repositories.
   `source.json` records the frozen recipe commit and SHA256 of both JSON files.
4. Recipe launch identity requires a revision in every serving command and a
   separate revision for external drafts. The evidence probe intentionally
   exits 1: 36 primary commands in 29 profiles and six draft-profile references
   are unpinned; [full stderr](revision-audit.stderr.txt). That remains a finding,
   not a passing launch gate. Exact proposed primary and draft flags are in the
   manifest and machine inventory.

Stopping rule: finish when every artifact in the two recipe files has metadata
or an explicit unknown after the one-hour time box. All 15 succeeded. There was
no need for authentication, retries, a virtual environment or cache downloads.
Existing Python 3.14.6 / huggingface_hub 1.8.0 / httpx 0.28.1 were used.

## Reproduction

From the repository root, the offline checks are:

```bash
python3 docs/campaigns/hopper-atlas-vs-vllm-2026-09/evidence/model-pins/assemble_pins.py --selftest
python3 docs/campaigns/hopper-atlas-vs-vllm-2026-09/evidence/model-pins/assemble_pins.py
python3 docs/campaigns/hopper-atlas-vs-vllm-2026-09/evidence/model-pins/check_recipe_pins.py bench/campaign/vllm_recipes.json
```

The first two commands exit 0. The third exits 1 at the recorded code tip; its
purpose is to expose the missing pins, not to certify model loading. Each
repository directory has its exact metadata fetch command, exit code, stdout,
stderr, raw API response and timestamped request receipt. Re-fetch into a fresh
output directory to preserve these historical observations. The collector only
calls `HfApi.model_info(files_metadata=True, token=False)`; it never calls
`snapshot_download`, `hf_hub_download` or a model loader.

The raw JSON responses are the source for revisions, sizes, gating and license
metadata. The source receipt for the proposed speculative `revision` key comes
from official vLLM code at its separately recorded SHA. It does not identify the
version inside any rental image. Metadata pins remain candidates until a run
proves the selected snapshot was actually loaded.
