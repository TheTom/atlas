#!/usr/bin/env bash
set -euo pipefail
umask 077
root=/workspace/atlas-rental
engine=${1:?engine required}
case "$engine" in atlas) previous=qwen38.atlas.c.lat.c1; port=8888 ;; vllm) previous=qwen38.vllm.b.lat.c1; port=8000 ;; *) exit 2 ;; esac
label=${2:?label required}
timing=${3:-off}
case "$timing" in off|native_fp8) ;; *) exit 2 ;; esac
if [ "$timing" = native_fp8 ] && [ "$engine" != atlas ]; then exit 2; fi
case "$label" in ''|*[!a-zA-Z0-9_-]*) exit 2 ;; esac
out=$root/results/benchmark.qwen38.$engine.$label
test ! -e "$out"
mkdir "$out"
export PATH=$root/vllm/bin:$PATH
export HF_HOME=$root/hf38 HF_HUB_CACHE=$root/hf38/hub CUDA_VISIBLE_DEVICES=0
python3 "$root/staging/instance_preflight.py" --expected-gpus 1 > "$out/admission.json"
nvidia-smi -q > "$out/nvidia-smi-q.txt"
df -h / > "$out/df-before.txt"
cp "$root/results/$previous/serve.argv" "$out/serve.argv"
cp "$root/results/$previous/process-env.json" "$out/process-env.json"
if [ "$timing" = native_fp8 ]; then
  python3 - "$out/process-env.json" <<'PYENV'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); d=json.loads(p.read_text()); d['ATLAS_DENSE_FP8']='1'; p.write_text(json.dumps(d,indent=2)+'\n')
PYENV
fi
cd "$root/src/atlas"
git rev-parse HEAD > "$out/harness.sha"
sha256sum "$root/bin/spark-qwen38" > "$out/available-spark.sha256"
printf '%s\n' 'User authorizes performance measurements despite a sole word-reversal error. Original coherency JSON stays unchanged; every other gate is required. Native-FP8 environment is an explicit separate precision profile, if selected. Not certified campaign data.' > "$out/RESTRICTION.txt"
python3 bench/campaign/process_endpoint.py free --url "http://127.0.0.1:$port" --out "$out/endpoint-admission.json" > "$out/endpoint-admission.log"
stop_owned() {
  task_rc=$?
  trap - EXIT INT TERM HUP
  if [ -f "$out/owner.json" ]; then
    python3 bench/campaign/process_launch.py stop --record "$out/owner.json" --timeout 15 > "$out/stop.json" 2> "$out/stop.stderr" || task_rc=2
  fi
  nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader > "$out/tenants-after.txt" || task_rc=2
  df -h / > "$out/df-after.txt"
  printf '%s\n' "$task_rc" > "$out/exit-code.txt"
  exit "$task_rc"
}
trap stop_owned EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
trap 'exit 129' HUP
start_epoch=$(date +%s)
python3 bench/campaign/process_launch.py start --record "$out/owner.json" --evidence "$out/launch.json" --log "$out/serve.log" --argv-nul "$out/serve.argv" --env-json "$out/process-env.json" --cwd "$root/src/atlas" > "$out/start.log" 2>&1
bash bench/hopper_ab/time_to_ready.sh --url "http://127.0.0.1:$port" --engine "$engine" --model Qwen/Qwen3.8-27B-FP8 --start-epoch "$start_epoch" --timeout-s 900 --process-owner "$out/owner.json" --out "$out/boot.json" > "$out/boot.log" 2>&1
python3 bench/campaign/process_endpoint.py owned --url "http://127.0.0.1:$port" --record "$out/owner.json" --out "$out/endpoint-owned.json" > "$out/endpoint-owned.log"
python3 bench/campaign/process_launch.py capture --record "$out/owner.json" --evidence "$out/launch-ready.json" > "$out/capture.log"
date -u +%FT%TZ > "$out/ready.utc"
for (( task_wait=0; task_wait<2400; task_wait++ )); do
  if [ -f "$out/requests-complete" ]; then exit 0; fi
  sleep 1
done
printf '%s\n' 'diagnostic request window exhausted' > "$out/window-expired.txt"
exit 124
