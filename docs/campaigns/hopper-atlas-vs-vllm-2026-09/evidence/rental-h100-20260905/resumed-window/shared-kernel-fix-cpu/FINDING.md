# Native FP8 attention O projection: H100 rental follow-up

The multi-sequence attention O projection dispatched one scalar W8A16 GEMV per active request even though its input/output rows are contiguous and the native bundle already contains a four-row block-scaled GEMV. This repeated weight reads and kernel launches in each full-attention layer. The larger QKV routing issue is deferred because its output layout and gate handling require a separate proof.

Implementation: `ce75585a96ec94de05133f616cbff0f8657a9f56`, integrated as `6b76f3d83cd4eadc90b62100a87925f46d2a4c8e`. The compiled source trees are identical; see `CPU-IMPLEMENTATION-RECEIPT.json`.

The production route now uses the existing batch4 kernel in chunks of at most four rows when the optional handle is present, the checkpoint is block-scaled FP8, and both projection dimensions align to 128. Single-row decode, missing handles, unsupported shapes and other scale layouts retain the original scalar dispatch. The route reuses the original E4M3 weight bytes and block scales, creates no temporary buffers, and leaves the subsequent O-projection LoRA fold in place. The initial dispatch-only change preserved kernel arithmetic. Its subsequent strict GPU oracle exposed an existing batch-kernel rounding defect, corrected below; no threshold was changed.

## Observed checks

- Red: production `ms_phase_o_proj` with four FP8 rows emitted four scalar launches where the new expected dispatch was one. Exit 101, one test failed. Raw `red.log` and test-only `red.patch` retained.
- Green: the real production call now covers M2/M4/M5/M16, exact input/output chunk offsets, original weight and scale pointers, no new allocations, single-row/missing-handle/unsupported-shape/scale-layout fallbacks. Three focused tests pass.
- Full model: 657 passed, 14 ignored across unit/integration executables. One intermediate test-fixture usize/u32 compile error is retained separately in `green-model.log`; corrected successful output is `green-model-final.log`.
- Clippy package/tests, workspace rustdoc and workspace doctests exit 0. Doctests contain no runnable examples and two ignored examples, so their exit is not additional numerical evidence. Changed-file formatting, spelling and Git diff checks pass.

## Runtime oracle and stopping rule

The included `native_fp8_oproj_batch_microtest` uses the actual Qwen3.8 O-projection shape N=5120, K=6144 and M=2,4,5. It compares the existing scalar kernel with the newly selected existing batch4 kernel on varied finite E4M3 weights, BF16 activations and per-block scales. It requires exact BF16 output bytes, finite values and intact leading/trailing guards. The same comparison function must first reject an output-bit mutation, a guard mutation and a NaN. It reports maximum absolute error and cosine before acceptance, so an observed numerical difference remains visible and cannot silently relax the oracle.

The initial numerical run failed at M4: three BF16 output differences, maximum absolute error0.000488281 and cosine1; M2 passed exactly. This is a failure under the fixed exact oracle. Parent owns the pending corrected-kernel numerical rerun, fresh real-model quality gates and frozen latency rerun. Do not claim numerical equivalence or performance benefit from CPU tests alone. Stop on a failed numerical oracle; keep the initial result before any further change. Preserve the campaign's separately authorized word-reversal exception and all original raw gate failures.


## Observed kernel arithmetic defect and correction

The initial real H100 numerical run on integrated6b76f3d failed the exact M4 oracle with three BF16 differences (maximum absolute error0.000488281; cosine1). A near-unity cosine was insufficient to prove the existing bit-equivalence claim. Raw output remains with the parent numerical receipt.

The scalar kernel accumulates each product separately. The preexisting batch4/batch16 shared template instead evaluated `acc += lo*w0 + hi*w1`, rounding each pair before adding it to the accumulator. This differs from `acc += lo*w0; acc += hi*w1`. Commit `d119578e4b941978c4644bdb6c35356a98102afd` splits the two additions to retain scalar FP32 order and updates the misleading old cosine-based bit-equivalence comment.

Commit `4c963ee95aa06be7066e51e02fbaf93a4fc55d67` extends the same exact numerical example to the shared batch16 template at M8/M16. Original batch4 M2/M4/M5 cases remain. Additional activation rows are generated after the original five rows and scale draws, preserving the observed red fixture bytes. Output extent guards cover the larger allocation. Production model dispatch is unchanged by these follow-ups; the parent owns compilation and actual GPU green evidence before promotion.
