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

// ── (b) common/ — inherited from gb10 by relative symlink ──

/// Every problem with one mirrored directory, as human-readable lines.
///
/// A mirror is correct when it is a bijection onto `origin` made of relative
/// symlinks that resolve: an entry `origin` has and `mirror` does not is a
/// kernel that vanishes from this hardware's build, an entry `mirror` has and
/// `origin` does not is a fork nobody declared, and a link that does not
/// resolve is a compile error deferred to whoever next owns a GPU.
///
/// Returns the empty vec when the mirror is sound. Kept as a function rather
/// than inline assertions so `the_dangling_symlink_check_can_fail` can drive
/// it against a deliberately broken tree — a checker that has never failed has
/// never been tested.
fn mirror_faults(mirror: &Path, origin: &Path) -> Vec<String> {
    let names = |dir: &Path| -> BTreeSet<String> {
        std::fs::read_dir(dir)
            .unwrap_or_else(|e| panic!("{}: {e}", dir.display()))
            .flatten()
            .map(|e| e.file_name().to_string_lossy().to_string())
            .collect()
    };
    let (mirrored, originals) = (names(mirror), names(origin));
    let mut faults = Vec::new();
    for missing in originals.difference(&mirrored) {
        faults.push(format!("{missing}: present in origin, absent from mirror"));
    }
    for extra in mirrored.difference(&originals) {
        faults.push(format!("{extra}: present in mirror, absent from origin"));
    }
    // Every mirrored entry is link-checked, including ones the origin no
    // longer has: a link is most likely to dangle precisely when its target
    // was renamed away, and reporting only "absent from origin" would hide
    // that the tree in hand does not compile.
    for name in &mirrored {
        let path = mirror.join(name);
        let Ok(link) = std::fs::read_link(&path) else {
            faults.push(format!("{name}: a regular file, not a symlink to origin"));
            continue;
        };
        if link.is_absolute() {
            faults.push(format!("{name}: absolute symlink {}", link.display()));
        }
        // THE ORACLE. `read_link` reports the stored text; `exists()` follows
        // it. A dangling link is invisible to `read_dir` and to git, and
        // shows up first as an nvcc "No such file or directory".
        if !path.exists() {
            faults.push(format!("{name}: dangling symlink -> {}", link.display()));
        }
    }
    faults.sort();
    faults
}

/// ORACLE: `kernels/gb10/common`. Hopper's `common/` is that directory,
/// reachable — all 181 entries (171 `.cu`, 9 `.cuh` headers the `.cu` files
/// `#include`, and `KERNEL.toml`, which `build.rs` merges as the base layer of
/// every target's flags and `[modules]` overrides).
///
/// Unlike strix's curated 99, nothing is left out: hopper is an NVIDIA target
/// compiled by the same nvcc, so a file gb10 compiles is a file hopper must
/// compile, and a subset here would be an undocumented kernel drop.
#[test]
fn common_mirrors_every_gb10_common_file() {
    let faults = mirror_faults(&hopper_dir().join("common"), &gb10_dir().join("common"));
    assert!(
        faults.is_empty(),
        "kernels/hopper/common has drifted from kernels/gb10/common:\n  {}",
        faults.join("\n  ")
    );
}

/// The header files matter as much as the sources: `common/*.cuh` is what the
/// macro-declared kernels `#include`, and a missing one fails the compile of a
/// `.cu` that is itself present. Counted explicitly so a mirror that silently
/// became `.cu`-only is not read as "no faults".
#[test]
fn common_carries_the_headers_and_the_kernel_toml() {
    let dir = hopper_dir().join("common");
    let mut by_ext = std::collections::BTreeMap::<String, usize>::new();
    for entry in std::fs::read_dir(&dir).expect("kernels/hopper/common").flatten() {
        let path = entry.path();
        let ext = path
            .extension()
            .map(|e| e.to_string_lossy().to_string())
            .unwrap_or_default();
        *by_ext.entry(ext).or_default() += 1;
    }
    assert!(dir.join("KERNEL.toml").exists(), "KERNEL.toml is the flag base");
    assert!(
        by_ext.get("cuh").copied().unwrap_or(0) > 0,
        "no .cuh headers mirrored: {by_ext:?}"
    );
    assert!(
        by_ext.get("cu").copied().unwrap_or(0) > 100,
        "suspiciously few .cu sources mirrored: {by_ext:?}"
    );
}

// ── (e) the oracle, tested ──

/// A dangling symlink must FAIL `mirror_faults`. Without this the whole
/// symlink half of this file is an assertion that has never once been observed
/// to fire, and `assert!(faults.is_empty())` passes just as happily against a
/// checker that always returns nothing.
#[test]
fn the_dangling_symlink_check_can_fail() {
    let root = std::env::temp_dir().join(format!(
        "atlas-hopper-mirror-{}-{}",
        std::process::id(),
        line!()
    ));
    let origin = root.join("origin");
    let mirror = root.join("mirror");
    std::fs::create_dir_all(&origin).unwrap();
    std::fs::create_dir_all(&mirror).unwrap();
    std::fs::write(origin.join("present.cu"), "// kernel\n").unwrap();
    std::fs::write(origin.join("gone.cu"), "// kernel\n").unwrap();
    std::os::unix::fs::symlink("../origin/present.cu", mirror.join("present.cu")).unwrap();
    // The failure this exists to catch: a link whose target was renamed or
    // removed. `read_dir` still lists it and git still stores it.
    std::os::unix::fs::symlink("../origin/gone.cu", mirror.join("gone.cu")).unwrap();
    std::fs::remove_file(origin.join("gone.cu")).unwrap();

    let faults = mirror_faults(&mirror, &origin);
    let _ = std::fs::remove_dir_all(&root);

    assert_eq!(
        faults,
        vec![
            "gone.cu: dangling symlink -> ../origin/gone.cu".to_string(),
            "gone.cu: present in mirror, absent from origin".to_string(),
        ],
        "the mirror check did not report a dangling symlink"
    );
}

/// …and the other two faults it is responsible for: a missing entry and a
/// regular file where a symlink belongs (a silent fork of a shared kernel).
#[test]
fn the_mirror_check_reports_missing_entries_and_regular_files() {
    let root = std::env::temp_dir().join(format!(
        "atlas-hopper-mirror-{}-{}",
        std::process::id(),
        line!()
    ));
    let origin = root.join("origin");
    let mirror = root.join("mirror");
    std::fs::create_dir_all(&origin).unwrap();
    std::fs::create_dir_all(&mirror).unwrap();
    std::fs::write(origin.join("forked.cu"), "// origin\n").unwrap();
    std::fs::write(origin.join("missing.cu"), "// origin\n").unwrap();
    std::fs::write(mirror.join("forked.cu"), "// a copy, not a link\n").unwrap();

    let faults = mirror_faults(&mirror, &origin);
    let _ = std::fs::remove_dir_all(&root);

    assert_eq!(
        faults,
        vec![
            "forked.cu: a regular file, not a symlink to origin".to_string(),
            "missing.cu: present in origin, absent from mirror".to_string(),
        ]
    );
}
