# Restore the BF16 multi-sequence decode head

Commit: `b5ef32d098b8c8ba8a85fcc45973a6ca05c746bf`, based on `5cde118469d5f623c3e26da3055dd9001b781fc2`. Tree: `a1b76d7c787a3b779d21b9008c77e1ae9d8d184e`.

The shared ordinary/mixed decode head unconditionally selected scalar `dense_gemm_bf16` for BF16 checkpoints despite loading the existing `dense_gemv_bf16_batchm` kernel and retaining an unused default-on environment switch. Qwen3.8's original BF16 head is 248320 by 5120 (2,542,796,800 bytes). This fix restores the shared-weight batch kernel for 1–8 rows with aligned K, and retains scalar fallback for larger batches, missing handles, opt-out, or K not divisible by eight. No weights, activations, CUDA kernels, or quantization formats change. Only exact `ATLAS_LMHEAD_BATCH_GEMV=0` disables this path, preserving the old switch semantics.

The existing CUDA kernel has a scalar K tail, but vectorized `uint4` row loads also require aligned row starts; K=130 therefore stays on the scalar fallback. Qwen's K=5120 satisfies the contract. The existing ops MAX_M=8 check is unchanged.

## Red-first evidence and oracles

The new test exercises the exact private production projection used by both `lm_head_project_batched` callers. With the old scalar implementation, the default case failed: actual kernel handle 51966 versus expected 48918; exit 101, 2 passed and 1 failed. With the dispatch restored, all 3 focused tests passed. Cases cover M=1/2/4/8, M=9/16 refusal to select the capped kernel, K=130 alignment fallback, missing handle and exact opt-out semantics. The mock observes kernel, original weight/input/output pointers, launch dimensions, stream, output stride and no allocation. It does not prove GPU arithmetic; see `GPU-CHECK-COMMANDS.md` for the real numerical check owned by the parent.

Full model CPU tests passed: 650 unit plus 4 integration = 654 passed, 14 ignored, no failures. Affected clippy, local formatting, diff check and typos passed. Workspace documentation generated successfully. Exact commands, exits, wall times and full output are in the corresponding `.json` and `.log` files. Workspace doctests completed with exit 0: zero executed, two ignored.

All rental CPU checks hide CUDA devices, set ATLAS_SKIP_BUILD=1 and use the dedicated target-cpu-checks with four jobs. No GPU calls, engine requests or release-target changes were made by this agent. The owned worktree contains only the three changed files on the recorded base; each SHA256 matches the committed file (`source-hashes.json`). GPU occupancy was empty at 00:57:26 UTC before staging; `df -h /` reported 500G total, 117G used and 384G available. The owned source worktree was removed successfully. Final cleanup `df -h /` again reported 384G available (`cleanup.log`); shared targets are preserved.

## Attribution limits

Before this fix, native latency C16 produced about 65 tok/s. Its 16 serial prefills consumed 26.8–26.9% of each measured burst wall time; even eliminating all of that observed interval could only reach roughly 89 tok/s. Thus serial prefill alone cannot explain the gap to vLLM's 790 tok/s. The lost BF16 dispatch is a source defect with a direct red regression, but its performance impact remains unmeasured until the parent rebuilds and runs the unchanged numerical/coherency and frozen ladder checks.

The existing GPU example compares batch output with repeated C1 GEMV, not the previous scalar GEMM accumulation order; same dtype is not a promise of bit equality to that old implementation. Original failed/slow cells and all certification/precision caveats remain retained.
