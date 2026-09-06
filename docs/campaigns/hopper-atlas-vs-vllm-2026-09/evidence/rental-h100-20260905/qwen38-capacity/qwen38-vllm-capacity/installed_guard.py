# Extracted verbatim guard body from installed vLLM 0.28.0 compilation.py:1499-1514.
def guard(kv_cache_config, max_num_reqs, cudagraph_mode, is_profiling):
    if (
        kv_cache_config is not None
        and max_num_reqs is not None
        and cudagraph_mode.has_full_cudagraphs()
        and not is_profiling
        and kv_cache_config.has_mamba_layers
        and max_num_reqs > kv_cache_config.num_blocks
    ):
        raise ValueError(
            f"max_num_seqs ({max_num_reqs}) exceeds available Mamba cache "
            f"blocks ({kv_cache_config.num_blocks}). Each decode sequence "
            "requires one Mamba cache block, so CUDA graph capture cannot "
            "proceed. Please lower max_num_seqs to at most "
            f"{kv_cache_config.num_blocks} or increase "
            "gpu_memory_utilization."
        )
