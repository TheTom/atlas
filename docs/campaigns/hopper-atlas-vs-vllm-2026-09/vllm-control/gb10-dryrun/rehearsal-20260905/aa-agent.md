### ISL 4096 / OSL 512 (temp 0.0, seed 42)

| C | Atlas tok/s | vLLM tok/s | ratio | Atlas TTFT p50/p99 ms | vLLM TTFT p50/p99 ms | Atlas TPOT p50 ms | vLLM TPOT p50 ms | rung |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 45.16 | 48.25 | 0.94x | 851 / 851 | 181 / 181 | 20.52 | 20.41 | **LOSS** |
| 16 | 177.74 | 226.61 | -- | 6137 / 11065 | 842 / 1387 | 76.25 | 68.02 | **INVALID** |

0/1 rungs won.

C=16 vllm: rep 1: vacuity (a request returned <80% of OSL 512)
