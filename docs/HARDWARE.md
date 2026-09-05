# Adding a new hardware target or model family

Atlas's compute stack is structured around **(hardware, model, quant) tuples**.
Each tuple is a self-contained body of work: kernels are written, tuned, and
tested per-tuple. This document explains how to extend the matrix.

## Directory layout

```
kernels/
└── <hardware>/                    e.g. gb10
    ├── HARDWARE.toml              arch, sm, fp32-residual flag
    ├── <quant>/                   shared kernels for this hw + quant
    │   └── *.cu                   e.g. nvfp4/dense_gemm.cu
    └── <model>/                   per-model overrides
        ├── MODEL.toml             model_type list, sampling presets, behavior
        └── <quant>/               per-(model, quant) overrides
            └── *.cu               e.g. qwen3.6-35b-a3b/nvfp4/inferspark_prefill_h128.cu
```

The build script (`crates/atlas-kernels/build.rs`) walks this tree and
compiles every `.cu` to PTX. Model-specific files override shared
files when a name collision occurs.

## Adding a new model family

If your model is similar to an existing one (e.g., adding Qwen3.7 to the
Qwen3.5/3.6 family), the mechanical recipe is:

1. **Create the kernel target dir**:
   ```
   kernels/gb10/qwen3.7-XXB/
   ├── MODEL.toml                  copy from a similar model's MODEL.toml
   └── nvfp4/                      or fp8/ etc. depending on the quant
       └── (per-target overrides — leave empty if shared kernels suffice)
   ```

2. **Write `MODEL.toml`**:
   ```toml
   [model]
   name = "qwen3.7-XXB"
   hf_id = "Qwen/Qwen3.7-XXB"
   params = "XXB"
   active_params = "XXB"
   architecture = "Hybrid Attention + GDN + Dense FFN"

   [[model_types]]
   model_type = "qwen3_5"          # what the HF config.json says
   hidden_size = NNNN              # exact hidden dim — wins over wildcards

   # Only if ANOTHER target declares the same (model_type, hidden_size) —
   # e.g. qwen3.8-27b's config is bit-identical to qwen3.6-27b's — declare
   # checkpoint-reference needles so runtime resolution can break the tie
   # (case-insensitive substrings of the HF id / --model-name / model dir).
   # build.rs FAILS if colliding targets omit this, and a tie the needles
   # cannot break to exactly one target is a hard startup error (never a
   # build-order pick; `--kernel-target` pins explicitly). Rules + rationale:
   # crates/atlas-kernels/src/resolve.rs.
   # match_names = ["qwen3.7-XXb"]

   # Architecturally-identical sibling (zero new kernels)? Reuse another
   # target's .cu tree instead of copying it — qwen3.8-27b compiles
   # qwen3.6-27b's sources this way and ships no files of its own:
   # kernel_source = "qwen3.6-27b"

   [behavior]
   default_num_drafts = 1
   max_thinking_budget = 512
   thinking_in_tools = false

   [sampling.thinking_text]
   temperature = 0.6
   top_p = 0.95
   top_k = 20

   # ... (other sampling presets — see existing MODEL.toml files)
   ```

3. **Wire to a `WeightLoader`** in `crates/spark-model/src/factory.rs`:
   most Qwen3-family models share `Qwen35WeightLoader` for MoE and
   `Qwen35DenseWeightLoader` for dense FFN. Pick the right one based on
   whether the model has experts.

4. **Add to test sweep** (`tests/run_all_models.py`): one round per
   variant (with/without MTP, EP=2 if applicable).

5. **Build with the wildcard target**:
   ```
   ATLAS_TARGET_MODEL='*' cargo build --release -p spark-server
   ```
   The new target compiles into the binary; runtime selects it via
   `model_type` + `hidden_size` matching, with `match_names` breaking any
   tie between config-identical checkpoints (see
   `crates/atlas-kernels/src/resolve.rs`).

If your model is genuinely new (different attention pattern, novel SSM
variant, etc.), you'll also need to:
6. Write a per-architecture `TransformerLayer` impl in
   `crates/spark-model/src/layers/` (mirror the structure of
   `qwen3_attention/` or `qwen3_ssm/`).
7. Add a new `WeightLoader` in `crates/spark-model/src/weight_loader/`
   if the safetensors key naming differs from existing families.

## Adding a new hardware target

Atlas's NVIDIA targets are **GB10 (Blackwell, sm_121)** and **Hopper
(H100/H200, sm_90a)**; `strix`/`strix-hip` (AMD gfx1151) and `metal` are the
non-NVIDIA sets. Adding another — say sm_120 for a consumer Blackwell, or
sm_100 for Blackwell datacenter — requires:

1. **`kernels/<new-hw>/HARDWARE.toml`**. The keys are exactly the ones
   `crates/atlas-kernels/build.rs` reads, plus documentation:
   ```toml
   [hardware]
   name = "gb10"                   # matches the directory name
   vendor = "nvidia"               # picks the compiler: nvidia | apple | amd | hip
   arch = "sm_121f"                # forwarded verbatim to `nvcc -arch=`
   compute_capability = "12.1"     # documentation — nothing reads it
   memory_bandwidth_gbps = 273     # documentation / roofline input
   memory_type = "LPDDR5X"
   memory_gb = 120
   ```
   Only `arch` and `vendor` are load-bearing: `arch` becomes `-arch=` (and,
   with any `a`/`f` feature suffix stripped, `KernelTarget.arch`), and
   `vendor` selects the `ComputeTarget` impl in `build_target.rs` and the
   per-vendor KERNEL.toml flag key (`extra_nvcc_flags` vs
   `extra_metal_flags`). The remaining keys have **no reader anywhere in the
   repo** — they are documentation, and `kernels/strix/HARDWARE.toml` records
   what happened to two keys that pretended otherwise.

   Get the SM number right. Hopper is **sm_90** (`sm_90a` with the
   arch-specific feature set); sm_100 is Blackwell **datacenter**, sm_120 is
   consumer Blackwell, sm_121 is GB10. PTX built for an `a`-suffixed arch does
   not run forward onto a later architecture.

2. **Kernel sources**: `kernels/<new-hw>/common/` for the shared set and
   `kernels/<new-hw>/<model>/<quant>/` for per-model shadows. If the new
   target starts out compiling another target's sources unchanged, share them
   with **relative symlinks** rather than copies — see the Hopper section
   below and `kernels/strix/common/`. Where the kernels do diverge, tile
   shapes, SMEM budget and tensor-core MMA instructions are what usually
   needs tuning.

3. **`atlas-kernels/build.rs`**: usually no changes needed — the build
   script auto-discovers new `kernels/<hw>/` directories.

4. **`spark-runtime/src/cuda_backend.rs`**: if the hardware has different
   capabilities (e.g., GDS supported, no NVLink, different RDMA NIC),
   wire the relevant flags here.

5. **NCCL env**: launchers like `scripts/start-ep2.sh` hardcode
   `NCCL_SOCKET_IFNAME=enp1s0f0np0` (GB10's RDMA NIC). Update for the
   new hardware's interconnect.

6. **CI**: GitHub Actions runs on `ubuntu-latest` with `ATLAS_SKIP_BUILD=1`
   so no GPU is needed. The new target compiles via the wildcard build
   on a host with the right SM.

## The Hopper (sm_90a) target

`kernels/hopper/` is H100 and H200 — both SM 9.0. It is the worked example of
a target that ships **no kernels of its own**.

**Kernel set: inherited from gb10 by symlink.** `kernels/hopper/common/` is 181
relative symlinks into `kernels/gb10/common/` (all 171 `.cu`, the 9 `.cuh`
headers, and `KERNEL.toml`), and each of the five model targets mirrors gb10's
`nvfp4/` directory file by file the same way. Git stores them as symlinks
(mode 120000); nothing is copied. This works because the gb10 kernels are
written to an SM80-class instruction floor — `mma.sync.m16n8k16`, `cp.async.cg`,
with TMA and `cp.async.bulk` deliberately avoided — and carry no
`__CUDA_ARCH__` gating.

Per-file links, not a `[model] kernel_source` redirect: `kernel_source`
redirects a whole quant tree and only within one hardware set, whereas
replacing one link with one real file is how a Hopper-tuned kernel will later
shadow its gb10 origin without forking the other 180. `MODEL.toml` is a real
copy — sampling and behaviour are checkpoint properties that must stay
editable per hardware — and each copy's header says so, including that its
`[expected_absent]` tables were harvested on GB10 and **not** re-harvested on
Hopper (`spark serve --check-kernels` on a real H100/H200 is what would do
that).

`kernels/hopper/<model>/nvfp4/` despite Hopper having no NVFP4 datapath: the
runtime's weight-format gate is that an nvfp4-built kernel bundle also serves
FP8 and BF16 checkpoints, so Hopper FP8 checkpoints run through these kernels.
An `fp8/` directory would be a second name for the same files.

**Hopper is FP8/BF16-only.** The NVFP4 CUTLASS wrappers in
`crates/spark-runtime/cuda/cutlass_nvfp4_gemm.cu` are gated on
`CUTLASS_ARCH_MMA_SM120_SUPPORTED || CUTLASS_ARCH_MMA_SM121_SUPPORTED` and
compile to nothing for sm_90a. Serving an NVFP4 checkpoint on Hopper needs an
Sm90 block-scaled path that does not exist yet.

**The compile gate.** `scripts/hopper_ptx_gate.sh` answers "does each kernel
compile for this architecture" with nvcc alone — no H100 needed, no GPU of any
kind:

```bash
# On any CUDA host (nvcc need not be on PATH):
CUDA_HOME=/usr/local/cuda scripts/hopper_ptx_gate.sh --selftest
CUDA_HOME=/usr/local/cuda scripts/hopper_ptx_gate.sh \
  --hw hopper --model all --jobs 4 --out receipts/ptx_gate.json
```

It resolves each model's file set the way `build.rs` does (common/ overridden
by the model directory by file stem, `KERNEL.toml` flags merged common-first),
runs `nvcc --ptx -arch=<arch>` then `ptxas -arch=<arch> -v`, and writes a JSON
ledger plus a markdown summary with per-model pass/fail counts, the first error
line of every failure, and the worst register/spill numbers. It exits non-zero
if anything failed.

**What it found, 2026-09-05** (CUDA 13.0.88, receipts in
`docs/campaigns/hopper-atlas-vs-vllm-2026-09/receipts/`): **870 of 871** kernels
across the five P0 targets emit PTX and assemble for sm_90a. The one that does
not is `kernels/gb10/qwen3.6-35b-a3b/nvfp4/moe_w4a16_grouped_gemm.cu`, which
ptxas rejects with

```
Instruction 'cvt with .e2m1x2' not supported on .target 'sm_90a'
Instruction 'mma with block scale' not supported on .target 'sm_90a'
Feature '.kind::mxf4nvf4' not supported on .target 'sm_90a'
```

— the NVFP4 block-scaled MMA path, Blackwell-only by construction. It is the
same gap as the CUTLASS wrappers above, reached through a hand-written kernel
instead: qwen3.6-35b-a3b needs an Sm90 MoE grouped GEMM before it serves on
Hopper. The other four P0 targets are complete, and
`nemotron-super-120b-a12b` also passes under `--strict`, i.e. with the
`--Werror all-warnings` the real build adds.

It runs a **self-test first, always**: one fixture that must compile for any
arch and one that must NOT compile for this one
(`scripts/fixtures/hopper_gate/`). If either verdict is wrong the gate refuses
to report results. A gate whose failure path has never executed is not
evidence — and the negative fixture is arch-specific, so pointing the gate at
the architecture the fixture happens to be valid on is itself caught.

Compilation is not correctness. A green gate says these kernels exist for
sm_90a; it says nothing about whether they produce the right numbers or run
well. Receipts live in `docs/campaigns/`.

## Adding a new quantization scheme

Atlas supports NVFP4 (E2M1 + FP8 scales), FP8 block-scaled, BF16 raw.
To add a new scheme (e.g., MX4, INT4):

1. **`crates/atlas-core/src/config.rs`**: extend the quant detection
   logic to recognize the new format from `quantization_config` in
   `config.json`.
2. **`crates/spark-model/src/weight_map/`**: add a loader function
   that produces the right `QuantizedWeight` variant.
3. **Per-model kernels**: write `*.cu` for the new quant under
   `kernels/gb10/<model>/<new-quant>/`. The build script auto-picks them.
4. **Dispatch**: `crates/spark-model/src/layers/<layer>/` per-quant
   branches in the forward path.

## Testing a new target

Once compiled:

```bash
# Smoke test
docker run --gpus all --ipc=host -p 8888:8888 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  atlas-gb10:latest \
  serve <new-model-hf-id> --max-seq-len 4096 --max-batch-size 1

curl http://localhost:8888/v1/chat/completions -d '{"model":"...","messages":[{"role":"user","content":"hi"}]}'

# Coherence + tool calls + long context
python3 tests/single_gpu_suite.py --url http://localhost:8888 --model <new-model-hf-id>

# Regression sweep
python3 tests/run_all_models.py
```

The sweep harness saves per-model JSONs to `tests/all_models_results/`
that you can diff against the pre-merge baseline (`tests/all_models_results.pre-refactor/`).

## Reference implementations

When in doubt, copy from a model with similar arch:

| New model is... | Look at |
|---|---|
| Hybrid SSM + attention MoE | `qwen3.5-35b-a3b/`, `qwen3.6-35b-a3b/` |
| Hybrid SSM + attention dense | `qwen3.5-27b/`, `qwen3.6-27b/` |
| Pure Mamba2 + MoE | `nemotron-3-nano-30b-a3b/` |
| Pure attention + MoE | `mistral-small-4/`, `minimax-m2-229b/` |
| Pure attention dense | `gemma-4-31b/` |
| Vision-language | `qwen3-vl-30b-a3b/` |
