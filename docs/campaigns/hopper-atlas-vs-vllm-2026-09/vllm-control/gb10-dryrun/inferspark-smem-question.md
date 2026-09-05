# GB10 Inferspark static shared-memory question

**NOT_RUN — Step B prerequisite blocked. No conclusion about driver JIT strictness or dead entry points is established.**

The overnight request reports 22 `inferspark_prefill*` entry points rejected by ptxas at `sm_121f` for static shared memory above 48 KB. That report has not been reproduced by this task. Step B's explicit 792579b pin predates the new architecture preflight while the current fork tip is 8b7405ca; target selection remains pending.

No release build or `--check-kernels` command ran, so this attempt has neither a generated `target/release/build/atlas-kernels-*/out/target_ptx.rs` nor a driver resolution report. The conditional Step C PTX command was therefore not executed. The final occupancy check also found an unowned compute process, so the idle-box prerequisite is false. Registry membership alone would not prove an entry point was loaded or resolved by the driver. Neither “ptxas is stricter” nor “these entry points are dead” follows from the available evidence.

After the target is selected and Step B finishes, preserve generated registry sources and the complete check-kernels report before removing `target/`. Then run the user-specified GB10 PTX gate on the idle box, join exact rejected entry-point names against the generated registry, and compare with real driver resolution evidence. These are required future observations, not results.

[Step C status](overnight-20260905/step-c.status.json) · [Step B status](overnight-20260905/step-b.status.json)
