// SPDX-License-Identifier: AGPL-3.0-only

//! The hardware targets that INHERIT `kernels/gb10`'s kernels instead of
//! shipping their own — `kernels/hopper` (H100/H200, sm_90a) and
//! `kernels/b200` (B200/GB200, sm_100a) — pinned against the REAL tree.
//!
//! Same posture as `target_resolution.rs`: `src/*_tests.rs` prove the rules on
//! fixtures, these prove the DATA that is actually checked in.
//!
//! Neither target ships a kernel of its own. Every source they compile is a
//! relative symlink into `kernels/gb10`, which makes `gb10` the ORACLE for
//! this whole file: an inherited kernel set is correct exactly when it is
//! gb10's kernel set, reachable. A symlink that dangles, or a gb10 file that
//! gained no counterpart, is a kernel that silently vanishes from that
//! hardware's build — the shadow-drift failure class documented in `build.rs`,
//! arriving through a different door.
//!
//! `cargo test` runs GPU-free with `ATLAS_SKIP_BUILD=1`, where `build.rs`
//! returns before target resolution ever happens, so without this file nothing
//! in CI looks at either tree at all.
//!
//! PARAMETRISED over [`INHERITED`] rather than duplicated per hardware set:
//! the second target arrived by copying the first, and two copies of an
//! assertion drift the moment one is updated. Each test names the hardware set
//! in its failure message, so a red still says which tree is wrong.

#[path = "support/mirror.rs"]
mod mirror;

use mirror::mirror_faults;

use std::path::{Path, PathBuf};

/// One hardware set that inherits gb10's kernels.
struct Inherited {
    /// `kernels/<hw>` directory name.
    hw: &'static str,
    /// `[hardware].arch`, verbatim — what reaches `nvcc -arch=`.
    arch: &'static str,
    /// `[hardware].compute_capability`.
    cc: &'static str,
    /// The opening line every copied MODEL.toml must carry, naming where the
    /// kernels came from. Per-target because it names the target.
    provenance: &'static str,
    /// The campaign's declared P0 model set for this hardware.
    models: &'static [&'static str],
    /// The ptxas rejection this hardware answers by defining
    /// `ATLAS_NO_WARP_BLOCKSCALE_MMA` — the arch-specific half of the reason,
    /// which the MODEL.toml entries must cite. Per-target because the two
    /// architectures reject the W4A4 region for DIFFERENT reasons.
    blockscale_rejection: &'static str,
}

/// The five P0 models of the Hopper/B200 campaign. Both inherited targets
/// carry the same set, so this is one const, not two — but it is a CURATED
/// subset of gb10's 26, not a mirror of it, and adding a model to a target
/// means adding its directory AND this list.
const P0_MODELS: &[&str] = &[
    "deepseek-v4-flash",
    "nemotron-3-nano-30b-a3b",
    "nemotron-super-120b-a12b",
    "qwen3-next-80b-a3b",
    "qwen3.6-35b-a3b",
];

/// Every hardware set whose kernels are gb10's, reached by symlink.
///
/// ORACLE for the arch strings: NVIDIA's own SM numbering. H100 and H200 are
/// both SM 9.0; B200 and GB200 are SM 10.0. The `a` suffix is nvcc's
/// arch-specific spelling — it opts the target into wgmma/TMA on Hopper and
/// tcgen05/native-NVFP4 on Blackwell datacentre, and it makes the PTX
/// non-forward-compatible, which is correct for a per-architecture target.
const INHERITED: &[Inherited] = &[
    Inherited {
        hw: "hopper",
        arch: "sm_90a",
        cc: "9.0",
        provenance: "Hopper target: kernel set inherited from gb10 via symlink",
        models: P0_MODELS,
        blockscale_rejection: "cvt with .e2m1x2",
    },
    Inherited {
        hw: "b200",
        arch: "sm_100a",
        cc: "10.0",
        provenance: "B200 target: kernel set inherited from gb10 via symlink",
        models: P0_MODELS,
        blockscale_rejection: "mma with block scale",
    },
];

fn kernels_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crates/atlas-kernels is two levels below the workspace root")
        .join("kernels")
}

fn hw_dir(hw: &str) -> PathBuf {
    kernels_root().join(hw)
}

fn gb10_dir() -> PathBuf {
    kernels_root().join("gb10")
}

fn hardware_toml(hw: &str) -> toml::Value {
    let path = hw_dir(hw).join("HARDWARE.toml");
    let text = std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    toml::from_str(&text).unwrap_or_else(|e| panic!("bad TOML in {}: {e}", path.display()))
}

// ── (a) HARDWARE.toml ──

/// ORACLE: `build.rs::resolve_targets`, which reads exactly `hardware.arch`
/// (required, string) and `hardware.vendor` (steers `resolve_compute_target`
/// and the per-vendor KERNEL.toml flag key). `name` mirrors gb10's file.
///
/// The arch numbers are the point of the test. Hopper is SM 9.0 — `sm_100` is
/// Blackwell datacentre, not Hopper — and B200 is SM 10.0, which is neither
/// consumer Blackwell (`sm_120`) nor GB10 (`sm_121`) nor Blackwell Ultra
/// (`sm_103`). Getting one of those wrong produces a target that compiles and
/// cannot load.
#[test]
fn every_inherited_hardware_toml_declares_its_own_nvidia_arch() {
    for t in INHERITED {
        let toml = hardware_toml(t.hw);
        let hw = toml
            .get("hardware")
            .unwrap_or_else(|| panic!("kernels/{}: no [hardware] table", t.hw));
        assert_eq!(
            hw.get("name").and_then(|v| v.as_str()),
            Some(t.hw),
            "kernels/{}: [hardware].name must match the directory",
            t.hw
        );
        assert_eq!(
            hw.get("vendor").and_then(|v| v.as_str()),
            Some("nvidia"),
            "kernels/{}: vendor picks the compiler in \
             build_target::resolve_compute_target",
            t.hw
        );
        assert_eq!(
            hw.get("arch").and_then(|v| v.as_str()),
            Some(t.arch),
            "kernels/{}: arch is what reaches nvcc -arch=",
            t.hw
        );
        assert_eq!(
            hw.get("compute_capability").and_then(|v| v.as_str()),
            Some(t.cc),
            "kernels/{}: compute_capability is read by tests/target_hints.rs",
            t.hw
        );
    }
}

/// The keys gb10's HARDWARE.toml carries, each inherited target carries too.
/// The `memory_*` keys have no reader in the tree, so this pins the documented
/// shape rather than a behaviour, exactly as strix's file does. The strix
/// precedent is that an unread key must at least be honest: two were deleted
/// there for having no reader, and these survive as roofline/documentation
/// input.
///
/// `compute_capability` is no longer among them — `tests/target_hints.rs`
/// reads it and holds `atlas_core::arch::target_hint` to it, so the value has
/// to be right.
#[test]
fn every_inherited_hardware_toml_carries_the_same_key_set_as_gb10() {
    let gb10_path = gb10_dir().join("HARDWARE.toml");
    let gb10: toml::Value =
        toml::from_str(&std::fs::read_to_string(&gb10_path).expect("gb10 HARDWARE.toml"))
            .expect("valid TOML");
    let keys = |v: &toml::Value| -> std::collections::BTreeSet<String> {
        v.get("hardware")
            .and_then(|h| h.as_table())
            .expect("[hardware] table")
            .keys()
            .cloned()
            .collect()
    };
    for t in INHERITED {
        assert_eq!(
            keys(&hardware_toml(t.hw)),
            keys(&gb10),
            "kernels/{}/HARDWARE.toml must declare the same keys as the other \
             NVIDIA targets",
            t.hw
        );
    }
}

// ── (b) common/ — inherited from gb10 by relative symlink ──

/// ORACLE: `kernels/gb10/common`. Each inherited `common/` is that directory,
/// reachable — all 181 entries (171 `.cu`, 9 `.cuh` headers the `.cu` files
/// `#include`, and `KERNEL.toml`, which `build.rs` merges as the base layer of
/// every target's flags and `[modules]` overrides).
///
/// Unlike strix's curated 99, nothing is left out: these are NVIDIA targets
/// compiled by the same nvcc, so a file gb10 compiles is a file they must
/// compile, and a subset here would be an undocumented kernel drop.
#[test]
fn every_inherited_common_mirrors_every_gb10_common_file() {
    for t in INHERITED {
        let faults = mirror_faults(&hw_dir(t.hw).join("common"), &gb10_dir().join("common"));
        assert!(
            faults.is_empty(),
            "kernels/{}/common has drifted from kernels/gb10/common:\n  {}",
            t.hw,
            faults.join("\n  ")
        );
    }
}

/// The header files matter as much as the sources: `common/*.cuh` is what the
/// macro-declared kernels `#include`, and a missing one fails the compile of a
/// `.cu` that is itself present. Counted explicitly so a mirror that silently
/// became `.cu`-only is not read as "no faults".
#[test]
fn every_inherited_common_carries_the_headers_and_the_kernel_toml() {
    for t in INHERITED {
        let dir = hw_dir(t.hw).join("common");
        let mut by_ext = std::collections::BTreeMap::<String, usize>::new();
        for entry in std::fs::read_dir(&dir)
            .unwrap_or_else(|e| panic!("{}: {e}", dir.display()))
            .flatten()
        {
            let path = entry.path();
            let ext = path
                .extension()
                .map(|e| e.to_string_lossy().to_string())
                .unwrap_or_default();
            *by_ext.entry(ext).or_default() += 1;
        }
        assert!(
            dir.join("KERNEL.toml").exists(),
            "kernels/{}: KERNEL.toml is the flag base",
            t.hw
        );
        assert!(
            by_ext.get("cuh").copied().unwrap_or(0) > 0,
            "kernels/{}: no .cuh headers mirrored: {by_ext:?}",
            t.hw
        );
        assert!(
            by_ext.get("cu").copied().unwrap_or(0) > 100,
            "kernels/{}: suspiciously few .cu sources mirrored: {by_ext:?}",
            t.hw
        );
    }
}

// ── (c) the P0 model targets ──

/// Model directories under `kernels/<hw>`, by the rule `build.rs` uses to
/// expand `ATLAS_TARGET_MODEL=*`: a subdirectory that has a MODEL.toml.
fn model_dirs(hw: &str) -> Vec<String> {
    let mut names: Vec<String> = std::fs::read_dir(hw_dir(hw))
        .unwrap_or_else(|e| panic!("kernels/{hw}: {e}"))
        .flatten()
        .filter_map(|e| {
            let name = e.file_name().to_string_lossy().to_string();
            e.path().join("MODEL.toml").exists().then_some(name)
        })
        .collect();
    names.sort();
    names
}

/// ORACLE: [`P0_MODELS`], the campaign's declared P0 set. A wildcard build
/// (`ATLAS_TARGET_MODEL=*`) compiles exactly the directories that carry a
/// MODEL.toml, so this set IS what an image for that hardware would serve.
#[test]
fn the_p0_model_targets_are_the_ones_declared() {
    for t in INHERITED {
        assert_eq!(model_dirs(t.hw), t.models, "kernels/{}", t.hw);
    }
}

/// Each MODEL.toml is a REAL file (behaviour and sampling are a per-target
/// decision, not something to inherit by link) whose `[model].name` matches
/// its directory — the invariant `resolve.rs` reports targets by.
#[test]
fn every_model_toml_is_a_real_file_naming_its_own_directory() {
    for t in INHERITED {
        for model in t.models {
            let path = hw_dir(t.hw).join(model).join("MODEL.toml");
            assert!(
                std::fs::read_link(&path).is_err(),
                "{}/{model}/MODEL.toml is a symlink; per-target behaviour must be \
                 editable for this hardware without moving gb10",
                t.hw
            );
            let toml: toml::Value = toml::from_str(&std::fs::read_to_string(&path).unwrap())
                .unwrap_or_else(|e| panic!("bad TOML in {}: {e}", path.display()));
            assert_eq!(
                toml.get("model")
                    .and_then(|m| m.get("name"))
                    .and_then(|v| v.as_str()),
                Some(*model),
                "kernels/{}/{model}",
                t.hw
            );
        }
    }
}

/// The copied MODEL.toml must say where it came from and what has NOT been
/// done. `[expected_absent]` is harvested per hardware (`spark serve
/// --check-kernels` on the real device) and these tables were harvested on
/// GB10 — carrying them over silently would let a kernel that is genuinely
/// missing on this hardware read as an expected absence.
#[test]
fn every_model_toml_records_its_inherited_provenance() {
    for t in INHERITED {
        for model in t.models {
            let path = hw_dir(t.hw).join(model).join("MODEL.toml");
            let text = std::fs::read_to_string(&path).unwrap();
            let head: String = text.lines().take(6).collect::<Vec<_>>().join("\n");
            assert!(
                head.contains(t.provenance),
                "{}/{model}/MODEL.toml does not open with the inheritance note \
                 {:?}:\n{head}",
                t.hw,
                t.provenance
            );
            assert!(
                head.contains("--check-kernels"),
                "{}/{model}/MODEL.toml does not say expected_absent is unharvested \
                 on this hardware",
                t.hw
            );
        }
    }
}

/// ORACLE: `kernels/gb10/<model>/nvfp4`. Same mirror rule as `common/`, per
/// model: every file individually symlinked, so a future hardware-tuned kernel
/// replaces ONE link instead of forking the whole directory.
///
/// An `nvfp4` dir even where the hardware has no NVFP4 datapath (Hopper): the
/// runtime's weight-format gate is that an nvfp4-built bundle also serves FP8
/// and BF16 checkpoints, so FP8 checkpoints run through these kernels. An
/// `fp8/` quant dir would be a second name for the same files.
#[test]
fn every_model_nvfp4_dir_mirrors_gb10() {
    for t in INHERITED {
        for model in t.models {
            let faults = mirror_faults(
                &hw_dir(t.hw).join(model).join("nvfp4"),
                &gb10_dir().join(model).join("nvfp4"),
            );
            assert!(
                faults.is_empty(),
                "kernels/{}/{model}/nvfp4 has drifted from gb10's:\n  {}",
                t.hw,
                faults.join("\n  ")
            );
        }
    }
}

// ── (d) what build.rs would resolve ──

/// Mirror of `build.rs::resolve_targets` for the GPU-free runner, which never
/// reaches it: `ATLAS_SKIP_BUILD=1` returns from `main()` before target
/// resolution runs, so a hardware set can be structurally broken and every
/// existing test still passes.
///
/// Reproduces the parts that decide WHAT gets compiled — HARDWARE.toml `arch`,
/// the `MODEL.toml`-carrying subdirectory scan, the `[model] kernel_source`
/// redirect, and the default `nvfp4` quant — and returns `(model, quant, arch,
/// kernel dir)` per target.
fn resolved_targets(hw: &str, quant: &str) -> Vec<(String, String, String, PathBuf)> {
    let dir = hw_dir(hw);
    let arch = hardware_toml(hw)["hardware"]["arch"]
        .as_str()
        .unwrap()
        .to_string();
    model_dirs(hw)
        .into_iter()
        .map(|model| {
            let model_dir = dir.join(&model);
            let toml: toml::Value =
                toml::from_str(&std::fs::read_to_string(model_dir.join("MODEL.toml")).unwrap())
                    .unwrap();
            let src = toml
                .get("model")
                .and_then(|m| m.get("kernel_source"))
                .and_then(|v| v.as_str())
                .map(|s| dir.join(s))
                .unwrap_or(model_dir);
            let kernel_dir = src.join(quant);
            (model, quant.to_string(), arch.clone(), kernel_dir)
        })
        .collect()
}

/// A wildcard build of each inherited target resolves its five P0 targets, all
/// at that hardware's arch, each with a kernel directory that exists. This is
/// the assertion the real build would make on a CUDA host, made where CI can
/// actually run it.
#[test]
fn a_wildcard_build_resolves_five_targets_at_the_declared_arch() {
    for t in INHERITED {
        let targets = resolved_targets(t.hw, "nvfp4");
        let names: Vec<&str> = targets.iter().map(|(m, ..)| m.as_str()).collect();
        assert_eq!(names, t.models, "kernels/{}", t.hw);
        for (model, quant, arch, kernel_dir) in &targets {
            assert_eq!(arch, t.arch, "{}/{model}", t.hw);
            assert_eq!(quant, "nvfp4", "{}/{model}", t.hw);
            assert!(
                kernel_dir.is_dir(),
                "{}/{model}: no kernel directory at {}",
                t.hw,
                kernel_dir.display()
            );
        }
    }
}

/// No inherited MODEL.toml redirects with `kernel_source`. Redirects are a
/// WITHIN-hardware mechanism — `build.rs` resolves the name against
/// `kernels/<hw>/` — so one here would have to name another target in the same
/// hardware set, not a gb10 one. These sets reuse gb10 through the filesystem
/// instead, which is why the kernel dirs above resolve to their own paths.
#[test]
fn no_inherited_target_redirects_its_kernel_source() {
    for t in INHERITED {
        let targets = resolved_targets(t.hw, "nvfp4");
        assert!(!targets.is_empty(), "no {} targets resolved at all", t.hw);
        for (model, _, _, kernel_dir) in targets {
            assert_eq!(
                kernel_dir,
                hw_dir(t.hw).join(&model).join("nvfp4"),
                "{}/{model}: kernel_source redirect changes where kernels come from",
                t.hw
            );
        }
    }
}

// ── (e) the W4A4 opt-out ──

/// The define that compiles the warp-block-scale W4A4 path out.
const GUARD_FLAG: &str = "-DATLAS_NO_WARP_BLOCKSCALE_MMA";

/// The model whose kernel set contains that path, and the two entry points it
/// loses. ORACLE for the pair: the `extern "C" __global__` declarations inside
/// the `#ifndef` region of the gb10 source, checked below rather than trusted.
const GUARDED_MODEL: &str = "qwen3.6-35b-a3b";
const GUARDED_MODULE: &str = "moe_w4a16";
const GUARDED_KERNELS: &[&str] = &[
    "moe_w4a16_fused_gate_up_t_k64_fp4",
    "moe_w4a16_down_t_k64_fp4",
];

/// ORACLE: the two ptxas rejections measured on Spark 1 (CUDA 13.0.88),
/// receipts under `docs/campaigns/hopper-atlas-vs-vllm-2026-09/receipts/`.
/// Both targets define the guard; gb10 must NOT, because its PTX may not move.
#[test]
fn both_inherited_targets_compile_out_the_warp_block_scale_path() {
    for t in INHERITED {
        let flags = hardware_toml(t.hw)
            .get("build")
            .and_then(|b| b.get("extra_nvcc_flags"))
            .and_then(|f| f.as_array())
            .map(|a| {
                a.iter()
                    .map(|v| v.as_str().unwrap_or("").to_string())
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();
        assert!(
            flags.iter().any(|f| f == GUARD_FLAG),
            "kernels/{}/HARDWARE.toml must define {GUARD_FLAG}: ptxas rejects \
             the W4A4 region here with {:?}",
            t.hw,
            t.blockscale_rejection
        );
    }
    let gb10: toml::Value =
        toml::from_str(&std::fs::read_to_string(gb10_dir().join("HARDWARE.toml")).unwrap())
            .unwrap();
    assert!(
        gb10.get("build").is_none(),
        "kernels/gb10/HARDWARE.toml must add no flags — the W4A4 path is \
         compiled IN on GB10 and its PTX may not move"
    );
}

/// The kernels the define removes are exactly the `__global__` entry points
/// inside the guarded region of the gb10 source. Derived, not asserted from
/// memory: a third W4A4 entry point added inside the guard and not declared
/// below would otherwise reach the boot gate on Hopper as a required
/// unresolved lookup, which is the failure `[expected_absent]` exists to make
/// impossible.
#[test]
fn the_declared_absences_are_the_entry_points_the_define_removes() {
    let src = gb10_dir()
        .join(GUARDED_MODEL)
        .join("nvfp4/moe_w4a16_grouped_gemm.cu");
    let text = std::fs::read_to_string(&src).unwrap_or_else(|e| panic!("{}: {e}", src.display()));
    let (_, guarded) = text
        .split_once("#ifndef ATLAS_NO_WARP_BLOCKSCALE_MMA")
        .unwrap_or_else(|| panic!("{}: no guard", src.display()));
    let mut inside: Vec<&str> = guarded
        .lines()
        .filter_map(|l| l.strip_prefix("extern \"C\" __global__ void "))
        .filter_map(|l| l.split('(').next())
        .collect();
    inside.sort_unstable();
    let mut expected: Vec<&str> = GUARDED_KERNELS.to_vec();
    expected.sort_unstable();
    assert_eq!(
        inside,
        expected,
        "{}: the entry points inside the guard are not the ones both \
         MODEL.tomls declare expected-absent",
        src.display()
    );
}

/// Both targets declare both kernels in `[expected_absent.moe_w4a16]`, each
/// with a reason that names THAT architecture's ptxas rejection.
///
/// A bare declaration would silence the boot gate without recording why, and
/// the two reasons are genuinely different: Hopper has no NVFP4 datapath at
/// all, datacentre Blackwell has one and reaches it through tcgen05. A reader
/// who cannot tell those apart cannot tell which target a tcgen05 port would
/// fix.
#[test]
fn both_inherited_targets_declare_the_w4a4_kernels_expected_absent() {
    for t in INHERITED {
        let path = hw_dir(t.hw).join(GUARDED_MODEL).join("MODEL.toml");
        let toml: toml::Value = toml::from_str(&std::fs::read_to_string(&path).unwrap())
            .unwrap_or_else(|e| panic!("bad TOML in {}: {e}", path.display()));
        let table = toml
            .get("expected_absent")
            .and_then(|e| e.get(GUARDED_MODULE))
            .and_then(|m| m.as_table())
            .unwrap_or_else(|| panic!("{}: no [expected_absent.{GUARDED_MODULE}]", path.display()));
        for kernel in GUARDED_KERNELS {
            let reason = table
                .get(*kernel)
                .and_then(|v| v.as_str())
                .unwrap_or_else(|| panic!("{}: {kernel} is not declared", path.display()));
            assert!(
                reason.contains(t.blockscale_rejection),
                "{}: {kernel}'s reason does not name this architecture's ptxas \
                 rejection {:?}:\n{reason}",
                path.display(),
                t.blockscale_rejection
            );
            assert!(
                reason.contains("ATLAS_NO_WARP_BLOCKSCALE_MMA"),
                "{}: {kernel}'s reason does not say what compiles it out",
                path.display()
            );
        }
    }
}

/// gb10 declares NEITHER kernel absent: it compiles both, and a declaration
/// there would mean the guard had leaked onto the target it must not touch.
#[test]
fn gb10_declares_neither_w4a4_kernel_absent() {
    let path = gb10_dir().join(GUARDED_MODEL).join("MODEL.toml");
    let toml: toml::Value = toml::from_str(&std::fs::read_to_string(&path).unwrap()).unwrap();
    let table = toml
        .get("expected_absent")
        .and_then(|e| e.get(GUARDED_MODULE))
        .and_then(|m| m.as_table());
    for kernel in GUARDED_KERNELS {
        assert!(
            table.map(|t| t.get(*kernel).is_none()).unwrap_or(true),
            "{}: {kernel} is compiled on GB10 and must not be declared absent",
            path.display()
        );
    }
}
