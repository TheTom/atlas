// SPDX-License-Identifier: AGPL-3.0-only

//! The `kernels/hopper` (H100/H200, sm_90a) target, pinned against the REAL
//! tree — same posture as `target_resolution.rs`: `src/*_tests.rs` prove the
//! rules on fixtures, these prove the DATA that is actually checked in.
//!
//! Hopper ships no kernels of its own. Every source it compiles is a relative
//! symlink into `kernels/gb10`, which makes `gb10` the ORACLE for this whole
//! file: hopper's kernel set is correct exactly when it is gb10's kernel set,
//! reachable. A symlink that dangles, or a gb10 file that gained no hopper
//! counterpart, is a kernel that silently vanishes from the build — the
//! shadow-drift failure class documented in `build.rs`, arriving through a
//! different door.
//!
//! `cargo test` runs GPU-free with `ATLAS_SKIP_BUILD=1`, where `build.rs`
//! returns before target resolution ever happens, so without this file nothing
//! in CI looks at the hopper tree at all.

use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

fn kernels_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crates/atlas-kernels is two levels below the workspace root")
        .join("kernels")
}

fn hopper_dir() -> PathBuf {
    kernels_root().join("hopper")
}

fn gb10_dir() -> PathBuf {
    kernels_root().join("gb10")
}

fn hardware_toml() -> toml::Value {
    let path = hopper_dir().join("HARDWARE.toml");
    let text = std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    toml::from_str(&text).unwrap_or_else(|e| panic!("bad TOML in {}: {e}", path.display()))
}

// ── (a) HARDWARE.toml ──

/// ORACLE: `build.rs::resolve_targets`, which reads exactly `hardware.arch`
/// (required, string) and `hardware.vendor` (steers `resolve_compute_target`
/// and the per-vendor KERNEL.toml flag key). `name` mirrors gb10's file. The
/// arch is `sm_90a` because H100 and H200 are both SM 9.0 and `a` is nvcc's
/// arch-specific spelling; `sm_100` is Blackwell datacenter, not Hopper.
#[test]
fn hardware_toml_declares_an_nvidia_sm90a_target() {
    let toml = hardware_toml();
    let hw = toml.get("hardware").expect("[hardware] table");
    assert_eq!(hw.get("name").and_then(|v| v.as_str()), Some("hopper"));
    assert_eq!(
        hw.get("vendor").and_then(|v| v.as_str()),
        Some("nvidia"),
        "vendor picks the compiler in build_target::resolve_compute_target"
    );
    assert_eq!(
        hw.get("arch").and_then(|v| v.as_str()),
        Some("sm_90a"),
        "Hopper is SM 9.0; sm_100 is Blackwell datacenter"
    );
    assert_eq!(
        hw.get("compute_capability").and_then(|v| v.as_str()),
        Some("9.0")
    );
}

/// The keys gb10's HARDWARE.toml carries, hopper carries too. Nothing in the
/// tree READS `compute_capability` or the `memory_*` keys — verified by grep
/// over the whole repo — so this pins the documented shape rather than a
/// behaviour, exactly as strix's file does. The strix precedent is that an
/// unread key must at least be honest: two were deleted there for having no
/// reader, and these three survive as roofline/documentation input.
#[test]
fn hardware_toml_carries_the_same_key_set_as_gb10() {
    let hopper = hardware_toml();
    let gb10_path = gb10_dir().join("HARDWARE.toml");
    let gb10: toml::Value =
        toml::from_str(&std::fs::read_to_string(&gb10_path).expect("gb10 HARDWARE.toml"))
            .expect("valid TOML");
    let keys = |v: &toml::Value| -> BTreeSet<String> {
        v.get("hardware")
            .and_then(|h| h.as_table())
            .expect("[hardware] table")
            .keys()
            .cloned()
            .collect()
    };
    assert_eq!(
        keys(&hopper),
        keys(&gb10),
        "hopper/HARDWARE.toml must declare the same keys as the other NVIDIA target"
    );
}
