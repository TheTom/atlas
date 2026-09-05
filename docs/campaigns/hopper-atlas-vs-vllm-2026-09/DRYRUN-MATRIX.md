# Step D2: rental-day dry-render matrix

CPU-only dry-render evidence collected 2026-09-05. No engine, Docker container or GPU was started. These are not H100, H200, B200 or GB10 performance measurements.

**The matrix is not rental-ready.** All rendered vLLM argv arrays match the recipe JSON and all 144 runnable Atlas FP8 renders contain calibration 256, but a known-invalid Nano speculative cell returns success through the driver, thinking policy is not consistently gated, and several named bookings/configurations cannot be selected. No campaign script, recipe JSON, schema, ladder or frozen code path was changed.

Code under test: `b2c17cfe30c33c53d28c4fbec35f6204b8cfb14b`. Policy source: docs branch `campaign/docs-hopper-2026-09` at `0b21f2a`, [PRD](https://github.com/TheTom/atlas/blob/0b21f2a/docs/campaigns/hopper-atlas-vs-vllm-2026-09/PRD-atlas-vs-vllm-hopper.md). Every log has the exact argv, exit status, elapsed time, full stdout and full stderr. [Source hashes and counts](evidence/dryrun-matrix/summary.json), [environment](evidence/dryrun-matrix/environment.json), [machine-readable index](evidence/dryrun-matrix/index.json), [enumeration](evidence/dryrun-matrix/enumeration.json), [collection script](evidence/dryrun-matrix/collect.py), [independent argv auditor](evidence/dryrun-matrix/audit.py).

## Coverage and stopping rule

The PRD has a model/topology list and frozen shapes, but does not assign a final spec/think state to every booking. Its own later sections disagree with earlier compile status, topology, quantization and speculative-depth statements. Therefore this report does not invent a fully frozen scored grid. It enumerates the named booking envelope and distinguishes scored candidates, conditional alternatives, and policy-only probes. The lead must resolve the remaining choices before labelling any combination a scored cell.

Each model/SKU is expanded into both engines, both frozen workloads (`lat` 1024/256; `agent` 4096/512), C=1 and C=16, and both spec/think switches. This is 32 cells per model/SKU, with an additional direct vLLM control render for each vLLM cell. Unsupported switches are explicitly marked as probes. Source lines below refer to the pinned PRD, not a moving branch.

The 26 model/SKU pairs actually named for this campaign produce 832 cells. Four extra GLM SKU pairs present only in the recipe JSON produce 128 policy probes; the explicitly unsupported DeepSeek H100 pair and the disputed MiniMax M3 H100 pair add 64; two unallocated P0 NVFP4 model-key proposals add 64. Together there are **34 model/SKU pairs, 1,088 driver invocations and 544 direct vLLM invocations**. Kimi is B200-only in this scored-campaign envelope; H100/H200 Kimi recipes are not silently added as scored rows. Their Hopper-emulation option remains a separately labelled customer exception in the PRD. Optional C=2..128 overflow sweeps are not frozen scored cells and were not rendered.

`scoring-envelope` means a candidate under the PRD's generic on/off rules, not a promise to rent or a resolved policy. `conditional-alternative` includes Super MTP and the Kimi DSpark second row. `policy-probe` includes Nano MTP, GLM-5.x think-off, Qwen3-Next Instruct think-on, DeepSeek MTP and unsupported SKU/model-key proposals. The GLM-5.3-Flash row is P1 in this docs revision; the task's P0/P1 wording does not define a second scored policy.

The stopping rule was reached: every enumerated cell has both applicable command results and an oracle verdict; all ambiguities and missing recipes have evidence. No recipe was invented to turn a red or absent row green. D2 completed within its two-hour time box.

## Oracles, red first, then observations

| Oracle | Known-bad observation first | Observed valid-input check | Verdict |
|---|---|---|---|
| Missing model/SKU refuses clearly | Missing Atlas and vLLM model keys each exited 3 with one line naming model and SKU | All absent entries produce that exact line; stderr is empty | PASS for refusal mechanism; absent scored candidates remain blocked |
| Invalid speculation is rejected | Invalid switch exited 2; Nano direct vLLM and Atlas spec-on exited 4 | Nano driver spec-on exited **0**, with nested error moved to stdout | FAIL: D2-F01 |
| vLLM serve argv equals JSON, including TP, context, quantization flags, head/worker and spec groups | Deliberately changed TP to 99; auditor exited 1 | **816/816** complete render-set comparisons passed (408 cells × driver/direct); model, TP and missing explicit maxlen/quant flags are checked as actual JSON contents, not filled in | PASS for transcription only |
| Atlas FP8 calibration and topology | Deliberately removed calibration; auditor exited 1 | **144/144** runnable Atlas rank-0 commands have calibration 256 and match recipe model/topology/spec/think flags | PASS |
| Frozen workload and client think flag | Deliberately changed ISL to 999; auditor exited 1 | **552/552** runnable cells render correct ISL/OSL/C, 3 reps, 1 warmup and requested ladder think flag | PASS for render |
| Paired speculative depth | Spec-on render checked against exact draft-count tokens after the corrupted-argv red | **40/40** paired vLLM cells with Atlas speculation available match draft depth: Qwen3.6 = 3, Qwen3-Next = 2 | PASS for available pairs; Super/DeepSeek do not form a spec-on pair |
| Coherency actually checks think-on workload | Known-wrong localhost replies exited 1 | Gate then exited 0 on seven think-off requests while the same stub returned empty content when thinking was enabled | FAIL: D2-F02 |

[Refusal red cases](evidence/dryrun-matrix/known-bad.json), [auditor red cases](evidence/dryrun-matrix/auditor-red-first.json), [HTTP policy reproduction](evidence/dryrun-matrix/think-policy-observation.log). Gates that require GPU boot, real coherency, timing, image/parser contents or memory were not claimed from these CPU checks. No recipe JSON was edited, so the three recipe-edit suites were not triggered; the checks above are observed output from the named D2 oracles.

## Model/SKU allocation and policy sources

| Model key | SKU | PRD source | Role / qualification |
|---|---|---|---|
| `nemotron-3-nano-fp8` | h100 | 3.1 L61; 6.1 L160; 7 L189 | plumbing; Atlas: runnable; key: canonical |
| `nemotron-3-nano-fp8` | h200 | 3.1 L61; 6.1 L160; 7 L189 | plumbing; Atlas: runnable; key: canonical |
| `nemotron-3-nano-fp8` | b200 | 3.1 L61; 6.1 L160; 7 L189 | plumbing; Atlas: runnable; key: canonical |
| `nemotron-3-super-fp8` | h100 | 3.1 L62; 5 L127; 6.1 L161; 7 L187-188 | P0; Atlas: runnable; key: canonical |
| `nemotron-3-super-fp8` | h200 | 3.1 L62; 5 L127; 6.1 L161; 7 L187-188 | P0; Atlas: runnable; key: canonical |
| `nemotron-3-super-fp8` | b200 | 3.1 L62; 5 L127; 6.1 L161; 7 L187-188 | P0; Atlas: runnable; key: canonical |
| `qwen3.6-35b-a3b-fp8` | h100 | 3.1 L63; 6.1 L162; 7 L190; 12 | P0-compile-status-conflict; Atlas: runnable; key: canonical |
| `qwen3.6-35b-a3b-fp8` | h200 | 3.1 L63; 6.1 L162; 7 L190; 12 | P0-compile-status-conflict; Atlas: runnable; key: canonical |
| `qwen3.6-35b-a3b-fp8` | b200 | 3.1 L63; 6.1 L162; 7 L190; 12 | P0-compile-status-conflict; Atlas: runnable; key: canonical |
| `qwen3-next-80b-fp8` | h100 | 3.1 L64; 6.1 L163; 7 L191 | P1; Atlas: runnable; key: canonical |
| `qwen3-next-80b-fp8` | h200 | 3.1 L64; 6.1 L163; 7 L191 | P1; Atlas: runnable; key: canonical |
| `qwen3-next-80b-fp8` | b200 | 3.1 L64; 6.1 L163; 7 L191 | P1; Atlas: runnable; key: canonical |
| `deepseek-v4-flash` | h200 | 3.1 L65; 6.1 L164; 7 L195 | P1; Atlas: runnable; key: canonical |
| `deepseek-v4-flash` | b200 | 3.1 L65; 6.1 L164; 7 L195 | P1; Atlas: runnable; key: canonical |
| `glm-5.3-flash` | h200 | 3.1 L66; 4 L101; 5 L127; 16 L312 | P1-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `glm-5.3` | h200 | 3.2 L77; 4 L101; 7 L192; 16 L312 | Phase-D-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `glm-4.5-air-fp8` | h100 | 3.1 L68; 4 L101; 7 L193; 16 L312 | canary-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `glm-4.5-air-fp8` | h200 | 3.1 L68; 4 L101; 7 L193; 16 L312 | canary-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `kimi-k3` | b200 | 3.1 L67; 3.2 L76; 7 L194; 16 L311 | Phase-D-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `minimax-m2.7` | h200 | 3.2 L73; 5 L125 | Phase-D-conditional; Atlas: conditional; key: unallocated-proposal |
| `qwen3.8-flash-next-fp8` | h100 | 3.2 L74; 5 L127 | Phase-D-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `qwen3.8-flash-next-fp8` | h200 | 3.2 L74; 5 L127 | Phase-D-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `qwen3.8-flash-next-fp8` | b200 | 3.2 L74; 5 L127 | Phase-D-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `minimax-m3` | h200 | 3.2 L75 | Phase-D-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `minimax-m3` | b200 | 3.2 L75 | Phase-D-vllm-reference; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `qwen3.8-27b-fp8` | h200 | 16 L309 | first-paid-cell; Atlas: runnable; key: unallocated-proposal |
| `glm-5.3-flash` | h100 | recipe JSON only; PRD 3.1 names H200 | recipe-only-probe; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `glm-5.3-flash` | b200 | recipe JSON only; PRD 3.1 names H200 | recipe-only-probe; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `glm-5.3` | h100 | recipe JSON only; PRD 3.2 names H200 | recipe-only-probe; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `glm-5.3` | b200 | recipe JSON only; PRD 3.2 names H200 | recipe-only-probe; Atlas: ATLAS_UNSUPPORTED; key: canonical |
| `deepseek-v4-flash` | h100 | 3.1 L65; 8 L212 explicit no-H100-recipe | negative-SKU-probe; Atlas: unsupported-SKU; key: canonical |
| `nemotron-3-super-nvfp4` | b200 | 3.1 L69; 5 L125; 8 L214 | NVFP4-unallocated-probe; Atlas: ATLAS_UNSUPPORTED; key: unallocated-proposal |
| `qwen3.6-35b-a3b-nvfp4` | b200 | 3.1 L63,L69; 5 L125; 8 L214 | NVFP4-unallocated-probe; Atlas: ATLAS_UNSUPPORTED; key: unallocated-proposal |
| `minimax-m3` | h100 | §3.2 L75; §8 L212 says no H100 recipe; JSON has a profile | negative-SKU-probe; Atlas: ATLAS_UNSUPPORTED; key: canonical |

For absent model keys, `qwen3.8-27b-fp8`, `minimax-m2.7`, `nemotron-3-super-nvfp4` and `qwen3.6-35b-a3b-nvfp4` are **explicit proposed allocation names**, not claimed existing keys. Searching the entire JSONs found no entry for the PRD checkpoint/target either. A spelling change alone cannot make these cells runnable.

## Topology alternatives that the CLI cannot select

`run_cell.sh` accepts model/SKU but no topology selector; `atlas_recipes.json` and `vllm_recipes.json` each contain at most one entry per key/SKU. Thus each alternative below maps to the same captured commands for that key/SKU. These are policy/allocation gaps, not additional silent runs with guessed flags.

| PRD booking / alternative | Observed Atlas | Observed vLLM | Consequence |
|---|---|---|---|
| Super H100: 2, 4 and 8 GPUs (§3.1 L62, §5 L127, §6.1 L161) | 2, EP2 TP1 | 8, TP8 | Neither a matched 2/4-GPU pair nor recipe-max Atlas 8 is selectable |
| Super H200: 1 and 8 GPUs (§5 L127, §6.1 L161, §7 L187) | 1 | 8, TP8 | First small H200 booking is not the rendered vLLM pair |
| Super B200: 1 and 2 GPUs (§3.1 L62 vs §5 L127) | 1 | 1 | One-GPU pair renders; two-GPU alternative is unallocated |
| Qwen3-Next H100: requested 2 vs generated 8 (§3.1 L64, §6.1 L163) | no recipe, exit 3 | 8, TP8 | Requested small topology cannot be rendered |
| DeepSeek B200: Atlas EP4 vs recipe 8 (§3.1 L65, §6.1 L164, §7 L195) | 4, EP4 TP1 | 8, TP8 + expert parallel | Must label unmatched topology; no matched alternative selector |
| Flash-Next H200: 4–8 range / explicit 8 TEP (§3.2 L74, §5 L127) | unsupported, exit 3 | 4, TP4 | Eight-GPU named form is not represented |
| GLM-5.3-Flash H200: 4–8 (§3.1 L66) | unsupported, exit 3 | 8, TP8 | Four-GPU alternative unallocated |
| Kimi B200: 16 GPUs, TP8 PP2 (§3.1 L67) | unsupported, exit 3 | head + one headless worker, TP8 PP2 | Topology render matches; real multi-node control is intentionally refused pending manual deployment |
| GLM-4.5-Air: 2 H100 or 1 H200 (§3.1 L68) | unsupported, exit 3 | no recipe, exit 3 | Canary remains reconstructed/unallocated |
| MiniMax M2.7: 8 H200 (§3.2 L73) | no recipe, exit 3 | no recipe, exit 3 | Conditional overflow cell cannot be rendered |
| Qwen3.8-27B: 1 H200 (§16 L309) | no recipe, exit 3 | no recipe, exit 3 | Adopted first paid cell cannot be rendered |

Spec is always requested identically in paired rows. This does **not** make a pair exist: Super and DeepSeek Atlas spec-on refuse while the vLLM reference renders speculation. Those are blocked alternatives, never mixed scored pairs. Likewise, matching numeric draft count alone does not establish common speculative method or weight identity. The recipe supplies Qwen3.6 MTP depth 3 while PRD §6.1/§7 mention a campaign depth-2 adaptation; no adaptation is selectable through this matrix, and the current depth-3 pair is reported exactly.

## Findings ranked by rental-day impact

### D2-F01 — P1: driver dry-run hides a failed vLLM render

Reproduction (working directory is the pinned checkout):

```bash
bash bench/campaign/run_cell.sh --engine vllm --model nemotron-3-nano-fp8 --sku h100 --workload lat --concurrency 1 --spec on --think off --out /tmp/atlas-step-d-dryrun-not-created/negative --dry-run
bash bench/campaign/vllm_control.sh nemotron-3-nano-fp8 h100 --spec on --dry-run
```

Observed driver exit **0**, direct control exit **4**. The driver's stderr is exactly empty. Its stdout contains the refusal and then boot/coherency/ladder commands. Direct-control stderr is exactly:

```text
ERROR: --spec on, but the recipe for nemotron-3-nano-fp8 on h100 renders no speculative profile.
       Speculation is both-or-neither: run BOTH legs spec off, or pick a model whose recipe has one.
```

This occurs in 24 Nano cells across the three SKUs. `run_cell.sh:774–775` leaves the dry-run renderer's failure unhandled and finalization at line 637 exits 0. An exit-only readiness sweep would pass an unusable recipe. [Driver evidence](evidence/dryrun-matrix/known-bad-nano-spec-through-driver.log), [direct evidence](evidence/dryrun-matrix/known-bad-nano-spec-direct.log). Script fix belongs to the lead.

### D2-F02 — P1: think-on cells have think-off coherency evidence

```bash
PYTHONDONTWRITEBYTECODE=1 python3 docs/campaigns/hopper-atlas-vs-vllm-2026-09/evidence/dryrun-matrix/reproduce_think_policy.py
```

Observed reproduction exit **0** (the observations matched the reproduction oracle); the nested known-wrong gate exited **1**, then the clean-think-off/broken-think-on gate exited **0**. Both nested stderr streams are exactly empty. The gate's seven retained request bodies all carry `enable_thinking: false`; a direct request to the same stub with `true` produces empty content. This is independent of a real model's ability to turn thinking off.

`run_cell.sh:830–833` never forwards a think policy to coherency; `coherency_gate.py:284` fixes all probes to false, while `run_cell.sh:840–842` forwards `--enable-thinking` to the ladder. Super's primary think-on row and GLM-5.x/Kimi reference rows therefore have a gate for a different request policy. [Observed HTTP JSON](evidence/dryrun-matrix/think-policy-observation.json), [passing gate JSON including requests](evidence/dryrun-matrix/think-policy-clean.json), [failing known-answer control](evidence/dryrun-matrix/think-policy-wrong-answer.json). No gate or ladder edits made.

### D2-F03 — P1: policy-blocked thinking settings are accepted

```bash
bash bench/campaign/run_cell.sh --engine vllm --model glm-5.3 --sku h200 --workload lat --concurrency 1 --spec off --think off --out /tmp/atlas-step-d-dryrun-not-created/vllm.glm-5.3.h200.lat.c1.specoff.thinkoff --dry-run
bash bench/campaign/run_cell.sh --engine atlas --model qwen3-next-80b-fp8 --sku h200 --workload lat --concurrency 1 --spec off --think on --out /tmp/atlas-step-d-dryrun-not-created/atlas.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkon --dry-run
```

Both exit **0**, stderr is exactly empty. GLM-5.3/Flash think-off is explicitly blocked by PRD §4 until a matched policy is frozen; Qwen3-Next Instruct explicitly supports only non-thinking (§6.1). The driver checks only on/off spelling at `run_cell.sh:118`; the Atlas renderer checks speculative support but has no corresponding thinking capability check. These results are marked policy failures, not evidence that reasoning was disabled or enabled. [GLM evidence](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c1.specoff.thinkoff.log), [Qwen3-Next evidence](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkon.log).

### D2-F04 — P0: the adopted first paid cell has no recipe allocation

```bash
bash bench/campaign/run_cell.sh --engine atlas --model qwen3.8-27b-fp8 --sku h200 --workload lat --concurrency 1 --spec on --think off --out /tmp/atlas-step-d-dryrun-not-created/atlas.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkoff --dry-run
bash bench/campaign/vllm_control.sh qwen3.8-27b-fp8 h200 --spec on --dry-run
```

Both exit **3**, stderr is exactly empty, stdout is exactly:

```text
no rendered profile for qwen3.8-27b-fp8 on h200
```

The checkpoint itself is absent from both JSONs; the proposed key is clearly marked unallocated. Booking the PRD §16 first paid H200 cell would reach this stop before launch. Allocate a verified recipe and frozen MTP depth before booking. [Atlas evidence](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkoff.log), [vLLM evidence](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkoff.log).

The same supported-mechanism/missing-allocation distinction applies to MiniMax M2.7 H200 and the already acknowledged GLM-4.5-Air H100/H200 canaries. Each exits 3 with empty stderr and stdout `no rendered profile for <model-key> on <sku>`; the table and logs retain the literal text. P0 NVFP4 B200 extras have neither canonical keys nor a final matched Atlas policy; PRD §8 keeps Atlas FP8 until its port, so they remain overflow proposals, not false missing-green claims.

### D2-F05 — P0: named small bookings map to larger or unmatched topologies

No new flags were invented. The exact Super H100/H200 commands render Atlas 2/1 GPUs and vLLM 8 GPUs, each exit **0** and each stderr exactly empty. The topology table above enumerates all alternatives. A 1×H200 or 2/4×H100 booking cannot run the rendered vLLM profile. Explicitly choose recipe-max or allocate a verified adaptation before booking; generic key/SKU success is not proof the proposed node fits. [Super H200 Atlas](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkon.log), [Super H200 vLLM](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkon.log).

### D2-F06 — P1: Kimi render matches its JSON but not the scored campaign context

```bash
bash bench/campaign/vllm_control.sh kimi-k3 b200 --spec off --dry-run
```

Exit **0**, stderr exactly empty. Both head and worker render `--max-model-len 1048576`; the PRD scored configuration is `49152` (§3.1, §7, §16). TP8, PP2, worker `--headless`, native model identity, FP8 KV and attention-config are preserved. This is a missing documented campaign adaptation, not proof of an OOM or performance defect; frozen latency requests remain 1024/256 or 4096/512. `run_cell.sh` has no extra-args/context selector. DSpark-on is only a secondary unresolved probe because §7 says its strategy excludes TP8+PP2. Real multi-node control is intentionally refused (documented exit 6); a cluster placement plan is still required. [Kimi log](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c1.specoff.thinkon.log).

### D2-F07 — P1: MiniMax M3 B200 quant label differs from the PRD

```bash
bash bench/campaign/vllm_control.sh minimax-m3 b200 --spec off --dry-run
```

Exit **0**, stderr exactly empty; output says `quant: bf16` and serves `MiniMaxAI/MiniMax-M3` without an explicit quantization override. PRD §3.2 names an NVFP4 B200 reference. The renderer correctly mirrors its JSON; this audit does not infer actual weight bytes from a CLI lacking a quant flag. Resolve the intended artifact with D3 identity evidence before quoting an NVFP4 result. [M3 log](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c1.specoff.thinkoff.log).

### D2-F08 — existing P0 launch gap: Nano parser file is not provisioned

Nano renders exit **0** with empty stderr and a relative `--reasoning-parser-plugin nano_v3_reasoning_parser.py`; the container mounts only the Hugging Face cache. This was already reported on [PR #895](https://github.com/Avarok-Cybersecurity/atlas/pull/895#discussion_r3939764399). The current dry renders still contain it. Image contents were not inspected in D2, so no new engine-boot claim or duplicate review comment is warranted. [Nano log](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkoff.log).

### D2-F09 — P2: README's thinking limitation is stale

`bench/campaign/README.md` still says the ladder hardcodes false and run_cell warns for think-on. All 276 available think-on renders actually pass `--enable-thinking` to the ladder, consistent with current script and ladder code. The residual problem is D2-F02's coherency policy, not the old blanket client limitation. This was observed by reading the emitted commands; stderr was empty. Update the README after resolving gate policy.

### D2-F10 — P2: MiniMax M3 H100 exclusion is stale in the PRD

```bash
bash bench/campaign/vllm_control.sh minimax-m3 h100 --spec off --dry-run
```

Exit **0**, stderr exactly empty. The JSON and rendered output contain a 16-GPU, two-node TP16 profile, whereas PRD §8 L212 says there is no H100 recipe. These 32 cells are negative-SKU/policy probes, not an added scored H100 booking. Atlas still refuses the model in one line. Resolve the stale exclusion before someone mistakes either statement for a verified hardware result. [M3 H100 evidence](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c1.specoff.thinkoff.log).

## Result counts and limits

The 1,088 cells are **552 scoring-envelope candidates, 472 policy probes and 64 conditional alternatives**, not 1,088 frozen scored cells. The complete audit yields 164 render passes, 500 blocked rows, 64 expected speculative refusals, 272 expected Atlas unsupported refusals and 88 expectation failures. Of those 88, **24 are the measured driver exit-code defect** (D2-F01), **48 are accepted GLM think-off policy probes** and **16 are accepted Qwen3-Next Instruct think-on policy probes** (D2-F03). The latter 64 demonstrate missing policy guards relative to the PRD, not an observed real-engine reasoning defect. D2-F02 separately demonstrates a request-policy mismatch using actual HTTP traffic to a CPU fixture; 276 available think-on render rows are flagged for it.

Recipe token fidelity and FP8 calibration are green. The missing allocations, topology/context/quant choices, Kimi placement, and inherited Nano parser gap remain written readiness blocks. No contradiction was “fixed” by modifying a faithfully transcribed recipe. Model support, license/access, actual weight quantization, GPU memory fit and engine boot belong to their separate evidence.

## Per-cell results

`run` is `run_cell.sh`; `control` is the additional `vllm_control.sh` invocation (`—` for Atlas). `EXPECTED_UNSUPPORTED` means the PRD's absent Atlas port was refused as expected. `EXPECTED_SPEC_REFUSAL` is a successful negative probe. `BLOCKED` records a policy/recipe/deployment gap despite any zero exit. `RENDER_PASS` is only an argv/orchestration render result. **None of these means CERTIFIED.**

For every row, the log holds the full command and both literal stderr streams. `∅` in the stderr column means exactly zero bytes; `log` points to nonempty literal stderr. The [index JSON](evidence/dryrun-matrix/index.json) repeats exact stderr for every non-green row, along with individual commands, exits, stdout/stderr hashes and findings. Absent-recipe refusals are one stdout line, `no rendered profile for <model-key> on <sku>`, with empty stderr; the literal `ATLAS_UNSUPPORTED` marker is not emitted. The two-line speculative refusal is a different exit-4 contract. The distinct stderr from valid refusals is shown in the findings above; empty stderr is never treated as evidence of success.

| Cell id / raw log | Category | run | control | Verdict / finding | stderr |
|---|---|---:|---:|---|---|
| [atlas.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.lat.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.lat.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.lat.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.lat.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.agent.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.agent.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.agent.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h100.agent.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [vllm.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c1.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.lat.c16.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.agent.c1.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h100.agent.c16.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [atlas.nemotron-3-nano-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.lat.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.lat.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.lat.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.lat.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.agent.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.agent.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.agent.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.h200.agent.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [vllm.nemotron-3-nano-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.lat.c1.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.lat.c16.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.agent.c1.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.h200.agent.c16.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [atlas.nemotron-3-nano-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.lat.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.lat.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.lat.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.lat.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.agent.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.agent.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-nano-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-nano-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.agent.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-nano-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-nano-fp8.b200.agent.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [vllm.nemotron-3-nano-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.lat.c1.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.lat.c16.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.agent.c1.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Nano-parser-not-provisioned | ∅ |
| [vllm.nemotron-3-nano-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [vllm.nemotron-3-nano-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-nano-fp8.b200.agent.c16.specon.thinkon.log) | policy-probe | 0 | 4 | FAIL: driver-exit-mismatch | log |
| [atlas.nemotron-3-super-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.lat.c1.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.lat.c1.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.lat.c16.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.lat.c16.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.agent.c1.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.agent.c1.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.agent.c16.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h100.agent.c16.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [vllm.nemotron-3-super-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.lat.c1.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.lat.c1.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.lat.c16.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.lat.c16.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.agent.c1.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.agent.c1.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.agent.c16.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h100.agent.c16.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [atlas.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c1.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c1.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c16.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.lat.c16.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.agent.c1.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.agent.c1.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.agent.c16.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.h200.agent.c16.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [vllm.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c1.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c1.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c16.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.lat.c16.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.agent.c1.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.agent.c1.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.agent.c16.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.nemotron-3-super-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.h200.agent.c16.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [atlas.nemotron-3-super-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.lat.c1.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.lat.c1.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.lat.c16.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.lat.c16.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.agent.c1.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.agent.c1.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.nemotron-3-super-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.nemotron-3-super-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.agent.c16.specon.thinkoff.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.nemotron-3-super-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-fp8.b200.agent.c16.specon.thinkon.log) | conditional-alternative | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [vllm.nemotron-3-super-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.nemotron-3-super-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.nemotron-3-super-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.lat.c1.specon.thinkoff.log) | conditional-alternative | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.nemotron-3-super-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.lat.c1.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.nemotron-3-super-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.nemotron-3-super-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.nemotron-3-super-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.lat.c16.specon.thinkoff.log) | conditional-alternative | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.nemotron-3-super-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.lat.c16.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.nemotron-3-super-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.nemotron-3-super-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.nemotron-3-super-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.agent.c1.specon.thinkoff.log) | conditional-alternative | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.nemotron-3-super-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.agent.c1.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.nemotron-3-super-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.nemotron-3-super-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.nemotron-3-super-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.agent.c16.specon.thinkoff.log) | conditional-alternative | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.nemotron-3-super-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-fp8.b200.agent.c16.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h100.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h100.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3.6-35b-a3b-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-fp8.b200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.6-35b-a3b-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-fp8.b200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.lat.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.lat.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.agent.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.agent.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [atlas.qwen3-next-80b-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h100.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED: requested-H100-topology-unallocated; named-cell-missing-recipe | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.lat.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.lat.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.agent.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.agent.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h100.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c1.specon.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c16.specoff.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.lat.c16.specon.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.agent.c1.specoff.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.agent.c1.specon.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.agent.c16.specoff.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.h200.agent.c16.specon.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.lat.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.lat.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.agent.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.agent.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.h200.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.lat.c1.specoff.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.lat.c1.specon.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.lat.c16.specoff.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.lat.c16.specon.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.agent.c1.specoff.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.agent.c1.specon.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.agent.c16.specoff.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.qwen3-next-80b-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3-next-80b-fp8.b200.agent.c16.specon.thinkon.log) | policy-probe | 0 | — | FAIL: Instruct-think-on-accepted; policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.lat.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.lat.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.agent.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.agent.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3-next-80b-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3-next-80b-fp8.b200.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.deepseek-v4-flash.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.lat.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.lat.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.deepseek-v4-flash.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.lat.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.lat.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.deepseek-v4-flash.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.agent.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.agent.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.deepseek-v4-flash.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.agent.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h200.agent.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [vllm.deepseek-v4-flash.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.deepseek-v4-flash.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.deepseek-v4-flash.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.deepseek-v4-flash.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.deepseek-v4-flash.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.deepseek-v4-flash.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.deepseek-v4-flash.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.deepseek-v4-flash.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.deepseek-v4-flash.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.deepseek-v4-flash.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.deepseek-v4-flash.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.deepseek-v4-flash.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.deepseek-v4-flash.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.deepseek-v4-flash.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.deepseek-v4-flash.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.deepseek-v4-flash.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h200.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.deepseek-v4-flash.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.lat.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.lat.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.deepseek-v4-flash.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.lat.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.lat.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.deepseek-v4-flash.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.agent.c1.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.agent.c1.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | — | RENDER_PASS | ∅ |
| [atlas.deepseek-v4-flash.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | — | BLOCKED: coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.agent.c16.specon.thinkoff.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [atlas.deepseek-v4-flash.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.b200.agent.c16.specon.thinkon.log) | policy-probe | 4 | — | EXPECTED_SPEC_REFUSAL | log |
| [vllm.deepseek-v4-flash.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; paired-GPU-count-differs | ∅ |
| [vllm.deepseek-v4-flash.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.b200.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off; paired-GPU-count-differs | ∅ |
| [atlas.glm-5.3-flash.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.glm-5.3-flash.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.lat.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.lat.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.agent.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.agent.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.glm-5.3.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.glm-5.3.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h200.agent.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h200.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h200.agent.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.glm-5.3.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h200.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.glm-4.5-air-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h100.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.lat.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.lat.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.lat.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.lat.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.agent.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.agent.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.agent.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h100.agent.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-4.5-air-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-4.5-air-fp8.h200.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.lat.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.lat.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.agent.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.glm-4.5-air-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-4.5-air-fp8.h200.agent.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [atlas.kimi-k3.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.kimi-k3.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.kimi-k3.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.kimi-k3.b200.lat.c1.specon.thinkoff.log) | conditional-alternative | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.kimi-k3.b200.lat.c1.specon.thinkon.log) | conditional-alternative | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.kimi-k3.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.kimi-k3.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.kimi-k3.b200.lat.c16.specon.thinkoff.log) | conditional-alternative | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.kimi-k3.b200.lat.c16.specon.thinkon.log) | conditional-alternative | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.kimi-k3.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.kimi-k3.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.kimi-k3.b200.agent.c1.specon.thinkoff.log) | conditional-alternative | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.kimi-k3.b200.agent.c1.specon.thinkon.log) | conditional-alternative | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.kimi-k3.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.kimi-k3.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.kimi-k3.b200.agent.c16.specon.thinkoff.log) | conditional-alternative | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.kimi-k3.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.kimi-k3.b200.agent.c16.specon.thinkon.log) | conditional-alternative | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.kimi-k3.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; Kimi-context-1048576-vs-49152; manual-multinode-required | ∅ |
| [vllm.kimi-k3.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Kimi-context-1048576-vs-49152; manual-multinode-required | ∅ |
| [vllm.kimi-k3.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c1.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: Kimi-context-1048576-vs-49152; manual-multinode-required; Kimi-TP8PP2-DSpark-unverified | ∅ |
| [vllm.kimi-k3.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c1.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; Kimi-context-1048576-vs-49152; manual-multinode-required; Kimi-TP8PP2-DSpark-unverified | ∅ |
| [vllm.kimi-k3.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; Kimi-context-1048576-vs-49152; manual-multinode-required | ∅ |
| [vllm.kimi-k3.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Kimi-context-1048576-vs-49152; manual-multinode-required | ∅ |
| [vllm.kimi-k3.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c16.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: Kimi-context-1048576-vs-49152; manual-multinode-required; Kimi-TP8PP2-DSpark-unverified | ∅ |
| [vllm.kimi-k3.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.kimi-k3.b200.lat.c16.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; Kimi-context-1048576-vs-49152; manual-multinode-required; Kimi-TP8PP2-DSpark-unverified | ∅ |
| [vllm.kimi-k3.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.kimi-k3.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; Kimi-context-1048576-vs-49152; manual-multinode-required | ∅ |
| [vllm.kimi-k3.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.kimi-k3.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Kimi-context-1048576-vs-49152; manual-multinode-required | ∅ |
| [vllm.kimi-k3.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.kimi-k3.b200.agent.c1.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: Kimi-context-1048576-vs-49152; manual-multinode-required; Kimi-TP8PP2-DSpark-unverified | ∅ |
| [vllm.kimi-k3.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.kimi-k3.b200.agent.c1.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; Kimi-context-1048576-vs-49152; manual-multinode-required; Kimi-TP8PP2-DSpark-unverified | ∅ |
| [vllm.kimi-k3.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.kimi-k3.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; Kimi-context-1048576-vs-49152; manual-multinode-required | ∅ |
| [vllm.kimi-k3.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.kimi-k3.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; Kimi-context-1048576-vs-49152; manual-multinode-required | ∅ |
| [vllm.kimi-k3.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.kimi-k3.b200.agent.c16.specon.thinkoff.log) | conditional-alternative | 0 | 0 | BLOCKED: Kimi-context-1048576-vs-49152; manual-multinode-required; Kimi-TP8PP2-DSpark-unverified | ∅ |
| [vllm.kimi-k3.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.kimi-k3.b200.agent.c16.specon.thinkon.log) | conditional-alternative | 0 | 0 | BLOCKED: coherency-think-off; Kimi-context-1048576-vs-49152; manual-multinode-required; Kimi-TP8PP2-DSpark-unverified | ∅ |
| [atlas.minimax-m2.7.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.minimax-m2.7.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m2.7.h200.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.lat.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.lat.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.agent.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.minimax-m2.7.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m2.7.h200.agent.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.lat.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.lat.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.agent.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.agent.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h100.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h100.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.lat.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.lat.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.agent.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.agent.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.8-flash-next-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-flash-next-fp8.b200.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.qwen3.8-flash-next-fp8.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-flash-next-fp8.b200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.minimax-m3.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.minimax-m3.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.minimax-m3.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.minimax-m3.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.minimax-m3.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.minimax-m3.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.minimax-m3.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.minimax-m3.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.minimax-m3.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.minimax-m3.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.minimax-m3.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.minimax-m3.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.minimax-m3.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.minimax-m3.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.minimax-m3.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [vllm.minimax-m3.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | RENDER_PASS | ∅ |
| [vllm.minimax-m3.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off | ∅ |
| [atlas.minimax-m3.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.b200.lat.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.b200.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.b200.lat.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.b200.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.b200.agent.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.b200.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.b200.agent.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.b200.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.minimax-m3.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.b200.lat.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.b200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.b200.agent.c1.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.b200.agent.c1.specon.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.b200.agent.c1.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.b200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.b200.agent.c16.specoff.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.b200.agent.c16.specon.thinkoff.log) | scoring-envelope | 0 | 0 | BLOCKED: M3-BF16-vs-PRD-NVFP4 | ∅ |
| [vllm.minimax-m3.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.b200.agent.c16.specon.thinkon.log) | scoring-envelope | 0 | 0 | BLOCKED: coherency-think-off; M3-BF16-vs-PRD-NVFP4 | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.qwen3.8-27b-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.8-27b-fp8.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | — | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c1.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c1.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c1.specon.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c16.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c16.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c16.specon.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.lat.c16.specon.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.agent.c1.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.agent.c1.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.agent.c1.specon.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.agent.c1.specon.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.agent.c16.specoff.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.agent.c16.specoff.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.agent.c16.specon.thinkoff.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [vllm.qwen3.8-27b-fp8.h200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.8-27b-fp8.h200.agent.c16.specon.thinkon.log) | scoring-envelope | 3 | 3 | BLOCKED: named-cell-missing-recipe | ∅ |
| [atlas.glm-5.3-flash.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.h100.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.glm-5.3-flash.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.lat.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.lat.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.lat.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.lat.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.agent.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.agent.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.agent.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.agent.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.h100.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.glm-5.3-flash.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3-flash.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3-flash.b200.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.glm-5.3-flash.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.lat.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.lat.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.agent.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.agent.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3-flash.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3-flash.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3-flash.b200.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.glm-5.3.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h100.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h100.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h100.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h100.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h100.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h100.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h100.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h100.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h100.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h100.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h100.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h100.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h100.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h100.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.h100.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.h100.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.glm-5.3.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h100.lat.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h100.lat.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h100.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h100.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h100.lat.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h100.lat.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h100.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h100.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h100.agent.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h100.agent.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h100.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h100.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h100.agent.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h100.agent.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.h100.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.h100.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.glm-5.3.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.b200.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.b200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.b200.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.b200.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.b200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.b200.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.b200.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.b200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.b200.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.b200.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.glm-5.3.b200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.glm-5.3.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.glm-5.3.b200.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.glm-5.3.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.b200.lat.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.b200.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.b200.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.b200.lat.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.b200.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.b200.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.b200.agent.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.b200.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.b200.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.b200.agent.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.glm-5.3.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.glm-5.3.b200.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | FAIL: blocked-GLM-think-off-accepted; policy-probe-accepted | ∅ |
| [vllm.glm-5.3.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.glm-5.3.b200.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [atlas.deepseek-v4-flash.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [atlas.deepseek-v4-flash.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.deepseek-v4-flash.h100.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.lat.c1.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.lat.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.lat.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.lat.c16.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.lat.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.lat.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.agent.c1.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.agent.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.agent.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.agent.c16.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.agent.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.deepseek-v4-flash.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.deepseek-v4-flash.h100.agent.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.nemotron-3-super-nvfp4.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.nemotron-3-super-nvfp4.b200.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.lat.c1.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.lat.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.lat.c16.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.lat.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.agent.c1.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.agent.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.agent.c16.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.nemotron-3-super-nvfp4.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.nemotron-3-super-nvfp4.b200.agent.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.lat.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c1.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specoff.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specon.thinkoff.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.qwen3.6-35b-a3b-nvfp4.b200.agent.c16.specon.thinkon.log) | policy-probe | 3 | 3 | BLOCKED | ∅ |
| [atlas.minimax-m3.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h100.lat.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h100.lat.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h100.lat.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h100.lat.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h100.lat.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h100.lat.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h100.lat.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h100.lat.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h100.agent.c1.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h100.agent.c1.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h100.agent.c1.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h100.agent.c1.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h100.agent.c16.specoff.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h100.agent.c16.specoff.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/atlas.minimax-m3.h100.agent.c16.specon.thinkoff.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [atlas.minimax-m3.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/atlas.minimax-m3.h100.agent.c16.specon.thinkon.log) | policy-probe | 3 | — | EXPECTED_UNSUPPORTED | ∅ |
| [vllm.minimax-m3.h100.lat.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.minimax-m3.h100.lat.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.minimax-m3.h100.lat.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.minimax-m3.h100.lat.c1.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.minimax-m3.h100.lat.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.minimax-m3.h100.lat.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.minimax-m3.h100.lat.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.minimax-m3.h100.lat.c16.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h100.lat.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.minimax-m3.h100.agent.c1.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h100.agent.c1.specoff.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.minimax-m3.h100.agent.c1.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h100.agent.c1.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.minimax-m3.h100.agent.c1.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h100.agent.c1.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.minimax-m3.h100.agent.c1.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h100.agent.c1.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.minimax-m3.h100.agent.c16.specoff.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h100.agent.c16.specoff.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.minimax-m3.h100.agent.c16.specoff.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h100.agent.c16.specoff.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
| [vllm.minimax-m3.h100.agent.c16.specon.thinkoff](evidence/dryrun-matrix/vllm.minimax-m3.h100.agent.c16.specon.thinkoff.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted | ∅ |
| [vllm.minimax-m3.h100.agent.c16.specon.thinkon](evidence/dryrun-matrix/vllm.minimax-m3.h100.agent.c16.specon.thinkon.log) | policy-probe | 0 | 0 | BLOCKED: policy-probe-accepted; coherency-think-off | ∅ |
