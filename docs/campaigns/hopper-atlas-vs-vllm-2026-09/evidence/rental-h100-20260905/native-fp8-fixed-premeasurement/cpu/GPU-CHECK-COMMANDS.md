# Existing native FP8 numerical examples

Prepared only. Run after the parent grants the GPU lease and verifies the Atlas destination. Replace `FINAL_HEAD` with the exact combined clean source head in the rental checkout. Do not use the CPU stub target for this build.

```sh
cd /workspace/atlas-rental/src/atlas
export PATH=/root/.cargo/bin:$PATH
export CARGO_TARGET_DIR=/workspace/atlas-rental/target CARGO_BUILD_JOBS=4
export ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL=qwen3.8-27b ATLAS_TARGET_QUANT=nvfp4
export CUDARC_CUDA_VERSION=13000
unset ATLAS_SKIP_BUILD RUSTUP_TOOLCHAIN CUTLASS_HOME FLASHINFER_HOME
# Require: git rev-parse HEAD = FINAL_HEAD and git status --porcelain is empty.
# Record df -h / and nvidia-smi before/after. Require >=20 GiB free and <300 GB task usage.
cargo +1.93.1 build --locked --release -p spark-model --features cuda,gpu-examples \
  --example w8a16_microtest --example w8a16_gemv_batch4_microtest
```

The two exact built paths are `/workspace/atlas-rental/target/release/examples/w8a16_microtest` and `/workspace/atlas-rental/target/release/examples/w8a16_gemv_batch4_microtest`. Copy them into the parent's source-revision-specific binary directory and capture SHA256 before using them. Preserve the source head, selected environment, build argv, exit, stdout/stderr and `/usr/bin/time -v` output. The existing `spark` executable is not replaced by this example-only build.

After all serving processes are stopped and `nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader` is empty, run the following against the copied binaries, keeping stdout/stderr/exit/time per command. These shapes bound CPU-reference cost while testing multiple 128-K scale blocks and the M tile tail.

```sh
# Known-bad configuration, expected exit1 before any GPU context is created:
./w8a16_microtest w8a16_gemm_pipelined 129 512 129 0x51A7
# Reference base and existing pipelined kernels, same random inputs and precision:
./w8a16_microtest w8a16_gemm 129 512 2048 0x51A7
./w8a16_microtest w8a16_gemm_pipelined 129 512 2048 0x51A7
# Small-M tiled fallback boundary, distinct from batch4:
./w8a16_microtest w8a16_gemm_pipelined 5 512 2048 0x51A7
# Existing batch4 and batch16 equivalence to repeated C1 GEMV:
./w8a16_gemv_batch4_microtest
```

The invalid K test proves the example's shape refusal only; it is not a known-bad numerical corruption. The GEMM example's independent CPU recompute preserves the two-level FP32 block fold; acceptance requires finite cosine >=0.9995. The GEMV example compares with the existing C1 kernel at M=4,8,16 using N512/K2048, accepting cosine >0.99999 (read output for max absolute difference too). Do not claim bit equality merely from cosine. GPU runtimes printed by the existing examples are shape-specific microbenchmarks, not full-model throughput or a certified campaign pair. After numerical checks, a fresh model boot/coherency and bounded warm C4 probe should precede another expensive full C16 ladder.
