# Existing BF16 batch GEMV numerical check

Parent owns the GPU lease and execution. These are preparation commands, not observed results.

```sh
cd /workspace/atlas-rental/src/atlas
env -u ATLAS_SKIP_BUILD ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL=qwen3.8-27b ATLAS_TARGET_QUANT=nvfp4 CUDARC_CUDA_VERSION=13000 CARGO_TARGET_DIR=/workspace/atlas-rental/target CARGO_BUILD_JOBS=12 /root/.cargo/bin/cargo +1.93.1 build --locked --release -p spark-model --features cuda,gpu-examples --example dense_gemv_bf16_batchm_microtest
/workspace/atlas-rental/target/release/examples/dense_gemv_bf16_batchm_microtest
```

The existing example compares M=1,2,4 against repeated C1 BF16 GEMV bit for bit at three shapes: (N,K)=(9216,3072),(3072,9216),(1024,3072). It does not cover the full Qwen vocabulary head or compare against the old scalar GEMM accumulation order. Its output must not be presented as full-model equivalence. Follow with the unchanged 17 arithmetic requests (C1 plus 16 concurrent), coherency checks and frozen latency C16 before reporting an improvement. Original weights and activations remain BF16; a different reduction order from scalar GEMM can still change rounding.

CPU negative input is the original production dispatch: M=1 selected scalar handle 51966 rather than existing batched handle 48918, test exit101. Unsupported M=9/16, missing handle, opt-out and unaligned K=130 retain the scalar path. The existing ops MAX_M refusal remains unchanged. GPU numerical comparison is pending parent execution.
