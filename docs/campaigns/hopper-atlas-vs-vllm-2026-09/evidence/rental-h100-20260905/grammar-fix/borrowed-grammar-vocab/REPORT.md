# Borrow immutable vocabulary during cold grammar preparation

This is Spark 1 CPU evidence. It does not establish an H100 serving speedup.

Production change: `ae8c693c38bce5fdead687515765a5c6fd4bb7b6` (root cherry-pick `72834f2`). Permanent allocation regression: `ccc18def6a321273023314dec07d9bca9c2e9137` (root `cd8c119`). A separate one-line clippy cleanup is `bad683736fd17e86ac2e06754634de430a782db1`.

## Finding and minimal change

`MaskGenerator::token_mask_with_first_char_check` deep-copied the entire sorted tokenizer vocabulary and subtree index before preparing each state mask. It also copied each previous scanned token. With approximately 248,000 vocabulary entries and 123 native masks, the first copy alone implies about 30 million temporary token-buffer allocations. A mask can reject every added token by its first character and still pay those copies.

The tokenizer information is immutable external data. Copying its reference lets the scanner borrow those two slices and the previous token while mutating only its parser state. The traversal, speculative acceptance, last scanned token, masks, stopping rules, 512-mask cap and four-worker bound remain unchanged. Warm grammar factoring remains in place.

## Red-first allocation oracle

The regular integration test prepares the same three-state `root ::= "yes"` grammar with 4,096 and 8,192 additional z-prefixed vocabulary tokens. None can match any grammar state. Tokenizer construction is outside the measured region. Doubling irrelevant tokens must not increase allocation calls during preparation. The matcher must still reject irrelevant text, accept `yes`, and terminate on EOS.

Observed old source: **12,356 → 24,644 allocations**, test fails, exit 101. Observed borrowed source: **58 → 58 allocations**, test passes, exit 0. These are allocation counts, not a timing threshold. The permanent test is `crates/xgrammar/tests/vocabulary_allocations.rs`; actual red/green logs are under `cpu-phase/integration-red.log` and `validation/integration-green.log`.

The safe test API comes from [stats_alloc documentation](https://docs.rs/stats_alloc/0.1.10/stats_alloc/). The dependency is pinned to 0.1.10, dev-only, MIT licensed, has no dependencies, and its fetched source is 15,853 bytes. xgrammar's `unsafe_code = "forbid"` is preserved. The exploratory standalone allocator probe is retained separately; it is not linked into production.

## Exactness and phase observations

The real native auto/required EBNF, existing pinned Qwen tokenizer, both EOS IDs, and exact 40-token response were replayed. All 123 serial/four-worker adaptive masks agree. Every full next-token mask and rollback mask is byte-identical to the original native golden files, including after warm factoring; the accepted output and malformed required-function refusal remain unchanged. `golden-comparison.json` records equal SHA-256 hashes.

| Factored grammar CPU phase | Before borrowing | After borrowing |
| --- | --- | --- |
| Grammar compile | 10–16 ms | 10–14 ms |
| Matcher construction | 44–54 microseconds | 46–55 microseconds |
| Serial mask preparation | 2.03–2.44 seconds | 1.41 seconds |
| Four-worker mask preparation | 1.85–1.97 seconds | 1.83–2.22 seconds |
| Warm mask fill | 0.173–0.176 ms/token | 0.169–0.186 ms/token |

These are two unpinned CPU repetitions per mode on Spark 1, not scored performance. Borrowing removes demonstrated allocation work and improves the serial phase. It does **not** yet establish a four-worker wall-time improvement on the H100 host. Preserve the parent's observed H100 cold-auto range of 5.28–6.57 seconds versus the earlier 4.824-second observation; do not replace that range with a fixed regression percentage.

The H100 grammarfix01 log brackets 6.201 seconds from request-session admission to `Grammar constrained decoding active`; prompt prefill then takes about 324 ms. The CPU replay attributes the dominant preparation work to mask generation rather than EBNF compilation or matcher construction.

A proposed duplicate rule-cache computation cause was **rejected**: every observed serial/four-worker preparation computes exactly 123 distinct structural keys, with no duplicates (`compute-counts.json`). The remaining parallel cost may involve shared `Arc<GrammarData>` reference-count traffic: `earley/scan.rs`, `complete.rs`, and `predict_fsm.rs` clone that shared Arc in hot state loops. This is a source-backed hypothesis, not a measured cause; no such optimization was applied, per the parent's stop rule.

## Final checks and cleanup

On final validation commit `bad6837`, all 5,111 tracked paths on Spark 1 match their recorded hashes. Full default package tests pass: spark-server 2,456, xgrammar 826 unit tests and the new allocation integration test. Two existing xgrammar tokenizer-fixture entries also report green but returned without a tokenizer and are not claimed as native validation. The 19 existing server ignores and one xgrammar documentation ignore remain.

Workspace `cargo doc --locked --workspace --no-deps` passes. Affected-crate clippy with `-D warnings` passes after observing red on the redundant `&run` worker closure and fixing only that borrow. Formatting, typos, diff checks and SPDX headers pass. Edited Rust files are 232, 52 and 88 lines. The Hopper PTX gate passes all seven assertions, including the genuine nvcc/ptxas known-bad two-entry fixture; Spark 1 has no shellcheck, so its optional shellcheck step was explicitly skipped and the parent owns the local shellcheck gate.

Both owned Spark 1 directories were removed after exporting evidence. Disk free immediately before/after cleanup was 2.8/2.9 GB; the authorized shared Cargo target remains. No GPU work, H100 device action, GitHub write or large model download was performed by this subtask.

Stopping rule: allocation regression observed red then green; full native mask/rollback equivalence; package, rustdoc, clippy and PTX checks pass; owned source/fixture directories removed. Parent owns H100 verification of whether the cold wall-time regression is resolved.

Root final batch `e68079c7d70035b17f52af3a33ca70a61c2863c5` has identical tested crate/kernel/Cargo inputs. Its only differences from the validation checkout are the two campaign recipe JSON files owned and checked by the parent.
