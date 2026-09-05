# Day-of runbook — Atlas vs vLLM on H100 / H200 / B200

Companion to the PRD (issue #899). Everything here is one of: a command that has a
GPU-free selftest, a receipt already measured on Spark 1, or an explicit "first
time on silicon" step. Nothing below has run on Hopper or B200 yet; the point of
the runbook is that the first run is a checklist, not an exploration.

## 0. Before renting (all done off the GPU clock)

| Item | Where | State |
|---|---|---|
| Kernels compile for sm_90a and sm_100a | `scripts/hopper_ptx_gate.sh`, receipts in the PR | 871/871 both arches, `--strict` on Super and Qwen3.6 |
| Wrong image fails loudly | `atlas-core::arch` + `spark-runtime` preflight | unit-tested; never seen a real mismatch |
| x86_64 `spark` binary for hopper / b200 | `.github/workflows/datacenter-binaries.yml` artifact, or `docker/hopper`, `docker/b200` | workflow authored; first CI run pending |
| vLLM control commands per (model, SKU) | `bench/campaign/vllm_control.sh` + `vllm_recipes.json` (from the verified recipe JSON) | rendered, digests must be pinned day-of |
| One-command cell | `bench/campaign/run_cell.sh` | dry-run tested |
| Artifact schema + validator | `bench/campaign/artifact.schema.json`, `validate_artifact.py` | selftests incl. known-bad |
| Client parity pins | `bench/hopper_ab/workloads.json` | frozen: temp 0, seed 42, penalties 0, `enable_thinking` false for think-off, nonce, 1 warmup + 3 reps |
| Weights prefetched to a persistent volume | `WEIGHTS-MANIFEST.md` (issue #899, comment 3) | sizes from the HF API; download with `hf download <id> --revision <rev>` |
| GB10 rehearsal of the whole flow | Codex Step A (Spark 2) | see NIGHT-LOG |

## 1. Provision

1. Rent the smallest box the ladder needs first: 1×H100 → 1×H200 → 1×B200, then multi-GPU. Never an 8-GPU node before the 1- and 2-GPU cells certify.
2. Driver ≥ r580, CUDA 13 runtime in the container. `nvidia-smi -q > preflight/nvidia-smi-q.txt` and keep it.
3. Persistent volume mounted at `~/.cache/huggingface`, weights already present (`hf download` list from the manifest). Check `df -h`.
4. Pull: `docker pull vllm/vllm-openai:<tag from vllm_recipes.json>`; record `docker inspect --format '{{index .RepoDigests 0}}'` and export it as `VLLM_IMAGE_DIGEST`. Pull or build `atlas-hopper` / `atlas-b200` (`docker build -f docker/hopper/Dockerfile -t atlas-hopper .`, ~10–15 min) or download the workflow artifact `spark-hopper-x86_64` and `chmod +x`.

## 2. Atlas first boot (Phase A)

```bash
# 1. does the binary belong on this GPU? (exit code = unresolved kernels; JSON has compiled_arch + device_cc)
./spark serve <MODEL> --check-kernels --no-tui
# 2. single GPU, minimal flags, then the recipe flags
./spark serve <MODEL> --port 8888 --bind 0.0.0.0 --no-tui --max-batch-size 1 --gpu-memory-utilization 0.90
# 3. N GPUs (EP) — workers first, health poll, exact rank-0 command echoed for the artifact
NGPUS=4 EP_SIZE=4 TP_SIZE=1 NCCL_PROFILE=debug bash scripts/start-node-ep.sh <MODEL>
```

Expected: `/health` 503 `{"status":"loading"}` then 200 `{"status":"ready"}`; `--check-kernels` exit 0 with `compiled_arch: sm_90a` (hopper) or `sm_100a` (b200) and `device_cc` 9.0 / 10.0. A mismatch message naming `ATLAS_TARGET_HW=...` means the wrong image. First-request cold start 5–30 s unless `--warmup-prompt` is passed (the cell runner passes it).

Every FP8 checkpoint gets `--fp8-kv-calibration-tokens 256` with FP8 KV (the cell kit adds it): without KV scales the FP8 KV scale defaults to 1.0 and clips, which on GB10 produced degenerate output that a byte-identity determinism check did not catch.

Model notes (from the PRD §6.1): Super → `--tool-call-parser bare_json`, think-on primary row, spec off by default; Nano → spec off, `--max-seq-len 32768`; Qwen3.6-35B → `--speculative --num-drafts 2 --mtp-quantization bf16`, `--lm-head-dtype bf16`; Qwen3-Next-80B → default `--ssm-h-dtype`; DeepSeek V4-Flash → EP only, spec off, `--oom-guard-mb 512`. On B200 the W4A4 escape hatch is compiled out; FP8 checkpoints are the A/B quant on both SKUs.

## 3. A cell

```bash
bench/campaign/run_cell.sh --engine atlas --model nemotron-3-super-fp8 --sku h200 \
  --workload lat --concurrency 16 --spec off --think on --out results/h200/super/atlas --yes
bench/campaign/run_cell.sh --engine vllm  --model nemotron-3-super-fp8 --sku h200 \
  --workload lat --concurrency 16 --spec off --think on --out results/h200/super/vllm --yes
bench/hopper_ab/compare.py results/h200/super/atlas/ladder.json results/h200/super/vllm/ladder.json
```

Order per box: Atlas leg fully (all workloads × C), tear down, vLLM leg, tear down, compare. Both legs inside 24 h. Spec on for both or off for both; the runner refuses a mismatched pair through `compare.py`.

Gates, in order, each producing JSON: time-to-ready ≤ 1800 s and a usable 1-token completion; coherency (determinism A/A, tool call parses, no `<think>` when off); ladder with the vacuity floor (every request ≥ 80 % of its output budget); validator on the artifact. A failed gate is the result of the cell: `verdict` NO-GO or PARTIAL with `failing_stage`. Do not retune and rerun; note it and move on.

## 4. Certify

A cell is CERTIFIED only if `validate_artifact.py` passes, the paired cell exists within 24 h, and the pair was spec-matched and think-matched. Fill `RESULTS-TEMPLATE.md` from the artifacts; the sales line is the PRD §13 form.

## 5. Teardown and receipts

Stop containers/ranks (`start-node-ep.sh --stop`, `docker stop`), copy `results/` and `preflight/` off the box, and add the artifacts under the campaign issue. If a kernel fails at load on silicon, run `--check-kernels` again and attach the JSON: that is the `expected_absent` harvest the PR says is still owed.

## Readiness checklist (tick before the first invoice)

- [ ] `spark --check-kernels` exit 0 on the target SKU with the expected `compiled_arch` / `device_cc`
- [ ] Atlas single-GPU boot + coherency on Nano (H100 or B200)
- [ ] vLLM Nano recipe boot + coherency, same box, digest recorded
- [ ] One full A/B pair through `run_cell.sh` with the validator green
- [ ] N-GPU boot with `start-node-ep.sh` (NCCL default profile) on the first multi-GPU box
- [ ] Results template row filled from artifacts, not by hand
