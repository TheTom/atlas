// SPDX-License-Identifier: AGPL-3.0-only

//! `w4a16_prefill_variant`: the row that says WHICH W4A16 prefill GEMM
//! family a target dispatches.
//!
//! The lever exists because of one measurement: `PREFILL-ANALYSIS.md` section
//! 3.6 puts the R9700's projection GEMMs at ~1.07 TFLOP/s on
//! `w4a16_gemm_t_m128` and ~4.11 on the plain `w4a16_gemm`, inverting the
//! 7.3x GB10 ordering the ladder was built for. `"rdna4"` routes them to
//! `w4a16_gemm_rdna4` instead.

use super::*;
use crate::layers::ops::target_defaults::W4a16PrefillVariant;
use crate::layers::ops::w4a16_prefill_rdna4;

/// R9700 resolves the RDNA 4 family from its DECLARATION, with nothing in the
/// environment: which is the whole point of the table. NVIDIA targets resolve
/// the GB10 family from theirs.
#[test]
fn the_declaration_alone_picks_the_family() {
    let r = empty(&R9700);
    assert_eq!(r.w4a16_prefill_variant.value, W4a16PrefillVariant::Rdna4);
    assert!(!r.w4a16_prefill_variant.from_env());
    assert!(w4a16_prefill_rdna4::armed(r.w4a16_prefill_variant.value));

    for d in [&GB10, &HOPPER] {
        let l = empty(d);
        assert_eq!(l.w4a16_prefill_variant.value, W4a16PrefillVariant::Gb10);
        assert!(!l.w4a16_prefill_variant.from_env());
        assert!(
            !w4a16_prefill_rdna4::armed(l.w4a16_prefill_variant.value),
            "{} must not probe a kernel its tree does not compile",
            d.hw
        );
    }
}

/// `ATLAS_W4A16_PREFILL_VARIANT=gb10` is the A/B behind the r9700 default: it
/// puts that target back on the arm the analysis measured at ~1.07 TFLOP/s and
/// changes nothing else. The override is tagged in the serve log, because a
/// campaign that cannot tell a declaration from a prefix is the arrangement
/// this table replaced.
#[test]
fn the_environment_overrides_the_declaration_in_both_directions() {
    let back = with(&R9700, &[("ATLAS_W4A16_PREFILL_VARIANT", "gb10")]);
    assert_eq!(back.w4a16_prefill_variant.value, W4a16PrefillVariant::Gb10);
    assert!(back.w4a16_prefill_variant.from_env());
    assert!(!w4a16_prefill_rdna4::armed(
        back.w4a16_prefill_variant.value
    ));

    let forward = with(&GB10, &[("ATLAS_W4A16_PREFILL_VARIANT", "rdna4")]);
    assert_eq!(
        forward.w4a16_prefill_variant.value,
        W4a16PrefillVariant::Rdna4
    );
    assert!(forward.w4a16_prefill_variant.from_env());
}

/// Case and surrounding whitespace do not change the answer, the same
/// tolerance `resolve_toggle` gives every other lever, so a recipe written
/// with a capital letter is not a silently different serve.
#[test]
fn the_spelling_is_case_and_whitespace_insensitive() {
    let l = with(&GB10, &[("ATLAS_W4A16_PREFILL_VARIANT", "  RDNA4 ")]);
    assert_eq!(l.w4a16_prefill_variant.value, W4a16PrefillVariant::Rdna4);
}

/// A spelling the build does not know is a PANIC, not a silent fallback. An
/// operator running an A/B that is quietly not happening is the failure
/// `layers::w4a16_v2_kernel` already refuses to ship, and the message names
/// both accepted values so the fix does not need this file.
#[test]
#[should_panic(expected = "the spellings are `gb10` and `rdna4`")]
fn an_unknown_family_fails_loudly() {
    let _ = with(&GB10, &[("ATLAS_W4A16_PREFILL_VARIANT", "wmma")]);
}

/// The serve log reports the resolved family and where it came from. Without
/// this the `(env)` tag is the only thing separating "this target declares
/// rdna4" from "somebody exported a prefix", which is the distinction the
/// whole table exists to make.
#[test]
fn the_serve_log_names_the_family_and_its_source() {
    assert!(format_levers(&empty(&R9700)).contains("w4a16_prefill_variant=rdna4"));
    assert!(!format_levers(&empty(&R9700)).contains("w4a16_prefill_variant=rdna4 (env)"));
    assert!(format_levers(&empty(&GB10)).contains("w4a16_prefill_variant=gb10"));
    assert!(
        format_levers(&with(&R9700, &[("ATLAS_W4A16_PREFILL_VARIANT", "gb10")]))
            .contains("w4a16_prefill_variant=gb10 (env)")
    );
}

/// `ATLAS_W4A16_VARIANT` and `ATLAS_W4A16_PREFILL_VARIANT` are different
/// questions and must stay so. The first picks v1/v2/v3 WITHIN the GB10
/// family, and `ATLAS_W4A16_VARIANT=v1` is REQUIRED on gfx1201 because SCALE
/// has no e4m3 MMA codegen there (`kernels/r9700/HARDWARE.toml`). If the two
/// were folded, the one variable that target must set would silently start
/// meaning "and also serve the GB10 prefill family", i.e. it would undo this
/// row on the only target that has it.
#[test]
fn the_gb10_v1_v2_v3_variable_does_not_touch_this_lever() {
    let l = with(&R9700, &[("ATLAS_W4A16_VARIANT", "v1")]);
    assert_eq!(l.w4a16_prefill_variant.value, W4a16PrefillVariant::Rdna4);
    assert!(!l.w4a16_prefill_variant.from_env());
}
