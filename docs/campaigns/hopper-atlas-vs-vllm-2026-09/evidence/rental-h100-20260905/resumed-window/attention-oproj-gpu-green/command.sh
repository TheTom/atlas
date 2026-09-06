#!/usr/bin/env bash
set -euo pipefail
umask 077
root=/workspace/atlas-rental
revision=${1:?full source revision required}
out=$root/results/diagnostic.native-fp8-oproj.$revision.build-resume01
cd "$root/src/atlas"
test "$(git rev-parse HEAD)" = "$revision"
test -z "$(git status --porcelain)"
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
assert s.free >= 20*1024**3 and s.used < 300_000_000_000, s
PY
export PATH=/root/.cargo/bin:$PATH
export CARGO_TARGET_DIR=$root/target CARGO_BUILD_JOBS=12
export ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL=qwen3.8-27b ATLAS_TARGET_QUANT=nvfp4 CUDARC_CUDA_VERSION=13000
unset ATLAS_SKIP_BUILD RUSTUP_TOOLCHAIN CUTLASS_HOME FLASHINFER_HOME
git rev-parse HEAD > "$out/source.sha"
env | sort | sed -n '/^ATLAS_TARGET_/p;/^CARGO_BUILD_JOBS=/p;/^CARGO_TARGET_DIR=/p;/^CUDARC_CUDA_VERSION=/p' > "$out/build.env"
if /usr/bin/time -v -o "$out/build.time" timeout 90 cargo +1.93.1 build --locked --release -p spark-model --features cuda,gpu-examples --example native_fp8_oproj_batch_microtest > "$out/build.stdout" 2> "$out/build.stderr"; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" > "$out/build.exit"
test "$rc" = 0
bin=$root/bin/$revision/qwen3.8-27b/examples
mkdir -p "$bin"
cp "$CARGO_TARGET_DIR/release/examples/native_fp8_oproj_batch_microtest" "$bin/"
sha256sum "$bin/native_fp8_oproj_batch_microtest" > "$out/binary.sha256"
printf '%s\0' "$bin/native_fp8_oproj_batch_microtest" > "$out/numerical.argv"
if /usr/bin/time -v -o "$out/numerical.time" timeout 120 "$bin/native_fp8_oproj_batch_microtest" > "$out/numerical.stdout" 2> "$out/numerical.stderr"; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" > "$out/numerical.exit"
nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader > "$out/tenants-after.txt"
df -h / > "$out/df-after.txt"
date -u +%FT%TZ > "$out/finished.utc"
test "$rc" = 0
test ! -s "$out/tenants-after.txt"
cat "$out/numerical.stdout"
