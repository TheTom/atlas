# H100 tool grammar repair

This continues [the original tool-call audit](RENTAL-H100-TOOL-CALLS.md) and [issue 910](https://github.com/Avarok-Cybersecurity/atlas/issues/910). For the Qwen3.6 diagnostic checkpoint, warm tool decoding improved from about 56 to 169–179 tokens/s in the final diagnostic. Restoring serial cold preparation then produced a 3.379 s first tool delta in one fresh H100 session. Cold latency remains much higher than the earlier vLLM diagnostic, and the existing word-reversal coherency failure remains. These are diagnostic results, not certified ladder scores.

## Reproduction and change

The original H100 trace at `f66a262` reports 13.78 ms/token in host sampling and 4.11 ms/token in GPU forward wait plus copy. An optimized replay on the separate Spark1 CPU localizes most mask work to parameter-value entry. The masks are already cached: the expensive state still needs contextual trials for 131,686 vocabulary entries. This is not simply a missing prewarm entry.

The native XML grammar used `value ::= leading_ws first_content rest`. Factoring the same language through `nonempty_value ::= first_content rest` lets the existing grammar optimizer inline the first-content rule into the scanner. Constraints remain active for auto, required and named tool choice. A separate change bounds synchronous cold mask preparation to four workers and starts no workers for already cached masks.

| Oracle | Known-bad observation | Fixed observation | Scope |
|---|---|---|---|
| Production value-entry state avoids contextual trials | One trial; test exits 101 | Zero; 88 focused grammar tests pass | CPU production builder |
| Accepted language and rollback remain identical | Original grammar retained as reference | Complete vocabulary masks identical across all 40 response positions and rollback; both EOS IDs | CPU pinned tokenizer |
| Empty-value and closing policy retained | Malformed keys, leading `<=>`, empty/whitespace-only values and merged tokens exercised | All four empty/force-close combinations pass | CPU regression suite |
| Cold workers overlap and stay bounded | Serial dispatcher fails overlap oracle | Bounded dispatch and cached zero-job tests pass | CPU xgrammar |
| Integration remains intact | Red tests recorded before implementation | 2,456 default server tests pass; 19 ignored; workspace doctests and rustdoc pass | Combined crate tree |

The optimized native CPU replay averages 6.728 → 0.172 ms/token for auto and 6.624 → 0.167 for required. The fixed values are from EBNF exported by the actual production builder. The original full masks match byte-for-byte. These CPU ratios do not establish an end-to-end H100 speedup.

Cold prewarm alone was less substantial: three fresh-process pairs on Spark1 gave median 2,194.670 → 1,342.347 ms for auto and 2,188.479 → 1,754.847 ms for required. Different phases and CPU hosts must not be pooled with server TTFT.

## Runtime validation

Combined source `ff7518071b1cbab18c5436ed4554e9a121b882b2` built on the H100 in 5m43s using the existing Hopper/Qwen3.6/NVFP4 selector, compiling 173 PTX modules. Binary SHA256 is `d292e71b416ca93c694eb0ac0754d018549e2789238e5d25f5c9ee5652341c78`; the predecessor remains preserved. Two fresh owned sessions repeated the identical plain plus four tool streams with decode timing enabled. All ten probes and the first session's additional twelve typed tool checks passed.

| H100 diagnostic | Original f66a262 | Fixed first session | Fixed second session |
|---|---:|---:|---:|
| Plain first visible content |0.0775 s|0.0786 s|0.0786 s|
| Cold first tool delta |4.8243 s|6.5667 s|5.2794 s|
| First repeated tool: first delta |0.1109 s|0.1091 s|0.1121 s|
| First repeated tool: complete call |0.7984 s|0.3173 s|0.3213 s|
| Host sample cost |13.78 ms/token|1.55–1.68 ms/token across matrix|separate raw trace retained|
| GPU forward wait plus copy |4.11 ms/token|4.16–4.21 ms/token|separate raw trace retained|
| Tool response rate reported by engine |about56 tokens/s|about163–176 tokens/s|about162–177 tokens/s|

Warm decode improved substantially. Cold first-schema latency was slower in these two observations. Subsequent fully cached prompts still trigger roughly 0.31 s internal prefill time, retained as a separate finding. The two sessions stopped with exit 0. Immediate device teardown snapshots briefly retained the stopped owned PID as `[No data]`; later successful fresh tenant queries were empty.

## Cold follow-through and stopping result

CPU phase inspection found a separate allocation defect: each prewarmed state copied the full sorted vocabulary and its token buffers. Borrowing immutable tokenizer slices and the previous token removes that work without changing the grammar, masks, 512-state cap or trial decisions. The permanent CPU allocation oracle doubled unrelated vocabulary from 4,096 to 8,192 tokens: old code increased allocations from 12,356 to 24,644 and failed; fixed code stayed at 58 and passed. Complete native response-position and rollback masks still match the original grammar. The final package checks passed 826 xgrammar unit tests plus the allocation integration test, 2,456 server tests, rustdoc, clippy and the seven-case CPU PTX suite. See [the CPU receipt](evidence/rental-h100-20260905/grammar-fix/borrowed-grammar-vocab/receipt.json).

That mechanism repair alone did not establish a cold H100 speedup. At `e68079c7`, the first tool delta was 5.744 s, inside the earlier four-worker range of 5.279–6.567 s. Optimized Spark1 CPU preparation also favored serial execution after the copy removal: about 1.41 s serial versus 1.83–2.22 s with four workers. This CPU evidence motivated restoring the engine's historical one-worker default; the bounded compiler API and its parallel correctness tests remain, as do the borrowed input and warm grammar factoring. No recipe, grammar constraint, mask limit or benchmark threshold was relaxed.

| Fresh H100 session | Source | Cold first tool / complete call | First repeat: first tool / complete call | Timing / typed tool oracles |
|---|---|---:|---:|---|
| `diagnostic.atlas.coldfix01`, borrowed input, four workers | `e68079c7` | 5.744018 / 5.939224 s | 0.106525 / 0.307480 s | 5/5 valid streams; 12/12 valid typed calls |
| `diagnostic.atlas.serialfix01`, borrowed input, one worker | `37228e85` | 3.378614 / 3.572566 s | 0.106280 / 0.306172 s | 5/5 valid streams; 12/12 valid typed calls |

The final stream reports engine decode rates of 169–179 tokens/s, with a 0.0767 s plain first-content control. Both sessions passed the first-token boot gate and stopped successfully. Their complete commands, environment, ownership, SSE chunks and typed responses are in the [runtime manifest](evidence/rental-h100-20260905/grammar-fix/runtime/MANIFEST.json). The final 3.379 s cold observation is lower than the original 4.824 s diagnostic and both four-worker repetitions; one observation is insufficient to estimate a cold latency distribution or isolate every change in the combined build. It remains far above the earlier approximately 0.164 s vLLM first-tool observation, which also used a different rendered prompt length. No additional cold iterations are planned for this rental.

| Source used to build Qwen3.6 | Actual executed binary SHA256 | Build evidence |
|---|---|---|
| `e68079c7d70035b17f52af3a33ca70a61c2863c5` | `d5f43d216a091f844856a5cd8816a9605d9075344a5f7f553d80a692acd5fc98` | [build command](evidence/rental-h100-20260905/grammar-fix/runtime/builds/e68079c7d70035b17f52af3a33ca70a61c2863c5/qwen3.6-35b-a3b/build.json), [activation](evidence/rental-h100-20260905/grammar-fix/runtime/builds/e68079c7d70035b17f52af3a33ca70a61c2863c5/qwen3.6-35b-a3b/activation.json) |
| `37228e85a72230e3857dbbb6c8d3286793793887` | `e2c1a9777b3ad4e38d58314d2bd30a0f8c37b3d1dd96d3d0a10cf6e9de062b18` | [build command](evidence/rental-h100-20260905/grammar-fix/runtime/builds/37228e85a72230e3857dbbb6c8d3286793793887/qwen3.6-35b-a3b/build.json), [activation](evidence/rental-h100-20260905/grammar-fix/runtime/builds/37228e85a72230e3857dbbb6c8d3286793793887/qwen3.6-35b-a3b/activation.json) |

These are source-build receipts paired with the owned process's binary hash; they do not fill an engine-declared Git field with the harness SHA. Both target `hopper / qwen3.6-35b-a3b / nvfp4`, serving the same pinned FP8 snapshot `95a723d08a9490559dae23d0cff1d9466213d989`, with diagnostic decode timing enabled. The 37.22 s final incremental build and successful Qwen3.6 probes do not certify the separate Qwen3.8 MMQ repair; that model requires its own audit, boot and coherency evidence.

Known-bad evidence and full CPU logs for the allocation repair and serial-default decision are indexed in the [cold follow-up manifest](evidence/rental-h100-20260905/grammar-fix/COLD-FOLLOWUP-EVIDENCE-MANIFEST.json). The speculative duplicate-cache-key explanation was rejected: all 123 generated keys were distinct in the profiled cold preparation. Shared grammar reference-count contention remains an untested hypothesis, not a finding of cause.

[Raw runtime files and checksums](evidence/rental-h100-20260905/grammar-fix/runtime/MANIFEST.json) retain commands, environment, boot/ownership, complete requests/JSON/SSE, build identity and logs. These per-request diagnostic rates are not pooled ladder percentiles.

CPU raw logs, source manifests, original/fixed grammar, full mask goldens, red/green outputs and checksums are under [grammar-fix evidence](evidence/rental-h100-20260905/grammar-fix/CPU-EVIDENCE-MANIFEST.json). Public tokenizer copies remain in local evidence and are represented by hashes to avoid duplicating model assets in Git.

Subsequent Qwen3.8 MMQ runtime recovery, first latency measurements and published source `fd65fb8` are summarized in [the current rental report](RENTAL-H100-REPORT.md). The later full CPU receipt clarifies that 829 reported xgrammar passes include two optional-tokenizer entries that returned early, and workspace doctests executed zero tests with two ignored. Previously recorded complete native masks and rollback evidence above remain the native replay oracle; the later broad command does not add another replay.
