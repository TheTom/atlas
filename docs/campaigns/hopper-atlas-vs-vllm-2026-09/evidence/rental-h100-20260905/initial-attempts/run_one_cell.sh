#!/usr/bin/env bash
set -euo pipefail
umask 077
root=/workspace/atlas-rental
engine=${1:?engine required}
label=${2:?label required}
workload=${3:-lat}
concurrency=${4:-1}
paired=${5:-}
case "$engine" in atlas|vllm) ;; *) exit 2 ;; esac
case "$label" in ''|*[!a-zA-Z0-9_-]*) exit 2 ;; esac
case "$workload" in lat|agent) ;; *) exit 2 ;; esac
case "$concurrency" in 1|16) ;; *) exit 2 ;; esac
out=$root/results/qwen.$engine.$label.$workload.c$concurrency
test ! -e "$out"
test ! -e "$out.runner.log"
test ! -e "$out.exit-code.txt"
export PATH=$root/vllm/bin:$PATH
export HF_HOME=$root/hf HF_HUB_CACHE=$root/hf/hub
export SPARK_BIN=$root/bin/spark VLLM_BIN=$root/vllm/bin/vllm
export CUDA_VISIBLE_DEVICES=0 W55_PROMPT_MODE=essay ATLAS_PORT=8888 VLLM_PORT=8000
python3 - <<'PY'
import datetime, json
from pathlib import Path
proof=json.loads(Path('/workspace/atlas-rental/download-proof/staging-proof.json').read_text())
assert proof['complete'] is True
assert proof['revision']=='95a723d08a9490559dae23d0cff1d9466213d989'
assert proof['repo_id']=='Qwen/Qwen3.6-35B-A3B-FP8'
assert Path('/workspace/atlas-rental/results/bootstrap/bootstrap.exit').read_text().strip()=='0'
build_exit=Path('/workspace/atlas-rental/results/bootstrap/atlas-build.exit')
if build_exit.exists():
    assert build_exit.read_text().strip()=='0'
else:
    paused=json.loads(Path('/workspace/atlas-rental/results/bootstrap/build-paused.json').read_text())
    assert paused['all_owned_build_processes_stopped'] is True
    for process in paused['after']:
        state=(Path('/proc')/str(process['pid'])/'stat').read_text().rsplit(')',1)[1].split()
        assert state[19]==process['start_ticks'] and state[0] in ('T','t'), 'Build is not paused'
deadline=datetime.datetime(2026,9,6,2,25,tzinfo=datetime.timezone.utc)
assert (deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>5460, 'Insufficient cell+export reserve'
PY
python3 "$root/staging/instance_preflight.py" --expected-gpus 1 > "$out.admission.json"
cd "$root/src/atlas"
args=(--engine "$engine" --model qwen3.6-35b-a3b-fp8 --sku h100
      --workload "$workload" --concurrency "$concurrency" --spec off --think off
      --process --model-path "$HF_HUB_CACHE/models--Qwen--Qwen3.6-35B-A3B-FP8/snapshots/95a723d08a9490559dae23d0cff1d9466213d989"
      --cell-timeout-s 2700 --out "$out" --yes)
if [ -n "$paired" ]; then
  test -f "$paired"
  args+=(--paired-artifact "$paired")
fi
date -u +%FT%TZ > "$out.started.utc"
if bash bench/campaign/run_cell.sh "${args[@]}" > "$out.runner.log" 2>&1; then
  task_cell_rc=0
else
  task_cell_rc=$?
fi
printf '%s\n' "$task_cell_rc" > "$out.exit-code.txt"
date -u +%FT%TZ > "$out.finished.utc"
nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader,nounits > "$out.tenants-after.txt"
df -h / > "$out.disk-after.txt"
exit "$task_cell_rc"
