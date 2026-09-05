// SPDX-License-Identifier: AGPL-3.0-only

//! `kernel_target_arch` — the HARDWARE.toml `arch` → `KernelTarget.arch`
//! mapping, pinned.
//!
//! ORACLE: the CUDA toolkit's own naming. `nvcc -arch=` accepts a *feature*
//! architecture (`sm_90a`, `sm_100a`, `sm_121f`) whose trailing letter selects
//! the arch-specific / family-specific instruction set on top of a base SM
//! number. The base number is what `KernelTarget.arch` records — the constants
//! in `crates/atlas-core/src/target.rs` spell it `sm_121`, not `sm_121f` — so
//! the mapping must strip the suffix and nothing else. Non-NVIDIA arch strings
//! (SCALE `gfx*`, Metal `metal3.1`) are opaque to this rule and pass through.
//!
//! `build_codegen.rs` used `trim_end_matches('f')`, which handled `sm_121f`
//! only; `sm_90a` (Hopper) would have reached the registry as `sm_90a`.
//!
//! This is an integration test rather than a `#[cfg(test)]` module inside the
//! build script because cargo never runs a build script's own unit tests —
//! the same reason `tests/kernel_shadow_detector.rs` exists.

#[path = "../build_arch.rs"]
mod build_arch;

use build_arch::kernel_target_arch;

#[test]
fn family_specific_suffix_is_stripped() {
    // GB10 ships `arch = "sm_121f"`; the registry records `sm_121`.
    assert_eq!(kernel_target_arch("sm_121f"), "sm_121");
}

#[test]
fn arch_specific_suffix_is_stripped() {
    // Hopper ships `arch = "sm_90a"` (wgmma/TMA opt-in), Blackwell datacenter
    // `sm_100a`. Both record their base SM.
    assert_eq!(kernel_target_arch("sm_90a"), "sm_90");
    assert_eq!(kernel_target_arch("sm_100a"), "sm_100");
    assert_eq!(kernel_target_arch("sm_121a"), "sm_121");
}

#[test]
fn a_plain_sm_number_is_unchanged() {
    assert_eq!(kernel_target_arch("sm_121"), "sm_121");
    assert_eq!(kernel_target_arch("sm_90"), "sm_90");
}

#[test]
fn non_nvidia_arch_strings_pass_through() {
    // SCALE/HIP select a per-arch toolchain dir by this exact string, and
    // Metal forwards it to `-std=`. Neither may be rewritten.
    assert_eq!(kernel_target_arch("gfx1151"), "gfx1151");
    assert_eq!(kernel_target_arch("gfx90a"), "gfx90a");
    assert_eq!(kernel_target_arch("metal3.1"), "metal3.1");
}
