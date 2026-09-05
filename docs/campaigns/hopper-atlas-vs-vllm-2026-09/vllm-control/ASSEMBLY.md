# Assemble GB10 rehearsal artifacts

`bench/hopper_ab/assemble.py` combines one unchanged ladder output, its boot
and coherency gates, and separately captured server/client provenance into
one PRD §10-shaped JSON per saved concurrency rung. It never connects to an
engine, downloads weights, changes the client, or certifies a Hopper result.

From the repository root:

```bash
python3 bench/hopper_ab/assemble.py \
  --ladder /absolute/path/lat-run-a.json \
  --boot /absolute/path/boot.json \
  --coherency /absolute/path/coherency.json \
  --provenance /absolute/path/provenance.json \
  --workload lat --run-id run-a --out-dir /absolute/path/cells
```

Use `--workload agent` for that frozen shape and a distinct run ID for every
engine/client invocation. Output names are
`<run-id>-<engine>-<workload>-c<concurrency>.json`. Existing output files are
refused. All inputs must describe the same endpoint and served model alias;
the boot engine must match external provenance. The assembler validates
nominal ISL, OSL, repetitions, warmup, sampling and allowed concurrencies
against `bench/hopper_ab/workloads.json`, whose SHA256 is recorded.

Exit 0 means every emitted cell passed the **measured rehearsal gates**.
Exit 1 means a failed or incomplete gate; the cell files are still written
and retain the failed observations. Exit 2 means malformed or conflicting
input, an existing output, or an I/O failure. Do not treat any exit code as
campaign certification. Every artifact states `gb10-rehearsal-cell`;
`verdict` is `PARTIAL` for a passing/incomplete single leg and `NO-GO` for an
observed failure. `rehearsal_verdict` separately says PASS, INCOMPLETE or FAIL.

## External provenance

The only required external identity values are `engine` (`atlas` or `vllm`)
and `hardware.hardware_id` (`gb10`). Other missing fields become JSON null
with an explicit `schema_gaps` entry. The following is a **template**, not a
record of an executed server. Replace nulls only with collected evidence:

```json
{
  "engine": "vllm",
  "engine_version": {
    "git_sha": null,
    "image_digest": null,
    "binary_sha256": null
  },
  "model": {"hf_id": null, "revision": null, "quant": null, "served_model_name": null},
  "hardware": {
    "hardware_id": "gb10", "gpu": null, "gpu_count": null,
    "driver": null, "cuda": null, "sm_clock_mhz": null, "nvidia_smi_q_sha256": null
  },
  "topology": {"tp": null, "ep": null, "world_size": null, "matched": null},
  "serve_command": null,
  "environment": null,
  "client": {
    "git_sha": null, "file_git_revision": null, "driver_sha256": null,
    "python_version": null, "aiohttp_version": null, "invocation": null,
    "environment": null, "prefix_cache_control": null, "url": null
  },
  "workload": {"spec": null, "presence_penalty": null, "frequency_penalty": null},
  "ptx_gate_ledger_sha256": null
}
```

`serve_command` and `client.invocation` should contain actual argv arrays.
Top-level `environment` is the recorded server launch environment;
`client.environment` is the recorded client environment, including the
explicit `W55_PROMPT_MODE=essay` setting. `client.prefix_cache_control`
describes the actual cache reset or disabled-cache procedure across A/A
invocations. Include redacted environment values only. `workload.spec`
should preserve the recorded `on`, `k`, method and any depth interpretation;
the assembler does not infer speculation from an image or model name.

If provided, `model.served_model_name`, `client.url` and
`client.driver_sha256` must match ladder/gate values. The served alias,
client URL and driver hash can otherwise be populated directly from the
ladder, since that is observed input. A model manifest revision is not proof
that a server loaded it; supply the revision from the executed launch and
snapshot evidence. Additional fields such as Docker argv, GPU UUIDs,
effective server configuration and package manifests remain in the complete
`raw.provenance` block even when §10 has no corresponding field.

## Preserved measurements and limits

- `raw.rung` preserves every emitted rep, token-count list, wall time,
  finish reason, clock string and error exactly. `raw.ladder_header`,
  `raw.boot`, `raw.coherency` and `raw.provenance` preserve the other inputs.
- `source_artifacts` records actual source paths and file SHA256s, including
  the assembler and frozen workload file. These hashes identify files;
  they do not substitute for missing engine provenance.
- `metrics.latency_percentile_series` retains all per-rep values. The
  headline scalar fields use the arithmetic mean of per-rep percentiles,
  matching the comparator's convention. They are not pooled percentiles.
  An incomplete percentile series has a null scalar and fails validation.
- Throughput mean is recomputed from raw rep rates; inconsistent stored
  summaries fail the latency gate. Missing completion usage, request
  errors, vacuity below 80% of OSL, and spread above 10% remain failed cells.
- `workload.isl` is explicitly nominal. Observed token usage remains in
  each raw rep. Warmup batches were already discarded by the ladder and
  cannot be recovered. The clock string was sampled before each batch on
  the client host; no measured under-load clock is invented.
- The boot mapping preserves `time_to_ready_s`, the non-streaming
  one-token-response `first_token_s`, and `total_s`. Missing timing stays
  unknown; measured total time above 1,800 seconds fails the boot gate.
  Coherency uses the three recorded checks and refuses an inconsistent
  summary Boolean. Missing provenance does not turn a measured gate pass
  into a fabricated failure, and no single-leg result proves A/B parity.

Run the synthetic instrument test with:

```bash
python3 bench/hopper_ab/assemble.py --selftest
```

The test-first red receipt is [assemble-red.txt](tool-evidence/assemble-red.txt).
The passing selftests and CLI exercise are recorded in
[assemble-green.txt](tool-evidence/assemble-green.txt). These use synthetic
fixtures only and are not hardware results. See [SCHEMA-GAPS.md](SCHEMA-GAPS.md)
for the underlying instrument limitations.
