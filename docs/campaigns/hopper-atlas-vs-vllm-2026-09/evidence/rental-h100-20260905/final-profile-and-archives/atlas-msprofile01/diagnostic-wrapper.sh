#!/usr/bin/env bash
# Explicit diagnostic only. Parent grants the exclusive GPU window.
set -euo pipefail
umask 077
label=${1:?fresh label required}
case "$label" in ''|*[!a-zA-Z0-9_-]*) exit 2 ;; esac
case "${2:-}" in
  --execute) exec timeout --signal=TERM --kill-after=30s 210s bash "$0" "$label" --bounded-worker ;;
  --bounded-worker) ;;
  *) printf '%s\n' "Prepared only: bash $0 $label --execute (240s outer cap)"; exit 0 ;;
esac
root=/workspace/atlas-rental
source=$root/src/atlas
previous=$root/results/benchmark.qwen38.atlas.native-head-lat01
out=$root/results/diagnostic.qwen38.msprofile.$label
test ! -e "$out"
mkdir "$out"
cd "$source"
# Registered through the EXIT trap below.
# shellcheck disable=SC2329
stop_owned() {
  task_rc=$?
  trap - EXIT INT TERM HUP
  if [ -f "$out/owner.json" ]; then
    python3 bench/campaign/process_launch.py stop --record "$out/owner.json" --timeout 15 > "$out/stop.json" 2> "$out/stop.stderr" || task_rc=2
  fi
  nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader > "$out/tenants-after.txt" || task_rc=2
  df -h / > "$out/df-after.txt"
  date -u +%FT%TZ > "$out/finished.utc"
  printf '%s\n' "$task_rc" > "$out/exit-code.txt"
  exit "$task_rc"
}
trap stop_owned EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
trap 'exit 129' HUP
date -u +%FT%TZ > "$out/started.utc"
cp "$0" "$out/diagnostic-wrapper.sh"
git rev-parse HEAD > "$out/harness.sha"
test "$(git rev-parse 'HEAD^{tree}')" = 072708d1df73c0bdcebf449512db7c40b61426ef
if pgrep -a -x 'rustc|cargo|nvcc|ptxas' > "$out/compiler-occupancy-before.txt"; then exit 2; else test "$?" -eq 1; fi
python3 "$root/staging/instance_preflight.py" --expected-gpus 1 > "$out/admission.json"
nvidia-smi -q > "$out/nvidia-smi-q.txt"
df -h / > "$out/df-before.txt"
python3 - "$previous" "$out" <<'PY'
from pathlib import Path
import hashlib,json,sys
old,out=map(Path,sys.argv[1:])
raw=(old/'serve.argv').read_bytes()
argv=[s.decode() for s in raw.rstrip(b'\0').split(b'\0')]
binary=Path(argv[0])
expected='/workspace/atlas-rental/bin/7c786cc50455dee52c11c3bf4097de945fbb8f6a/qwen3.8-27b/spark'
assert str(binary)==expected and binary.is_file(), 'exact measured 7c binary required'
assert hashlib.sha256(binary.read_bytes()).hexdigest()=='23efba747b5b309a1750789e1166055e9b4432e0511462da719e626cce01db64'
assert argv[argv.index('--max-batch-size')+1]=='4'
assert argv[argv.index('--lm-head-dtype')+1]=='bf16'
env=json.loads((old/'process-env.json').read_text())
assert env.get('ATLAS_DENSE_FP8')=='1'
assert 'ATLAS_MS_PROFILE' not in env
env['ATLAS_MS_PROFILE']='1'
(out/'serve.argv').write_bytes(raw)
(out/'process-env.json').write_text(json.dumps(env,indent=2)+'\n')
(out/'profile-change.json').write_text(json.dumps({'source_session':str(old),'argv_identical':True,'only_added_environment':{'ATLAS_MS_PROFILE':'1'},'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'scope':'Synchronized C4 phase attribution; graphs disabled in multi-sequence decode; not a throughput measurement or certification'},indent=2)+'\n')
PY
python3 bench/campaign/process_endpoint.py free --url http://127.0.0.1:8888 --out "$out/endpoint-admission.json" > "$out/endpoint-admission.log"
python3 "$root/concurrent_quality_probe.py" --selftest > "$out/quality-selftest.log"
start_epoch=$(date +%s)
python3 bench/campaign/process_launch.py start --record "$out/owner.json" --evidence "$out/launch.json" --log "$out/serve.log" --argv-nul "$out/serve.argv" --env-json "$out/process-env.json" --cwd "$source" > "$out/start.log" 2>&1
bash bench/hopper_ab/time_to_ready.sh --url http://127.0.0.1:8888 --engine atlas --model Qwen/Qwen3.8-27B-FP8 --start-epoch "$start_epoch" --timeout-s 90 --process-owner "$out/owner.json" --out "$out/boot.json" > "$out/boot.log" 2>&1
python3 bench/campaign/process_launch.py capture --record "$out/owner.json" --evidence "$out/launch-ready.json" > "$out/capture.log"
python3 bench/campaign/process_endpoint.py owned --url http://127.0.0.1:8888 --record "$out/owner.json" --out "$out/endpoint-before.json" > "$out/endpoint-before.log"
if pgrep -a -x 'rustc|cargo|nvcc|ptxas' > "$out/compiler-occupancy-ready.txt"; then exit 2; else test "$?" -eq 1; fi
printf '%s\0' python3 "$root/concurrent_quality_probe.py" --url http://127.0.0.1:8888 --model Qwen/Qwen3.8-27B-FP8 --out "$out/quality" > "$out/quality.argv"
if timeout --signal=TERM --kill-after=5s 60s python3 "$root/concurrent_quality_probe.py" --url http://127.0.0.1:8888 --model Qwen/Qwen3.8-27B-FP8 --out "$out/quality" > "$out/quality.log" 2>&1; then quality_rc=0; else quality_rc=$?; fi
printf '%s\n' "$quality_rc" > "$out/quality.exit"
python3 bench/campaign/process_endpoint.py owned --url http://127.0.0.1:8888 --record "$out/owner.json" --out "$out/endpoint-after.json" > "$out/endpoint-after.log"
python3 - "$out" <<'PY'
import json,re,statistics,sys
from pathlib import Path
out=Path(sys.argv[1])
rx=re.compile(r'ATLAS_MS_PROFILE n=(\d+) padded_n=(\d+): total=(\d+)us\s+ssm=(\d+)us\((\d+)L\)\s+attn=(\d+)us\((\d+)L\)\s+head=(\d+)us')
rows=[]
for line in (out/'serve.log').read_text().splitlines():
    match=rx.search(line)
    if match:
        row=dict(zip(('n','padded_n','total_us','ssm_us','ssm_layers','attention_us','attention_layers','head_us'),map(int,match.groups())))
        row['source_line']=line
        rows.append(row)
groups=[]
for n,padded in sorted({(r['n'],r['padded_n']) for r in rows}):
    selected=[r for r in rows if (r['n'],r['padded_n'])==(n,padded)]
    groups.append({'n':n,'padded_n':padded,'steps':len(selected),'median_us':{k:statistics.median(r[k] for r in selected) for k in ('total_us','ssm_us','attention_us','head_us')}})
result={'scope':'Synchronized device-inclusive wall attribution; includes CPU launch/sync overhead; not frozen throughput','bucket_meaning':{'ssm':'whole SSM transformer layers, including FFN','attention':'whole attention transformer layers, including FFN','head':'final normalization and head projection'},'rows':rows,'groups':groups,'actual_c4_observed':any(r['n']==4 and r['padded_n']==4 for r in rows)}
(out/'profile-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'groups':groups,'actual_c4_observed':result['actual_c4_observed']}))
if not result['actual_c4_observed']: raise SystemExit(2)
PY
exit "$quality_rc"
