#!/usr/bin/env bash
# Rental-node preflight: the abort rules, as checks with pass/fail. Run first, before spending on downloads.
# Usage: bash preflight_node.sh [--want-gpus N] [--want-cc 9.0] [--min-disk-gb 250]
# Exit 0 = go. Exit 1 = abort (reasons printed). Read-only; changes nothing on the host.
set -uo pipefail
WANT_GPUS=${WANT_GPUS:-1}; WANT_CC=${WANT_CC:-9.0}; MIN_DISK_GB=${MIN_DISK_GB:-250}
while [ $# -gt 0 ]; do case $1 in --want-gpus) WANT_GPUS=$2; shift 2;; --want-cc) WANT_CC=$2; shift 2;; --min-disk-gb) MIN_DISK_GB=$2; shift 2;; *) echo "unknown $1"; exit 2;; esac; done
fail=0; ok(){ echo "  ok   $*"; }; bad(){ echo "  FAIL $*"; fail=1; }; note(){ echo "  note $*"; }

echo "== GPU"
if ! command -v nvidia-smi >/dev/null; then bad "no nvidia-smi"; else
  nvidia-smi --query-gpu=index,name,compute_cap,memory.total,driver_version --format=csv,noheader
  n=$(nvidia-smi -L | wc -l | tr -d ' ')
  [ "$n" -ge "$WANT_GPUS" ] && ok "$n GPU(s) >= $WANT_GPUS" || bad "$n GPU(s) < $WANT_GPUS"
  cc=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | sort -u | tr '\n' ' ')
  [ "$(echo $cc | tr -d ' ')" = "$WANT_CC" ] && ok "compute capability $cc" || bad "compute capability '$cc' != $WANT_CC (hopper target is sm_90a, CC 9.0 only)"
  drv=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1); major=${drv%%.*}
  # Atlas links the CUDA 13 runtime: driver must be >= 580 (CUDA 13.0). A 12.x driver fails at cuInit, PTX never matters.
  [ "$major" -ge 580 ] && ok "driver $drv supports CUDA 13 (>= 580)" || bad "driver $drv < 580: cannot run a CUDA 13 binary; wrong host, abort"
  if [ "$n" -gt 1 ]; then
    echo "  topology:"; nvidia-smi topo -m 2>/dev/null | sed -n "1,$((n+1))p" | sed 's/^/    /'
    if nvidia-smi topo -m 2>/dev/null | grep -qE 'NV[0-9]+'; then ok "NVLink present"; else bad "no NVLink between GPUs (PIX/SYS only)"; fi
  fi
  busy=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l | tr -d ' ')
  [ "$busy" = 0 ] && ok "no foreign compute processes" || bad "$busy compute process(es) already on the GPUs"
fi

echo "== Host"
echo "  $(nproc) vCPU, $(free -g | awk '/^Mem:/{print $2}') GB RAM, $(. /etc/os-release; echo $PRETTY_NAME), kernel $(uname -r)"
avail=$(df -BG --output=avail / | tail -1 | tr -dc 0-9)
[ "$avail" -ge "$MIN_DISK_GB" ] && ok "disk ${avail}G free >= ${MIN_DISK_GB}G" || bad "disk ${avail}G free < ${MIN_DISK_GB}G (Super FP8 alone is 120 GiB)"
mount | grep -qE ' / .*overlay' && note "root is an overlay: nothing persists past the container. Sync results off-box continuously."
for t in python3 apt-get wget curl git tmux docker; do command -v $t >/dev/null && ok "$t present" || note "$t missing (bootstrap installs the apt ones; docker cannot be installed inside a container)"; done
ls /usr/local/cuda*/bin/nvcc 2>/dev/null | sed 's/^/  nvcc: /' || note "no nvcc (bootstrap installs cuda-toolkit-13-0)"
[ -f /etc/apt/sources.list.d/cuda.list ] && ok "NVIDIA apt repo configured" || note "no NVIDIA apt repo; bootstrap adds the keyring"
dpkg-query -W -f='${Version}\n' libnccl2 2>/dev/null | sed 's/^/  libnccl2: /' || note "no libnccl2 (bootstrap installs >= 2.28 +cuda13.0)"

echo "== Network (metadata only, no downloads)"
python3 - <<'PY' 2>&1 | sed 's/^/  /'
import urllib.request, time, json
for name,u in [("huggingface.co","https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4"),("github.com","https://api.github.com/repos/Avarok-Cybersecurity/atlas"),("nvidia apt","https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/")]:
    t=time.time()
    try: urllib.request.urlopen(u,timeout=15).read(2048); print(f"ok   {name} reachable ({(time.time()-t)*1000:.0f} ms)")
    except Exception as e: print(f"FAIL {name}: {e}")
PY

echo; [ $fail = 0 ] && echo "PREFLIGHT: GO" || { echo "PREFLIGHT: ABORT (see FAIL lines)"; exit 1; }
