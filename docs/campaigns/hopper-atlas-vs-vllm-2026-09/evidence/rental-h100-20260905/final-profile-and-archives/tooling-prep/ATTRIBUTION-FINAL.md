# Final C4 attribution

The prepared diagnostic completed successfully on the unchanged7c binary after the final tooling admission. All17 arithmetic requests passed, actual client overlap16 was observed, the profiler captured12 n4/padded4 steps and2 n2 steps, and owned cleanup exited0. The raw result is `remote-results/diagnostic.qwen38.msprofile.msprofile01/`.

| C4 phase | Median synchronized wall time per batch step | Approximate share |
|---|---:|---:|
| All48 SSM transformer layers, including FFNs |26.165ms|68.6%|
| All16 attention transformer layers, including FFNs |11.0285ms|28.9%|
| Final normalization and BF16 head |0.951ms|2.5%|
| Sum measured by the profiler |38.1555ms|100%|

These are medians of each recorded field; independent medians need not sum exactly. The2 n2 steps had a25.8205ms median total (18.1155ms SSM,6.871ms attention,0.834ms head). They are a drain observation, not a separate controlled performance run.

The data moves priority away from further head optimization. Eliminating the entire measured head would remove only about2.5% of this instrumented step. It does not establish the effect on frozen throughput.

The next targeted investigation should split the SSM transformer block into native FP8 FFN work versus GDN projections/recurrent work, using the same original weights and C4 admission. There are three times as many SSM layers as attention layers; per-layer aggregate medians are approximately545µs versus689µs respectively. The SSM total alone therefore does not show that the recurrent SSM kernel is slow. Both buckets contain FFNs, so optimizing GDN on the basis of the68.6% share would be premature.

A useful follow-up fixture would preserve the current arithmetic oracle and record per-phase timing for native FP8 gate/up/down, GDN input/output projections, and recurrence. Compare one change at a time against the retained7c native checkpoint profile, then rerun uninstrumented C1/C16. No new profiling flags, precision change or wider active batch should be mixed into that comparison. The proven vLLM A/A control and raw cross-check should remain its external reference.

## Limits

ATLAS_MS_PROFILE synchronizes before/after each whole layer and disables multi-sequence CUDA graphs. Times include CPU launch/sync overhead and device execution; they are neither exclusive GPU times nor a projection of frozen-ladder token throughput. Only12 short C4 steps were sampled. The probe's exact arithmetic success supports this diagnostic's correctness; it does not replace original coherency outcomes or the retained word-reversal exception. No further GPU work is needed for this report.

Source points for the next phase split: `crates/spark-model/src/layers/qwen3_ssm/trait_decode_multi_seq.rs` dispatches batched GDN work at lines115–117 and FFN work later in the same whole-layer call. `trait_decode_multi_seq/ssm_batched.rs` and `ssm_batched_recurrent.rs` own the GDN projection/recurrence side. The outer profiler wraps the complete call, so it cannot separate these existing subpaths.
