// SPDX-License-Identifier: AGPL-3.0-only
//
// HARDWARE.toml `arch` → `KernelTarget.arch` mapping for build.rs. Included
// via `#[path = "build_arch.rs"] mod build_arch;` and reached from the codegen
// module as `super::build_arch::kernel_target_arch`.
//
// Its own file, with no `super::` dependencies, so
// `tests/kernel_shadow_detector.rs`-style integration tests can compile the
// SAME code: cargo never runs a build script's `#[cfg(test)]` modules, so a
// rule that lives only inside build.rs is a rule nothing tests.

/// The base SM string a compiled target is recorded under, given the `arch`
/// its HARDWARE.toml declares.
///
/// nvcc's `-arch=` takes a *feature* architecture: a base SM number plus an
/// optional one-letter suffix selecting an extended instruction set —
/// `a` = arch-specific (Hopper `sm_90a` wgmma/TMA, Blackwell `sm_100a`),
/// `f` = family-specific (`sm_121f`). The suffix steers the COMPILER; it is
/// not part of the architecture's identity, and `KernelTarget.arch` spells
/// GB10 `sm_121` (see `crates/atlas-core/src/target.rs`). So strip it.
///
/// Only `sm_<digits>` strings are touched. SCALE/HIP `gfx*` names select a
/// per-arch toolchain directory verbatim (`gfx90a` is a whole architecture,
/// not `gfx90` plus a suffix) and Metal forwards `metal3.1` to `-std=`;
/// rewriting either would break the build it feeds.
pub(crate) fn kernel_target_arch(arch: &str) -> String {
    let Some(digits) = arch.strip_prefix("sm_") else {
        return arch.to_string();
    };
    let trimmed = digits.trim_end_matches(['a', 'f']);
    if trimmed.is_empty() || !trimmed.bytes().all(|b| b.is_ascii_digit()) {
        return arch.to_string();
    }
    format!("sm_{trimmed}")
}
