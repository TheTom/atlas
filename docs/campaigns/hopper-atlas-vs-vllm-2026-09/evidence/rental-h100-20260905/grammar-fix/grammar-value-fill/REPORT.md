# Parameter value-entry grammar factoring

CPU mechanism evidence on Spark 1; these are not H100 throughput measurements.

The native Qwen tool grammar put `first_content` after a separate `leading_ws` rule. The optimizer only inlines a rule reference at the start of its containing sequence. Ordinary multi-byte content tokens therefore crossed a rule boundary at value entry and needed contextual Earley trials. Instrumentation observed 131,686 uncertain tokens in the hot first-content state, with the same 123 warmed masks throughout the request.

The production change factors `first_content rest` into `nonempty_value`, preserving the empty-value opt-in and all closing-delimiter restrictions. This allows the existing optimizer to keep ordinary value content inside one scanner. No matcher, mask, warmup count, grammar mode, or sampling behavior is changed.

Local implementation commit: `da794ce33f65539d00b802cb773c8ade61ccb6cf`. Root cherry-pick: `6884325dc381a592e240da909b8b2f5578cecd44`, combined with cold prewarm. Root and validation checkout both have tree `58f896cfc3f15654a7d739da0cf071506de05bde`.

## Red-first production regression

Oracle: after accepting `<parameter=city>\n`, ordinary merged tokens `Reykjavik` and `3 days` must be accepted by static state masks without uncertain-token contextual trials. The original production builder failed with 1 trial, expected 0 (exit 101), before the production edit. The fixed builder passes for all four combinations of `allow_empty_value` and `force_close`.

A second regression compares every complete mask with the original unfactored language while accepting and rolling back each input byte. Cases cover native values, HTML starting with `<`, empty and whitespace-only values, unknown keys, leading `=` and `>`, close-prefix counterexamples, and merged `>=`, `>a`, and complete close tokens. Existing native required-mode grammar tests also pass.

Command: `CUDA_VISIBLE_DEVICES="" ATLAS_SKIP_BUILD=1 CUDARC_CUDA_VERSION=13000 CARGO_TARGET_DIR=/home/pidtom/atlas-hopper-gate-full/target cargo test --locked -p spark-server --bin spark grammar::tests:: -- --nocapture`.

Observed focused result: **88 passed, 0 failed**, exit 0. Actual red and green logs are in `actual-server/`.

## Optimized real-tokenizer replay

The replay uses the already-staged pinned Qwen tokenizer (248,320 token slots), both EOS IDs `[248046,248044]`, exported native auto/required grammars, and the exact 40-token `get_weather` response. Both sides use baseline matcher/parser source; temporary instrumentation and the scratch-storage experiment were removed for these final timings. The optimized replay executable only changes the EBNF input through the same algebraic factoring as production.

| Mode | Original fill ms/token | Factored fill ms/token | Warm mask count |
| --- | ---: | ---: | ---: |
| Auto | 6.728 | 0.173 | 123 |
| Required | 6.624 | 0.170 | 123 |

Oracle: every full vocabulary bitmask at every position, including after accept/rollback, must compare byte-for-byte with the original grammar. Both auto and required golden comparisons passed. Actual content tokens remain accepted; malformed required function names remain refused. See `native-cpu/reference-final.stdout`, `native-cpu/factored-final.stdout`, and `native-cpu/factored/golden-final-*.json`.

This is one CPU replay per mode on a different host from the rental GPU. It establishes the source of repeated grammar work and semantic equivalence for the checked traces, not a scored serving speedup. Cold prewarm is still roughly 1.8–2.0 seconds serial in this independent baseline compiler fixture; the parent batches the separate parallel prewarm fix for H100 measurement.

The scratch-row storage candidate was tested separately and did not materially improve this workload. It is excluded from the production patch. Its red/green records remain under `native-cpu/scratch-*` for provenance.

## Stopping rule

Stop after the production regression is red then green, exact native masks/rollback match, and full default server plus rustdoc package gates pass on the combined source. The parent owns actual H100 retesting and all repository remote writes.

## Combined-source validation

All 5,110 tracked paths on Spark 1 matched the committed source manifest. Full default spark-server tests: 104 library + 2,349 binary + 3 artifact tests passed; 19 existing/explicit diagnostic or GPU tests ignored. Workspace doctests and `cargo doc --locked --workspace --no-deps` both exited 0. The documentation build completed in 20.35 seconds. Formatting, touched-file typos and diff checks passed. Logs and source verification are in `actual-server/`.

## Actual production-builder replay

The existing ignored native server diagnostic was explicitly run against the combined tree and passed (1 test, 83.50 seconds). It compiled both native auto and required grammars from the actual server tool builder, with both EOS IDs. The serial and parallel adaptive masks, all next-token masks and rollback masks matched; unknown required function names stayed refused. Its unoptimized CPU fill times were 9.571/9.433 ms per token and are not compared with release timings.

The exported production EBNF was then replayed with the same optimized baseline matcher executable used for the original language: **0.172 ms/token auto, 0.167 ms/token required**, both with 123 masks. Both complete 40-position mask/rollback golden files match the original language byte-for-byte. See `actual-server/native/golden-comparison.json` for matching SHA-256 values. This confirms that the real builder produces the effective transformation, not only the manually factored exploratory EBNF.

Cleanup removed both owned Spark 1 directories. The shared checkout was not modified; authorized shared Cargo cache artifacts remain. `cleanup-before.txt` and `cleanup-after.txt` record disk occupancy; source verification and all logs were exported first.
