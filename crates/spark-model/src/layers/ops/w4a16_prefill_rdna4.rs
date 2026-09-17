// SPDX-License-Identifier: AGPL-3.0-only

//! WHICH W4A16 prefill GEMM a target dispatches, and the handle for the
//! RDNA 4 one.
//!
//! # The measurement
//!
//! `amd-rig-handoff/audit/PREFILL-ANALYSIS.md` section 3.6. On an R9700 the
//! Ornith-1.0-9B runs its projection GEMMs at ~1.07 TFLOP/s on
//! `w4a16_gemm_t_m128` and the Qwen3.8-27B at ~4.11 TFLOP/s on the plain
//! `w4a16_gemm`: so the twin arm that wins by 7.3x on GB10 loses by 3.85x on
//! gfx1201. `kernels/r9700/common/w4a16_gemm_rdna4.cu` is the answer to the
//! two structural causes the audit names (128 accumulator VGPRs under
//! `__launch_bounds__(128, 3)`, and an emulated `cp.async` drained in full
//! once per K step), and this module is how it is reached.
//!
//! # The rule
//!
//! The lever is `[defaults] w4a16_prefill_variant`, `"rdna4"` on
//! `kernels/r9700` and `"gb10"` everywhere else, overridden by
//! `ATLAS_W4A16_PREFILL_VARIANT`. [`rdna4_prefill_kernel`] issues the kernel
//! lookup ONLY when that resolves to `Rdna4`, which is the discipline
//! [`crate::layers::w4a16_v2_kernel`] established: a probe that can never
//! succeed on this target adds a permanently-failing row to the boot audit and
//! buys nothing. It is an init-time call whose result the layer stores, never
//! a per-launch one.
//!
//! # Why a zero handle is a fallback here and a panic there
//!
//! `w4a16_v2_kernel` PANICS when `ATLAS_W4A16_VARIANT=v2` names a kernel the
//! target does not ship, because that request is an operator asking for a
//! specific arm and getting silence. This one returns `KernelHandle(0)` and
//! lets the caller fall through to the plain arm, because the r9700 value is a
//! DEFAULT rather than a request: a build of that target with the source
//! removed, or a checkout at a commit before it landed, must serve on the arm
//! it served on before rather than refuse to start. An operator who types the
//! variable and means it still gets a hard answer, the spelling is validated
//! in `target_defaults::resolve_w4a16_variant`, which panics on anything that
//! is not `gb10` or `rdna4`.

use spark_runtime::gpu::{GpuBackend, KernelHandle};

use super::target_defaults::{self, W4a16PrefillVariant};

/// The module and entry point of the RDNA 4 prefill GEMM.
///
/// The module name comes from `kernels/gb10/common/KERNEL.toml` `[modules]`
/// (`w4a16_gemm_rdna4 = "w4a16_rdna4"`), which is the one `[modules]` table on
/// every target: the other trees' `common/KERNEL.toml` are symlinks to it.
/// The SOURCE is not shared: it is a real file under
/// `kernels/r9700/common/`, declared in that target's `[kernels] overrides`,
/// so no NVIDIA build compiles it and no NVIDIA build defines this symbol.
pub const RDNA4_MODULE: &str = "w4a16_rdna4";
pub const RDNA4_KERNEL: &str = "w4a16_gemm_rdna4";

/// Whether this target dispatches the RDNA 4 arm at all, pure, so the rule
/// is gradable from a CPU test without a GPU or the process environment.
pub fn armed(variant: W4a16PrefillVariant) -> bool {
    matches!(variant, W4a16PrefillVariant::Rdna4)
}

/// The RDNA 4 prefill GEMM handle, or `KernelHandle(0)` when this target does
/// not ask for it or does not carry it.
///
/// ⚠️ INIT-TIME. Callers store the handle on the layer beside
/// `w4a16_gemm_k`; `gpu.kernel(..)` is a module lookup, not something to do
/// per launch, and the route must stay constant across CUDA-graph replays.
#[track_caller]
pub fn rdna4_prefill_kernel(gpu: &dyn GpuBackend) -> KernelHandle {
    if !armed(target_defaults::resolved().w4a16_prefill_variant.value) {
        return KernelHandle(0);
    }
    let h = crate::layers::try_kernel(gpu, RDNA4_MODULE, RDNA4_KERNEL);
    if h.0 == 0 {
        tracing::warn!(
            "w4a16_prefill_variant=rdna4 but {RDNA4_MODULE}::{RDNA4_KERNEL} is not in this \
             target's kernel set: the prefill projections stay on the plain w4a16_gemm arm"
        );
    } else {
        tracing::debug!(handle = h.0, "w4a16_gemm_rdna4 prefill arm armed");
    }
    h
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The rule, both ways. `armed` is the whole of the dispatch decision, so
    /// it is the whole of what a CPU test can pin.
    #[test]
    fn only_the_rdna4_family_arms_the_rdna4_kernel() {
        assert!(armed(W4a16PrefillVariant::Rdna4));
        assert!(!armed(W4a16PrefillVariant::Gb10));
    }

    /// The names the lookup uses are the names the kernel tree declares. A
    /// typo here is a permanently-zero handle and a silent fallback to the arm
    /// the R9700 measures at ~1.07 TFLOP/s, which is exactly the failure that
    /// would never show up as an error.
    #[test]
    fn the_lookup_names_match_the_kernel_tree() {
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .and_then(std::path::Path::parent)
            .expect("crates/spark-model is two levels below the workspace root")
            .join("kernels");

        let source = root.join("r9700/common").join(format!("{RDNA4_KERNEL}.cu"));
        assert!(
            source.is_file() && !source.is_symlink(),
            "{} must be a REAL file in the r9700 tree: it is target-owned, and \
             check_cross_hardware.py rule S1 refuses a cross-hardware symlink",
            source.display()
        );
        let text = std::fs::read_to_string(&source).expect("read the kernel source");
        assert!(
            text.contains(&format!("void {RDNA4_KERNEL}(")),
            "{} does not define `{RDNA4_KERNEL}`",
            source.display()
        );

        let modules = std::fs::read_to_string(root.join("gb10/common/KERNEL.toml"))
            .expect("read the shared [modules] table");
        assert!(
            modules.contains(&format!("{RDNA4_KERNEL} = \"{RDNA4_MODULE}\"")),
            "kernels/gb10/common/KERNEL.toml [modules] must map the stem \
             `{RDNA4_KERNEL}` to `{RDNA4_MODULE}`, or the lookup resolves nothing"
        );
    }
}
