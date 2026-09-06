import importlib.util
import json
import pathlib
import sys

repo = pathlib.Path(sys.argv[1])
catalog_path = pathlib.Path(sys.argv[2])
config_path = pathlib.Path(sys.argv[3])
sys.path.insert(0, str(repo / "bench/campaign"))
spec = importlib.util.spec_from_file_location("atlas_render", repo / "bench/campaign/atlas_render.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
doc = json.loads(catalog_path.read_text())
entry = renderer.find(doc, "qwen3.8-27b-fp8", "h100")
assert entry is not None
args = renderer.build_args(doc, entry, "off", "off")
def value(flag):
    assert args.count(flag) == 1, flag
    return args[args.index(flag) + 1]
bs = int(value("--max-batch-size"))
assert value("--max-num-seqs") == "128"
assert value("--gpu-memory-utilization") == "0.90"
assert value("--enable-prefix-caching") == "true"
assert value("--kv-cache-dtype") == "fp8"
assert value("--kv-high-precision-layers") == "auto"
assert value("--max-seq-len") == "24576"
assert value("--fp8-kv-calibration-tokens") == "256"
assert "--speculative" not in args
# These three values are unchanged CLI/SSOT defaults, verified in source receipts.
cache_slots, rollback_slots, chunk = 16, 8, 8192
c = json.loads(config_path.read_text())["text_config"]
layers = c["layer_types"].count("linear_attention")
attn_layers = c["layer_types"].count("full_attention")
h = c["linear_num_value_heads"] * c["linear_value_head_dim"] * c["linear_key_head_dim"] * 4
key_dim = c["linear_num_key_heads"] * c["linear_key_head_dim"]
value_dim = c["linear_num_value_heads"] * c["linear_value_head_dim"]
conv_dim = 2 * key_dim + value_dim
conv = conv_dim * c["linear_conv_kernel_dim"] * 4
blob = layers * (h + conv)
gdn = chunk * (conv_dim * 2 + c["linear_num_value_heads"] * 2 * 4 + value_dim * 2 + value_dim * 2)
components = {"base_ssm": bs * blob, "decode_rollback": rollback_slots * bs * blob, "prefix_snapshots": cache_slots * blob, "gdn_two_phase": gdn, "cuda_headroom": 512 * 2**20}
reserve = sum(components.values())
assert sum([32 * blob, rollback_slots * 32 * blob, cache_slots * blob, gdn, 512 * 2**20]) // 2**20 == 46923, "must reproduce observed initial reserve"
# Logs display one decimal GiB. Charge the upper pre-KV endpoint and lower
# utilization-budget endpoint; do not credit a smaller batch's arena saving.
pre_kv_upper = int(57.25 * 2**30)
budget_lower = int(71.25 * 2**30)
kv_budget = max(0, budget_lower - pre_kv_upper - reserve)
# Actual log: 4/16 boundary attention layers BF16, the remaining12 FP8.
bf16_layers = 4
kv_bytes_per_token = 2 * c["num_key_value_heads"] * c["head_dim"] * ((attn_layers - bf16_layers) + 2 * bf16_layers)
block_tokens = 16
block_bytes = block_tokens * kv_bytes_per_token
kv_blocks = kv_budget // block_bytes
# One permanent dummy block is excluded from usable capacity.
usable_tokens = max(0, kv_blocks - 1) * block_tokens
workloads = {}
for name, isl, osl in [("lat", 1024, 256), ("agent", 4096, 512)]:
    for concurrency in [1, 16]:
        active = min(bs, concurrency)
        tokens = active * (isl + osl)
        workloads[f"{name}.c{concurrency}"] = {"offered_concurrency": concurrency, "active_ceiling": active, "queued_at_full_admission": concurrency - active, "kv_tokens": tokens, "kv_bytes": tokens * kv_bytes_per_token, "fits": tokens <= usable_tokens}
worst_context_tokens = bs * int(value("--max-seq-len"))
receipt = {"catalog": str(catalog_path), "max_batch_size": bs, "queue_channel_capacity": 128, "ssm_layers": layers, "h_bytes_per_layer": h, "conv_bytes_per_layer": conv, "ssm_blob_bytes": blob, "reserve_components_bytes": components, "inference_reserve_bytes": reserve, "inference_reserve_GiB": reserve / 2**30, "pre_kv_upper_GiB": 57.25, "budget_lower_GiB": 71.25, "kv_budget_lower_bytes": kv_budget, "kv_budget_lower_GiB": kv_budget / 2**30, "kv_bytes_per_token": kv_bytes_per_token, "kv_block_bytes": block_bytes, "kv_blocks_lower": kv_blocks, "kv_usable_tokens_lower_after_dummy": usable_tokens, "workloads": workloads, "all_active_at_max_context_tokens": worst_context_tokens, "all_active_at_max_context_fits": worst_context_tokens <= usable_tokens}
print(json.dumps(receipt, indent=2), flush=True)
assert kv_budget > 0, "no KV budget after real inference reserve"
assert all(w["fits"] for w in workloads.values()), "frozen ladder active requests exceed available paged KV capacity"
assert worst_context_tokens <= usable_tokens, "all active requests at declared context exceed available paged KV capacity"
print("PASS: declared active batch, both frozen ladders and four full contexts fit the conservative capacity model; fresh GPU boot remains unproven")
