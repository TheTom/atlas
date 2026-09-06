// SPDX-License-Identifier: AGPL-3.0-only

//! The `ATLAS_NO_WARP_BLOCKSCALE_MMA` opt-out on the targets that inherit
//! `kernels/gb10`'s kernels, and the `[expected_absent]` declarations that
//! answer it.
//!
//! Split out of `inherited_targets.rs` at the 500-LoC cap. That binary pins the
//! tree as MIRRORED — every inherited file is gb10's file, reachable. This one
//! pins the single place an inherited tree may deliberately DIVERGE from gb10:
//! ptxas rejects the warp-block-scale W4A4 region on sm_90a and sm_100a, so
//! those two targets compile it out, and each must then declare the two entry
//! points it loses with a reason naming its OWN rejection.
//!
//! It is a per-target property, not a property of inheriting: `rtx-pro-6000`
//! is sm_120a, the architecture the warp-level
//! `mma.sync ... .kind::mxf4nvf4.block_scale` was introduced ON, so it keeps
//! the whole kernel set. Both halves are asserted — a target whose
//! `blockscale_rejection` is `None` must define NO extra nvcc flag and declare
//! NEITHER entry point absent, exactly as gb10 does. Silently skipping it
//! would let the macro be added to a target that can run the kernels, deleting
//! two of them, with nothing red.
//!
//! Parametrised over [`INHERITED`] from `support/inherited.rs` — the same
//! declaration `inherited_targets.rs` reads, so a target added to one binary
//! cannot be missed by the other.
//!
//! `cargo test` runs GPU-free with `ATLAS_SKIP_BUILD=1`, where `build.rs`
//! returns before target resolution ever happens, so without this file nothing
//! in CI looks at either tree at all.

#[path = "support/inherited.rs"]
mod inherited;

use inherited::{INHERITED, gb10_dir, hardware_toml, hw_dir};

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
/// receipts under `docs/campaigns/hopper-atlas-vs-vllm-2026-09/receipts/`, and
/// — for the target that declares none — CUTLASS's own
/// `CUTLASS_ARCH_MMA_SM120_SUPPORTED` gate, which is exactly the architecture
/// the warp-level form exists on.
///
/// The targets that cannot assemble the region define the guard; the one that
/// can must add NO flags at all, and neither must gb10, whose PTX may not
/// move. A stray flag on an sm_120a target is not a harmless extra define: it
/// removes two kernels the hardware runs.
#[test]
fn each_inherited_target_guards_the_block_scale_path_only_if_its_isa_must() {
    for t in INHERITED {
        let toml = hardware_toml(t.hw);
        let build = toml.get("build");
        let flags = build
            .and_then(|b| b.get("extra_nvcc_flags"))
            .and_then(|f| f.as_array())
            .map(|a| {
                a.iter()
                    .map(|v| v.as_str().unwrap_or("").to_string())
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();
        let Some(rejection) = t.blockscale_rejection else {
            assert!(
                build.is_none(),
                "kernels/{}/HARDWARE.toml must add no flags — sm_120a HAS the \
                 warp-level block-scaled MMA, so the kernel set is gb10's \
                 whole, got {flags:?}",
                t.hw
            );
            continue;
        };
        assert!(
            flags.iter().any(|f| f == GUARD_FLAG),
            "kernels/{}/HARDWARE.toml must define {GUARD_FLAG}: ptxas rejects \
             the W4A4 region here with {rejection:?}",
            t.hw
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

/// A target that compiles the region OUT declares both kernels in
/// `[expected_absent.moe_w4a16]`, each with a reason that names THAT
/// architecture's ptxas rejection; a target that compiles them IN declares
/// neither.
///
/// A bare declaration would silence the boot gate without recording why, and
/// the reasons are genuinely different: Hopper has no NVFP4 datapath at all,
/// datacentre Blackwell has one and reaches it through tcgen05. A reader who
/// cannot tell those apart cannot tell which target a tcgen05 port would fix.
/// The negative side matters as much — declaring a kernel absent on hardware
/// that HAS it turns a real gap into an expected one, silently, which is the
/// whole failure `[expected_absent]` is auditing for.
#[test]
fn each_inherited_target_declares_exactly_the_w4a4_kernels_it_loses() {
    for t in INHERITED {
        let path = hw_dir(t.hw).join(GUARDED_MODEL).join("MODEL.toml");
        let toml: toml::Value = toml::from_str(&std::fs::read_to_string(&path).unwrap())
            .unwrap_or_else(|e| panic!("bad TOML in {}: {e}", path.display()));
        let table = toml
            .get("expected_absent")
            .and_then(|e| e.get(GUARDED_MODULE))
            .and_then(|m| m.as_table());
        let Some(rejection) = t.blockscale_rejection else {
            for kernel in GUARDED_KERNELS {
                assert!(
                    table.map(|t| t.get(*kernel).is_none()).unwrap_or(true),
                    "{}: {kernel} COMPILES on sm_120a and must not be declared \
                     absent — a declaration here hides a real gap",
                    path.display()
                );
            }
            continue;
        };
        let table = table
            .unwrap_or_else(|| panic!("{}: no [expected_absent.{GUARDED_MODULE}]", path.display()));
        for kernel in GUARDED_KERNELS {
            let reason = table
                .get(*kernel)
                .and_then(|v| v.as_str())
                .unwrap_or_else(|| panic!("{}: {kernel} is not declared", path.display()));
            assert!(
                reason.contains(rejection),
                "{}: {kernel}'s reason does not name this architecture's ptxas \
                 rejection {rejection:?}:\n{reason}",
                path.display()
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
