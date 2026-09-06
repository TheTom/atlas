#!/usr/bin/env bash
set -euo pipefail
umask 077
root=/workspace/atlas-rental
out=$root/results/tooling.ms-profile-env.f08d4ea
cd "$root/src/atlas"
test -d "$out"
test ! -e "$out/linux-green.exit"
cp "$0" "$out/deploy-command.sh"
nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader > "$out/tenants-before-deploy.txt"
test ! -s "$out/tenants-before-deploy.txt"
df -h / > "$out/df-before.txt"
test -z "$(git status --porcelain)"
test "$(git rev-parse HEAD)" = 7c786cc50455dee52c11c3bf4097de945fbb8f6a
git rev-parse HEAD > "$out/source-before.sha"
git bundle verify "$root/f08d4ea-tooling.bundle" > "$out/bundle-verify.stdout" 2> "$out/bundle-verify.stderr"
git fetch "$root/f08d4ea-tooling.bundle" HEAD > "$out/fetch.stdout" 2> "$out/fetch.stderr"
git rebase FETCH_HEAD > "$out/rebase.stdout" 2> "$out/rebase.stderr"
test "$(git rev-parse HEAD)" = f08d4eafb3f56e2168bfc993a657191a4e424a1e
test "$(git rev-parse 'HEAD^{tree}')" = 072708d1df73c0bdcebf449512db7c40b61426ef
git diff --exit-code 7c786cc50455dee52c11c3bf4097de945fbb8f6a HEAD -- crates kernels Cargo.toml Cargo.lock vendor jinja-templates rust-toolchain.toml 3rdparty_patches > "$out/compiled-path-diff.txt"
git rev-parse HEAD > "$out/source-after.sha"
printf '%s\0' "$root/vllm/bin/python3" bench/campaign/process_launch_test.py -v > "$out/linux-green.argv"
if /usr/bin/time -v -o "$out/linux-green.time" timeout 120 "$root/vllm/bin/python3" bench/campaign/process_launch_test.py -v > "$out/linux-green.stdout" 2> "$out/linux-green.stderr"; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" > "$out/linux-green.exit"
df -h / > "$out/df-after.txt"
date -u +%FT%TZ > "$out/finished.utc"
tail -n 5 "$out/linux-green.stderr"
test "$rc" = 0
bash "$root/run_qwen38_ms_profile.sh" msprofile01 --execute
