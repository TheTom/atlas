# Metal CI ran the real parity suite with an empty kernel registry

Observed September 6, 2026, after the H100 rental was destroyed. This is a CI repair, not a new enterprise GPU benchmark.

The [Metal job](https://github.com/Avarok-Cybersecurity/atlas/actions/runs/34007169227/job/101430753851) failed at PR head `8882f088b3e1382456c72a7288c267b8dc6985de`. The runner tested merge commit `1b311f1489291383ec9dded32d4f85a07450a3b0`. Both Metal compile checks passed, but the real parity suite returned exit 101: **0 passed, 35 failed, 5 ignored**. Failures included `Metal: unknown module 'noop_smoke'` and `Metal: unknown module 'attention_prefill'`. These are missing-module failures, not numerical disagreements.

The workflow sets `ATLAS_SKIP_BUILD=1` globally. `crates/atlas-kernels/build.rs` responds by emitting empty CUDA and Metal registries. The real Metal parity step selected its hardware/model/quant target but did not override that setting. [Commit 64b468b](https://github.com/Avarok-Cybersecurity/atlas/commit/64b468bf2d0602c9695dfb09f667e7608352cac6) adds `ATLAS_SKIP_BUILD: "0"` only to that step, plus a comment. Runtime code, kernel code, tolerances and performance gate paths are unchanged.

## Reproduction and oracle

Run on Tom's Mac with its real Apple Metal device, using an owned Cargo target directory. Exact commands, environment, exit status and timing are in the adjacent JSON receipts. The passing invocation and effective environment were read from the edited workflow YAML.

```sh
ATLAS_SKIP_BUILD=1 ATLAS_TARGET_HW=metal \
ATLAS_TARGET_MODEL=qwen3-5-4b-vlm-mlx-int8 ATLAS_TARGET_QUANT=mlx_int8 \
CUDARC_CUDA_VERSION=13000 CARGO_BUILD_JOBS=4 \
cargo test -p spark-runtime --no-default-features --features metal --locked metal_backend
```

| Check | Oracle | Observed | Verdict |
|---|---|---|---|
| Known-bad inherited setting | Real parity tests must fail when required modules are absent | Exit 101; 0 passed, 35 failed, 5 ignored; 18.667 s | Red reproduced |
| Workflow step override | The same tests must resolve real modules and pass without tolerance changes | Exit 0; 35 passed, 0 failed, 5 ignored; 43 Metal kernels compiled; 1.745 s | Green locally |
| Conditional-skip check | Success must involve a Metal backend, not a silent early return | Same suite with `-- --nocapture`: exit 0, 35 passed, 5 ignored, zero `skipping metal_backend` messages | Green locally |
| GitHub runner after push | The corrected parity job must pass on the CI runner | Pending at publication | Unproven remotely |

Five existing tests that require local model checkpoints remain ignored. No weights were downloaded. The red wall time includes initial compilation; the green wall time uses the same target cache. Those times are not a performance comparison.

Stopping rule: reproduce the missing registry on real Metal, execute the same suite green with no backend skips, pass the required local checks, publish the two-line fix, then await CI. Do not change unrelated kernels or use the destroyed rental.

## Required checks

All receipts are under `prepush/`.

- Campaign: 85 assertions; launcher: 30; datacenter Dockerfiles: 17.
- Atlas renderer: 346/346 over 19 entries; vLLM renderer: 258/258 over 31 entries.
- Artifact validator: 26/26, including seven known-bad fixtures; assembler: 16/16.
- PTX gate: all seven assertions passed on Spark 1 with CPU-only nvcc/ptxas, including the real known-bad assembly case. Its optional shellcheck was unavailable there; the two gate scripts passed local `shellcheck -S warning`.
- Formatting, typos and `git diff --check`: exit 0. No shell script was changed.
- Extra workflow syntax check, `actionlint -shellcheck= .github/workflows/ci.yml`: exit 0. Full actionlint returns 1 on both the original and edited workflow for the same three unrelated SC2016 informational shell warnings. The baseline logs retain this limitation.
- The first vLLM selftest invocation omitted the required `--recipes` argument and returned 2 before testing. The corrected command and its passing output are retained; no renderer fix was required.

The owned local Cargo target (634 MB) and Spark 1 CPU fixture directory (5.1 MB) were removed. `cleanup.json` retains before/after `df -h /` and removal confirmation. Spark 1's GPU and warm checkout were not used; Spark 2 and the destroyed rental were not contacted.

## Other CI state at the audited head

`pr-before.json` records successful Hopper and B200 x86_64 compilation jobs, all three PTX compilation jobs, docs and coverage. These are CI status observations; no new GPU execution or binary runtime validation is claimed. Clippy, workspace tests and the advisory benchmark check remained queued.

The other failed job, [seal status](https://github.com/Avarok-Cybersecurity/atlas/actions/runs/34007169227/job/101428937523), reports that the current head has no codeowner Seal. That is an outstanding maintainer review requirement. No seal, stamp, thread resolution or merge was performed.
