# Hopper A/B — Atlas vs vLLM — RESULTS

**Status: TEMPLATE. Every table below is empty and every number in it is a
placeholder.** Nothing here has been measured. Fill a cell only from a
committed artefact; a cell filled from memory or from a terminal scrollback is
worth less than an empty one, because an empty cell reads as unmeasured and a
wrong one reads as measured.

- Campaign PRD: `docs/campaigns/hopper-atlas-vs-vllm-2026-09/` (this directory)
- Driver: `bench/hopper_ab/` — `time_to_ready.sh`, `coherency_gate.py`, `compare.py`
- Frozen shapes: `bench/hopper_ab/workloads.json` (the SSOT; a leg that does
  not match it is not in this campaign)
- Ladder client: `bench/ladder38/harness_w55_conc_ladder.py`

## How to fill this in

One row per **cell**, where a cell is the full tuple:

> (engine, model, SKU, topology, workload, C, speculation)

Two rows that differ in any one of those seven are different measurements. The
GB10 campaign lost a whole reference by comparing across the speculation axis —
vLLM with MTP is 1.8–1.9x vLLM without it at low concurrency — so speculation is
part of the cell identity, not a footnote.

Rules that make a row trustworthy, all of them learnt the expensive way:

1. **Both legs on the same node, sequentially.** A second engine resident on
   the GPUs is a third variable.
2. **Speculation is both-or-neither**, never one engine's on against the
   other's off.
3. **Paste the serve command verbatim**, including the flags you think are
   defaults. The recipe id alone overstates provenance the moment anything was
   overridden.
4. **Paste the image digest**, not the tag. `vllm/vllm-openai:latest` names a
   different image next week and the row becomes unreproducible.
5. **Paste the `nvidia-smi` fingerprint**, including the device count. Two runs
   of the same flags on a 2-GPU and an 8-GPU node are different measurements
   and nothing else in the row distinguishes them.
6. **A failed coherency gate voids the row.** Strike it through; do not report
   its throughput.

## Fingerprints

Fill once per box, then reference by name from the tables.

| Box | `nvidia-smi --query-gpu=name` | GPUs (`nvidia-smi -L`) | Driver | CUDA | Host / kernel | Notes |
|---|---|---:|---|---|---|---|
| _hopper-a_ | | | | | | |
| _hopper-b_ | | | | | | |

## Engine builds

| Engine | Version / commit | Image digest | Notes |
|---|---|---|---|
| Atlas | | (built from source; record the commit and the `kernels/` target) | |
| vLLM | | `sha256:` | official recipe image, unmodified |

## Boot and coherency gates

Per (engine, model, SKU, topology). These are PASS/FAIL, not scores — a leg
that fails any of them has no comparable numbers however fast it was.

| Engine | Model | SKU | Topology | Boot (s) | Boot ≤ 1800 s | Determinism | Tool-call JSON | No `<think>` leak | Artefact |
|---|---|---|---|---:|---|---|---|---|---|
| Atlas | | | tp= ep= world= | | | | | | `time_to_ready.json` / `coherency.json` |
| vLLM | | | tp= | | | | | | |

Boot is measured by `bench/hopper_ab/time_to_ready.sh` with `--start-epoch` set
from before the serve process launched. Record `first_token_s` beside it: an
engine that answers `/health` before its graphs are captured is ready by the
health check and not by the clock.

## Throughput and latency

One table per workload. `tok/s/user` is per-stream decode rate; `node tok/s` is
the aggregate the box delivered. Both are reported because they answer
different questions and diverge exactly where a scheduler is doing something
interesting.

### Workload `lat` — ISL 1024 / OSL 256

| Engine | Model | SKU | Topology | C | Spec | TTFT p50 (ms) | TTFT p99 (ms) | TPOT p50 (ms) | tok/s/user | node tok/s | Ratio | Verdict | Artefact |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| Atlas | | | | 1 | on/off | | | | | | | | |
| vLLM | | | | 1 | on/off | | | | | — | | | |
| Atlas | | | | 16 | on/off | | | | | | | | |
| vLLM | | | | 16 | on/off | | | | | — | | | |

### Workload `agent` — ISL 4096 / OSL 512

| Engine | Model | SKU | Topology | C | Spec | TTFT p50 (ms) | TTFT p99 (ms) | TPOT p50 (ms) | tok/s/user | node tok/s | Ratio | Verdict | Artefact |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| Atlas | | | | 1 | on/off | | | | | | | | |
| vLLM | | | | 1 | on/off | | | | | — | | | |
| Atlas | | | | 16 | on/off | | | | | | | | |
| vLLM | | | | 16 | on/off | | | | | — | | | |

### Optional full ladder — C = 1, 2, 4, 8, 16, 32, 64, 128

Emitted by `compare.py`; paste its markdown output under a heading naming the
workload and the topology. The full sweep is what makes a crossover readable —
vLLM's C=128 falling below its own C=64 on GB10 was only visible from the whole
ladder, never from two points.

## Serve commands, verbatim

One block per (engine, model, SKU, topology). Copy from the shell, do not
retype.

```text
# Atlas — <model> on <SKU> <topology>
spark serve ...
```

```text
# vLLM — <model> on <SKU> <topology>
# image sha256:...
vllm serve ...
```

## Certified cells

A cell is CERTIFIED when every box below is ticked for BOTH engines. An
uncertified cell may appear in the tables above; it may not appear in anything
sales sends out.

- [ ] Same node, sequential legs, no co-tenant process on the GPUs
- [ ] Weights prefetched before both legs (a cold pull is not boot time)
- [ ] Boot ≤ 30 min, measured from before the serve process launched
- [ ] Greedy determinism: two runs of one prompt at temp 0, byte-identical
- [ ] Tool-call arguments parse as JSON, with `finish_reason == "tool_calls"`
- [ ] No `<think>`/`</think>` in content with thinking off
- [ ] Sampling pinned identically: temp 0, seed 42, presence and frequency
      penalties 0, `chat_template_kwargs.enable_thinking=false`
- [ ] Speculation the same on both engines (both on, or both off)
- [ ] 1 warmup discarded, 3 timed reps, raw series recorded not just the mean
- [ ] `compare.py` accepted the pair (it refuses mismatched workload axes)
- [ ] Image digest, serve command and `nvidia-smi` fingerprint pasted verbatim
- [ ] Result JSONs committed under this directory

## Open questions

Anything a reader would ask that the tables do not answer. Kept in the document
rather than in a thread, because a caveat that lives in a thread is a caveat
nobody reading the numbers will see.

-
