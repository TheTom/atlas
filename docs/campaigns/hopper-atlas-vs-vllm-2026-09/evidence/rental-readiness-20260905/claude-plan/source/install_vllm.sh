#!/usr/bin/env bash
# vLLM control engine via pip (no docker in this container). Idempotent.
set -uo pipefail
. /root/env.sh
[ -x /root/.local/bin/uv ] || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=/root/.local/bin:$PATH
[ -d /root/vllm-venv ] || uv venv /root/vllm-venv --python 3.12
S=$(date +%s)
uv pip install --python /root/vllm-venv/bin/python vllm 2>&1 | tail -5
/root/vllm-venv/bin/python -c "import vllm,torch;print('vllm',vllm.__version__,'torch',torch.__version__,'cuda',torch.version.cuda,'sm',torch.cuda.get_device_capability(0))"
echo "VLLM_INSTALL_EXIT=$? in $(( $(date +%s)-S ))s"
