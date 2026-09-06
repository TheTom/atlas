# H100 dense NVFP4 MMQ capability defect

**Update:** full combined-source rental CPU validation passed at9cfce36; see [CPU-GATES-FINAL.md](CPU-GATES-FINAL.md). The temporary block below is retained as chronology and is resolved.

P0: the first 13-token Qwen3.8-27B request failed with CUDA 719 after the kernel audit resolved all 265 requested symbols. The vendored activation quantizer reported `quantize_mmq_nvfp4_worker has no device code compatible CUDA arch 900, compiled 900`. The failed cell is retained as `qwen38.atlas.b.lat.c1`.

## Cause and repair

`q4k_vendor/common.cuh` defines `BLACKWELL_MMA_AVAILABLE` only for NVIDIA `1200 <= __CUDA_ARCH__ < 1300`. Neither Hopper 900 nor datacentre Blackwell 1000 qualifies. `nvfp4_mmq.cu` previously exported its public wrappers regardless, so the activation worker compiled into `NO_DEVICE_CODE` and function lookup still succeeded. The separate `ATLAS_NO_WARP_BLOCKSCALE_MMA` guard used by other Atlas W4A4 modules never controlled this vendor module.

DenseFfn construction treated those resolved handles as capability. `finalize_nvfp4_mmq_load` repacked gate/up/down and freed their W4A16 transposed twins; prefill then dispatched through the trap. A late forward-only disable would leave the fallback weights missing.

The fix wraps the complete public implementation in the **vendor's own capability macro**. Unsupported targets now resolve no MMQ handles, so existing finalize logic returns before repacking/freeing and existing prefill uses W4A16. The two shipped Hopper dense targets explicitly explain all 13 missing exports in their kernel audit. There is currently no B200 dense-27B target; the vendor guard correctly excludes SM1000 if one is added. No architecture threshold is newly duplicated in production Rust, no recipe/environment override is added, and no watchdog or capacity accounting changes.

Commit: `14ddfaf` in `codex/hopper-nvfp4-mmq-capability`, based on `72834f2`. Parent owns cherry-pick, fresh CUDA build and real-engine validation.

## Observed CPU checks

- **Known bad first:** actual Clang C++ preprocessing of the wrapper with the verbatim vendor macro and constants exposed 13 public wrappers at arch 900, 1000 and 1300. Oracle expected 0; exit 1. At 1200/1210 it correctly exposed 13. `preprocess-red.json`.
- **Green after fix:** the identical command emits 0/0/13/13/0 wrappers for 900/1000/1200/1210/1300; exit 0. `preprocess-green.json`.
- GB10/control: preprocessed old/new SM1200 and SM1210 token streams are identical after whitespace normalization. This proves this guard changes no supported branch text; it does not substitute for numeric GPU tests. `gb10-preprocessor-equivalence.json`.
- Actual MODEL.toml parse checks passed all four hardware/model combinations: Hopper36+38 name exactly all13 exports, GB10 names none absent.
- Registered Rust source-guard test, built standalone from its identical test body with rustc: 1 passed. `source-guard-test.log`.
- `cargo fmt --all -- --check`, changed-file `typos`, and `git diff --check`: exit0.
- New production finalize regression is registered under `layers::dense_ffn::mmq_tests::unavailable_mmq_preserves_transposed_weights_without_repack_or_free`; it calls the real finalize method with a missing required MMQ handle and checks no allocations, launches, synchronization or freed fallback twins. **Cargo execution pending**, not counted as passed.

The preprocessing receipt intentionally omits includes and uses the unchanged vendor predicate, so it proves conditional export selection without CUDA headers. A fresh real CUDA compile/PTX/audit is still required.

## Temporary broad-validation block

Local offline `cargo test --locked --offline -p atlas-kernels --test nvfp4_mmq_capability` exited101 because `anyhow v1.0.104` is not in the local cache. Spark1 had only2.8GiB free (2.9GiB after sibling cleanup); parent explicitly prohibited new Cargo/build work there. No new Spark1 worktree or build was created. Full affected crate tests, server gate and workspace rustdoc remain pending until parent assigns an adequate CPU build environment. No H100 calls, GPU work, remote writes, installs or downloads were performed for this fix.

Stopping rule for this bounded task: deliver focused source commit after observed red/green export oracle, retaining the broad-test block and requiring fresh H100 compile/audit/coherency before claiming runtime repair.
