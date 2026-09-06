#!/usr/bin/env bash
set -euo pipefail
umask 077
root=/workspace/atlas-rental
revision=${1:?revision required}
cd "$root/src/atlas"
test "$(git rev-parse HEAD)" = "$revision"
test -z "$(git status --porcelain)"
out=$root/results/diagnostic.native-fp8-kernels.$revision
test ! -e "$out"
mkdir "$out"
cp "$0" "$out/command.sh"
nvidia-smi -q > "$out/nvidia-smi-before.txt"
nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader > "$out/tenants-before.txt"
test ! -s "$out/tenants-before.txt"
df -h / > "$out/df-before.txt"
python3 - <<'PY'
import shutil
s=shutil.disk_usage('/workspace')
assert s.free >= 20 * 1024**3 and s.used < 300_000_000_000, s
PY
export PATH=/root/.cargo/bin:$PATH
export CARGO_TARGET_DIR=$root/target CARGO_BUILD_JOBS=6
export ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL=qwen3.8-27b ATLAS_TARGET_QUANT=nvfp4 CUDARC_CUDA_VERSION=13000
unset ATLAS_SKIP_BUILD RUSTUP_TOOLCHAIN CUTLASS_HOME FLASHINFER_HOME
git rev-parse HEAD > "$out/source.sha"
env | sort | sed -n '/^ATLAS_TARGET_/p;/^CARGO_BUILD_JOBS=/p;/^CARGO_TARGET_DIR=/p;/^CUDARC_CUDA_VERSION=/p' > "$out/build.env"
if /usr/bin/time -v -o "$out/build.time" cargo +1.93.1 build --locked --release -p spark-model --features cuda,gpu-examples --example w8a16_microtest --example w8a16_gemv_batch4_microtest > "$out/build.stdout" 2> "$out/build.stderr"; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" > "$out/build.exit"
test "$rc" = 0
bin=$root/bin/$revision/qwen3.8-27b/examples
mkdir -p "$bin"
cp "$CARGO_TARGET_DIR/release/examples/w8a16_microtest" "$CARGO_TARGET_DIR/release/examples/w8a16_gemv_batch4_microtest" "$bin/"
sha256sum "$bin/w8a16_microtest" "$bin/w8a16_gemv_batch4_microtest" > "$out/binaries.sha256"
run_case() {
  label=$1
  expected=$2
  shift 2
  printf '%s\0' "$@" > "$out/$label.argv"
  nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader > "$out/$label.tenants-before"
  if /usr/bin/time -v -o "$out/$label.time" timeout 180 "$@" > "$out/$label.stdout" 2> "$out/$label.stderr"; then case_rc=0; else case_rc=$?; fi
  printf '%s\n' "$case_rc" > "$out/$label.exit"
  printf '%s exit=%s expected=%s\n' "$label" "$case_rc" "$expected"
  test "$case_rc" = "$expected"
}
# This red input proves shape validation only; numerical accuracy has separate
# existing CPU-reference and repeated-C1 GPU oracles in the examples below.
run_case shape-red 1 "$bin/w8a16_microtest" w8a16_gemm_pipelined 129 512 129 0x51A7
run_case base-reference 0 "$bin/w8a16_microtest" w8a16_gemm 129 512 2048 0x51A7
run_case pipelined-tail 0 "$bin/w8a16_microtest" w8a16_gemm_pipelined 129 512 2048 0x51A7
run_case pipelined-small 0 "$bin/w8a16_microtest" w8a16_gemm_pipelined 5 512 2048 0x51A7
run_case batch-equivalence 0 "$bin/w8a16_gemv_batch4_microtest"
nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader > "$out/tenants-after.txt"
df -h / > "$out/df-after.txt"
date -u +%FT%TZ > "$out/finished.utc"
