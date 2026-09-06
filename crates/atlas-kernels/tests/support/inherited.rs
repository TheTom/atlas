// SPDX-License-Identifier: AGPL-3.0-only

//! WHICH hardware sets inherit `kernels/gb10`'s kernels, and where their files
//! live on disk.
//!
//! Shared by `tests/inherited_targets.rs` and
//! `tests/inherited_targets_w4a4.rs`, which pin two different properties of the
//! same trees and must agree on what those trees ARE: a second copy of
//! [`INHERITED`] would let one binary keep testing a target the other had
//! already been told about. Lives under `tests/support/` so cargo does not pick
//! it up as a test target of its own — a subdirectory is not auto-discovered, a
//! `tests/*.rs` is — the same reason `mirror.rs` is here.
//!
//! Each including binary reads the subset of this file it needs (the W4A4
//! binary asks only for `hw` and `blockscale_rejection`), so the unread
//! remainder is dead code in exactly one of the two — allowed here rather than
//! split further, because the point of the file is that ONE declaration
//! describes each target.
#![allow(dead_code)]

use std::path::{Path, PathBuf};

/// One hardware set that inherits gb10's kernels.
pub struct Inherited {
    /// `kernels/<hw>` directory name.
    pub hw: &'static str,
    /// `[hardware].arch`, verbatim — what reaches `nvcc -arch=`.
    pub arch: &'static str,
    /// `[hardware].compute_capability`.
    pub cc: &'static str,
    /// The opening line every copied MODEL.toml must carry, naming where the
    /// kernels came from. Per-target because it names the target.
    pub provenance: &'static str,
    /// The campaign's declared P0 model set for this hardware.
    pub models: &'static [&'static str],
    /// The ptxas rejection this hardware answers by defining
    /// `ATLAS_NO_WARP_BLOCKSCALE_MMA` — the arch-specific half of the reason,
    /// which the MODEL.toml entries must cite. Per-target because the two
    /// architectures that need it reject the W4A4 region for DIFFERENT
    /// reasons.
    ///
    /// `None` means the architecture HAS the warp-level
    /// `mma.sync ... .kind::mxf4nvf4.block_scale`, so it must NOT define the
    /// macro and must NOT declare the two W4A4 entry points absent — the gb10
    /// posture, on a target that is not gb10. Stated as an option rather than
    /// left out of the list, because "this target keeps the kernel set whole"
    /// is the claim, and a target absent from `INHERITED` would be asserted
    /// about by nothing at all.
    pub blockscale_rejection: Option<&'static str>,
}

/// The five P0 models shared by the Hopper/B200 campaign. A CURATED subset of
/// gb10's 26, not a mirror of it: adding a model to a target means adding its
/// directory AND the list that target carries.
pub const P0_MODELS: &[&str] = &[
    "deepseek-v4-flash",
    "nemotron-3-nano-30b-a3b",
    "nemotron-super-120b-a12b",
    "qwen3-next-80b-a3b",
    "qwen3.6-35b-a3b",
];

/// Hopper additionally carries the PRD section 16 first paid 27B cell and
/// the same-hardware source target its kernel_source redirect requires.
pub const HOPPER_MODELS: &[&str] = &[
    "deepseek-v4-flash",
    "nemotron-3-nano-30b-a3b",
    "nemotron-super-120b-a12b",
    "qwen3-next-80b-a3b",
    "qwen3.6-27b",
    "qwen3.6-35b-a3b",
    "qwen3.8-27b",
];

/// Every hardware set whose kernels are gb10's, reached by symlink.
///
/// ORACLE for the arch strings: NVIDIA's own SM numbering. H100 and H200 are
/// both SM 9.0; B200 and GB200 are SM 10.0; the RTX PRO 6000 Blackwell
/// workstation parts are SM 12.0. The `a` suffix is nvcc's arch-specific
/// spelling — it opts the target into wgmma/TMA on Hopper, tcgen05 and native
/// NVFP4 on Blackwell datacentre, and consumer Blackwell's warp-level
/// block-scaled MMA on sm_120a — and it makes the PTX non-forward-compatible,
/// which is correct for a per-architecture target.
///
/// `sm_120a` rather than gb10's `sm_121f`: a family arch runs on CC >= 12.1
/// within the 12.x family, so `sm_121f` PTX does NOT load on a CC 12.0 device.
/// The workstation part needs its own arch string even though it shares gb10's
/// instruction set.
pub const INHERITED: &[Inherited] = &[
    Inherited {
        hw: "hopper",
        arch: "sm_90a",
        cc: "9.0",
        provenance: "Hopper target: kernel set inherited from gb10 via symlink",
        models: HOPPER_MODELS,
        blockscale_rejection: Some("cvt with .e2m1x2"),
    },
    Inherited {
        hw: "b200",
        arch: "sm_100a",
        cc: "10.0",
        provenance: "B200 target: kernel set inherited from gb10 via symlink",
        models: P0_MODELS,
        blockscale_rejection: Some("mma with block scale"),
    },
    Inherited {
        hw: "rtx-pro-6000",
        arch: "sm_120a",
        cc: "12.0",
        provenance: "RTX PRO 6000 target: kernel set inherited from gb10 via symlink",
        models: P0_MODELS,
        // NOT `Some(...)`: workstation Blackwell is the SAME consumer-Blackwell
        // ISA family as GB10 and HAS the warp-level
        // `mma.sync ... .kind::mxf4nvf4.block_scale` (CUTLASS gates it as
        // CUTLASS_ARCH_MMA_SM120_SUPPORTED). Defining the macro here would
        // delete two kernels this hardware can run.
        blockscale_rejection: None,
    },
];

pub fn kernels_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crates/atlas-kernels is two levels below the workspace root")
        .join("kernels")
}

pub fn hw_dir(hw: &str) -> PathBuf {
    kernels_root().join(hw)
}

pub fn gb10_dir() -> PathBuf {
    kernels_root().join("gb10")
}

pub fn hardware_toml(hw: &str) -> toml::Value {
    let path = hw_dir(hw).join("HARDWARE.toml");
    let text = std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    toml::from_str(&text).unwrap_or_else(|e| panic!("bad TOML in {}: {e}", path.display()))
}
