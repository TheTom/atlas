// SPDX-License-Identifier: AGPL-3.0-only

//! Box-class ids — the strings a gate baseline is keyed by.
//!
//! A benchmark's thresholds live under `kernels/<hw>/<model>/BENCH.toml` and
//! are assembled into `GateBaseline.hardware`, keyed by the `<hw>` directory
//! name. Which key a run is scored against comes from two directions:
//!
//! * an operator typing `spark benchmark run <id> --hardware h100`, and
//! * a record's own fingerprint, via [`super::Hardware::gate_key`].
//!
//! Those two agreeing is not automatic. The baseline is only evidence of what
//! has ALREADY been measured, so it cannot answer "is `h100` a box class we
//! recognise?" — before the first Hopper run, an `h100` typed at the command
//! line and an `h800` typed by mistake look identical to it. They are not the
//! same situation: one is fixed by running the gate on the box, the other by
//! correcting the spelling, and a caller told the wrong one hunts for a typo
//! that is not there.
//!
//! [`KNOWN_HARDWARE_IDS`] is that registry — the ids Atlas recognises,
//! independent of what has been measured on them.

/// Every box class Atlas recognises, whether or not any gate has a record on
/// it yet.
///
/// SSOT for `--hardware` validation. An id belongs here once the project has
/// decided it is a class worth scoring separately — which is a threshold
/// question, not a hardware-availability one: two boxes share an id only if a
/// ceiling measured on one is meaningful on the other.
///
/// Kept in step with the `kernels/<hw>/HARDWARE.toml` directories by
/// `every_kernel_hardware_dir_is_registered` below. The list is deliberately
/// wider than that tree: `h100` and `h200` are registered before any Hopper
/// kernels land, so the resolver can tell an operator "no record yet" instead
/// of "unknown hardware" for the whole span of the porting campaign.
pub const KNOWN_HARDWARE_IDS: [&str; 6] = [
    // NVIDIA GB10 / DGX Spark — the box every committed record was measured on.
    "gb10",
    // NVIDIA Hopper. Two ids, not one: H200 is the same SM with 141 GB of
    // HBM3e at 4.8 TB/s against H100's 80 GB at 3.35 TB/s, and every metric a
    // gate carries (TTFT, TPOT, node tok/s) moves with memory bandwidth. One
    // shared id would score an H100 run against H200 numbers.
    "h100",
    "h200",
    // Apple Silicon, via the Metal backend.
    "metal",
    // AMD Strix Halo — Vulkan and HIP are separate targets and separate
    // classes; the same silicon through two backends does not produce
    // interchangeable numbers.
    "strix",
    "strix-hip",
];

/// True when `id` names a box class Atlas recognises.
///
/// Case- and shape-sensitive on purpose: the id is a directory name and a
/// baseline key, so `H100` is not `h100` any more than it is on disk.
pub fn is_known_hardware_id(id: &str) -> bool {
    KNOWN_HARDWARE_IDS.contains(&id)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Oracle: the registry's own contract — the ids the Hopper campaign types
    /// at `--hardware` must be recognised before the first record exists, or
    /// the resolver cannot distinguish "go measure it" from "you typoed".
    #[test]
    fn the_hopper_slots_are_registered_before_they_are_measured() {
        assert!(is_known_hardware_id("h100"));
        assert!(is_known_hardware_id("h200"));
        assert!(is_known_hardware_id("gb10"));
    }

    /// Oracle: the same contract, negative side. `h800` is a real NVIDIA part
    /// that Atlas has never registered, and `H100` is the right part spelled
    /// the wrong way — a baseline key is a directory name, so case matters.
    #[test]
    fn an_unregistered_or_miscased_id_is_not_known() {
        assert!(!is_known_hardware_id("h800"));
        assert!(!is_known_hardware_id("H100"));
        assert!(!is_known_hardware_id(""));
        assert!(!is_known_hardware_id("b200"));
    }

    /// Oracle: the `kernels/<hw>/HARDWARE.toml` tree — the thing that actually
    /// produces baseline keys (`gate::bench::load_all`).
    ///
    /// A backend whose kernels are in the tree but whose id is not registered
    /// would have its `--hardware` refused as "unknown" the moment its last
    /// BENCH.toml entry went `unmeasured`. Registration is one line; noticing
    /// that regression from a benchmark refusal is not.
    #[test]
    fn every_kernel_hardware_dir_is_registered() {
        let kernels = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../kernels");
        let mut found = Vec::new();
        for entry in std::fs::read_dir(&kernels)
            .expect("kernels/ is in the tree")
            .flatten()
        {
            if !entry.path().join("HARDWARE.toml").exists() {
                continue;
            }
            let name = entry.file_name().to_string_lossy().to_string();
            assert!(
                is_known_hardware_id(&name),
                "kernels/{name}/ declares a HARDWARE.toml but {name:?} is not in \
                 KNOWN_HARDWARE_IDS; add it there or --hardware {name} reads as a typo"
            );
            found.push(name);
        }
        assert!(
            !found.is_empty(),
            "read no hardware dirs at all — the walk is broken, not the registry"
        );
    }
}
