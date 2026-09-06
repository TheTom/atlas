#!/usr/bin/env bash
set -euo pipefail
cd /workspace/atlas-rental/src/native-fp8-ffn-kernels
export CUDA_VISIBLE_DEVICES=''
export ATLAS_SKIP_BUILD=1 CUDARC_CUDA_VERSION=13000
export CARGO_TARGET_DIR=/workspace/atlas-rental/target-cpu-checks CARGO_BUILD_JOBS=4
export ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL=qwen3.8-27b ATLAS_TARGET_QUANT=nvfp4
/root/.cargo/bin/cargo +1.93.1 test --locked -p spark-model
/root/.cargo/bin/cargo +1.93.1 clippy --locked -p spark-model --tests
/root/.cargo/bin/cargo +1.93.1 doc --locked --workspace --no-deps
/root/.cargo/bin/cargo +1.93.1 test --locked --workspace --doc
