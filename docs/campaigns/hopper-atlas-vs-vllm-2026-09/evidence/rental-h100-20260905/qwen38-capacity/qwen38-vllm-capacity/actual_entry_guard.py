import json
import pathlib
import sys
import types
from installed_guard import guard

catalog_path = pathlib.Path(sys.argv[1])
catalog = json.loads(catalog_path.read_text())
entries = [entry for entry in catalog["entries"] if entry["model_key"] == "qwen3.8-27b-fp8" and entry["sku"] == "h100"]
assert len(entries) == 1
entry = entries[0]
args = entry["args"]
assert args.count("--max-num-seqs") <= 1
# Inspected installed v0.28 EngineArgs H100 API-server default; see source receipt.
limit = int(args[args.index("--max-num-seqs") + 1]) if "--max-num-seqs" in args else 1024
observed_blocks = 810
print(json.dumps({"catalog": str(catalog_path), "model_key": entry["model_key"], "sku": entry["sku"], "max_num_seqs": limit, "limit_origin": "explicit recipe" if "--max-num-seqs" in args else "installed v0.28 H100 default", "observed_mamba_blocks": observed_blocks, "verdict": entry["verdict"]}), flush=True)
mode = types.SimpleNamespace(has_full_cudagraphs=lambda: True)
guard(types.SimpleNamespace(has_mamba_layers=True, num_blocks=observed_blocks), limit, mode, False)
assert min(limit * 2, 512, 8192) == 512, "graph capture ceiling changed"
assert limit >= 16, "frozen C16 workload would be capped"
print(json.dumps({"guard": "PASS", "max_num_seqs": limit, "max_cudagraph_capture_size": 512, "frozen_concurrency_max": 16, "margin_blocks": observed_blocks - limit}))
