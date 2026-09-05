#!/usr/bin/env bash
# Resumable model download queue into the SHARED HF cache ($HF_HOME, default /root/hf), so Atlas (`spark serve <hf-id>`)
# and vLLM (`vllm serve <hf-id>`) read the same bytes once. Never use --local-dir on a 300 GB disk: it duplicates weights.
# Re-run after any restart; complete files are skipped. Disk guard: skip a repo if free space < its size + 40 GiB.
export HF_HOME=${HF_HOME:-/root/hf}; mkdir -p "$HF_HOME"
. /root/env.sh
QUEUE=(
  "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 19"
  "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 31"
  "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 120"
)
for entry in "${QUEUE[@]}"; do
  r=${entry% *}; need=${entry##* }; d="$HF_HOME/done/${r//\//__}"; mkdir -p "$HF_HOME/done"
  free=$(df -BG --output=avail / | tail -1 | tr -dc 0-9)
  if [ -f "$d.complete" ]; then echo "SKIP $r (complete)"; continue; fi
  if [ "$free" -lt $((need+40)) ]; then echo "DEFER $r: need ${need}G+40G, free ${free}G"; continue; fi
  S=$(date +%s)
  until /root/venv/bin/hf download "$r" --max-workers 8; do echo "retry $r $(date -u +%T)"; sleep 30; done
  touch "$d.complete"
  echo "DONE $r $(date -u +%FT%TZ) cache=$(du -sh "$HF_HOME/hub" | cut -f1) in $(( ($(date +%s)-S)/60 )) min"
done
echo "QUEUE_DONE $(date -u +%FT%TZ)"; df -h / | tail -1
