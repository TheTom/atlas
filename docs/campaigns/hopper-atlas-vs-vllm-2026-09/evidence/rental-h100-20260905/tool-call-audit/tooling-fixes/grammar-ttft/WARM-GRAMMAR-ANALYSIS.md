# Single-H100 diagnostic: cold and warm grammar cost

Source inspected: Atlas `57d9c1cfbaf851afa1255653aba80715681ae058`. These are diagnostic observations and hypotheses, not scored A/B results. No grammar or engine behavior changed in this analysis.

The parent observed fixed-build auto tool first output at 4.935 s cold (engine service TTFT 4.890 s), then 0.115 s for the identical warm request. Required mode was 1.359 s cold and 0.104 s warm. All returned valid tool calls. Tool decode was approximately 56 tokens/s, versus approximately 235 for plain Atlas and 275 for vLLM tools in these short diagnostics. The prior TTFT accounting fix makes cold preparation visible; it does not accelerate it.

## What executes on every grammar token

`crates/spark-server/src/scheduler/decode_logits_step.rs:132` makes any grammar-bearing sequence in the batch use the host sampling path. Plain eligible greedy rows can use GPU argmax. At a 248k vocabulary, one BF16 row transfers about 496 KB from device, then expands to about 992 KB of FP32 on the CPU (`decode_logits_seq.rs:40`). The copy timing includes waiting for the GPU forward pass, so a large copy timer alone does not prove PCIe bandwidth is the cause.

The host pipeline computes the current grammar bitmask, applies it, performs the B1 top-two scan, and applies penalties. `GrammarState` already caches a fill within one matcher position: forced-token, grammar application and EOS checks reuse that fill. Removing or skipping fills would be an incorrect proposed fix. Warm compiled masks also do not imply zero fill cost: `crates/xgrammar/src/matcher/fill.rs` combines all live scanable states, resolves uncertain tokens through reversible Earley-parser trials, and builds the final mask for each position.

`crates/spark-runtime/src/sampler/sample_impl.rs:47` then allocates and copies another full FP32 logits vector. Temperature zero bypasses the subsequent sort/softmax, so those are not implicated in this request. The greedy helper deliberately resolves ties to the last index, whereas the other argmax helper uses the first; replacing one with the other would change outputs.

## First measurement and stopping rule

Use only the already documented `ATLAS_DECODE_TIMING=1` through the owned launcher (allowlist patch a6e3e35). Run three identical 41-token warm tool responses so the existing 100-host-token summary fires. Inspect `copy+fwd-wait` versus `sample(248k host)`; preserve all request payloads and normal grammar/recipe flags. `ATLAS_MTP_TIMING=1` alone does not produce a summary when speculative decoding is off, despite collecting some grammar timings.

If sample dominates, collect a CPU call-stack profile or narrow diagnostic timings for grammar fill versus FP32 conversion/copy, B1 and greedy sampling before choosing a patch. If copy+forward wait dominates, measure CUDA forward versus synchronization separately before attempting a CPU-mask optimization. Stop this diagnostic after a stable attribution; do not change the scoring workload or suppress grammar for a faster number.

## Ranked optimization candidates

1. **Recurring warm host overhead.** The approximate tool-versus-plain excess is about 13 ms per token. Attribute it first. A future GPU mask+sampling path could avoid full-logit transfers, but must preserve all pipeline masks, penalties, forced-token behavior, logprobs, and host tie/NaN rules. This is not a safe one-line fast path. Smaller candidates are an FP32 slice sampling entry point that avoids the redundant vector copy, and skipping the B1 scan when outside a parameter body (where its result has no consumer). Each needs a production-path red test and measured payoff.
2. **Cold serial mask preparation.** `GrammarState::build` calls `compile_top_k_masks(512)` synchronously before prefill. `compiled_grammar.rs:363` computes the selected states serially. `get_or_compute_mask` performs expensive scans outside both cache mutexes, so bounded parallel execution of the same selected mask set is a plausible generic speedup. Keep all selected masks, wait before first sample, and test bit-for-bit mask equality, accepted/rejected continuations and rollback against the serial path. Profile compilation versus mask warmup before claiming the whole 4.8 s is warmup. The compiler's `max_threads` field is retained only for API parity and does not currently parallelize this loop.
3. **Overlap only.** Moving the same warmup onto a worker while GPU prefill runs preserves the work, but can hide only the available prefill duration. On this short prompt that appears to be roughly 0.1 s, so overlap alone cannot remove a multi-second cold stall. For long prompts it may be more useful. Any bounded worker pool must avoid monopolizing the shared host-sampling pool while other requests decode.

No engine optimization was implemented, no GPU request was sent by this agent, and no threshold or grammar-mask count changed.
