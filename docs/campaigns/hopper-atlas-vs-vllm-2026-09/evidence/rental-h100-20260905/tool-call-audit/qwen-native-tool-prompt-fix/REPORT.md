# Native Qwen tool prompt duplication

Local fix commit: `387e5e885db2f08a3f4491f940c9ec375d106425`. No remote GitHub writes performed by this agent.

The same weather request was observed as 1135 prompt tokens in Atlas and 320 in vLLM. Atlas inserts the qwen3_coder parser's long system prompt, then renders the checkpoint template with tools again. The production CPU regression reproduced two `# Tools` sections before the fix and failed with exit 101. A second negative control caught a custom checkpoint template with no tools support being classified as native; this also failed before adding conservative MiniJinja AST capability detection.

The fix suppresses the duplicate parser schema and unrelated Bash/Write/Edit guidance only for known Qwen3.5/3.6 checkpoint templates that reference `tools`, with no custom/openai override, under qwen3_coder/qwen3_xml and TSCG off. Required/named tool-choice instructions remain. Hermes, other parsers, fallback/custom templates, and TSCG retain their existing contribution. An unchanged normalization helper moved into existing helpers_a to keep edited source files at or below 500 lines. The obsolete contradictory comment claiming injection was globally removed was corrected.

The real checkpoint tokenizer, used offline with CUDA_VISIBLE_DEVICES empty, counted the production-rendered old request as 1135 tokens, corrected native compact JSON as 298, and native HF spaced JSON as 320. The remaining 22-token gap is existing explicit serialization policy. It was not silently changed or described as engine byte parity. No real GPU result for the fix is asserted here.

Validation: 52 tokenizer tests passed, including five new production-path/capability regressions; 154 parser tests passed with one pre-existing ignored test that mutates process-global ATLAS_BUFFER_TOOL_ARGS; four existing chat-prepare tests passed. Formatting, typos and diff checks passed. Every edited .rs file is at most 500 lines. These CPU checks used an owned Spark1 worktree and its permitted shared Cargo target. No GPU calls or HTTP requests were issued. File hashes in remote-tested-files.json prove the tested source matched the local committed source despite remote worktree Git metadata retaining its original detached base.

Read red/green stdout/stderr and exit files for actual observations. `offline-count.json` and `red-rendered-prompts.json` retain the exact prompt evidence. `local-checks.json` contains commands and hashes. The original Atlas/vLLM refrigerator coherency failures remain unchanged and both are failures; matching wrong answers did not justify an Atlas-only numerical defect claim.

## Broad validation follow-up

Validation includes TTFT fix ad852945 on top of the native-prompt fix. An unrestricted `cargo test --no-default-features -p spark-server` failed to compile: it exposed our test's registration in the thin library (fixed by local follow-up commit `4823185256cbece103062020754892dd29f1a998`) plus existing backend-less binary/integration imports. The files behind those latter errors are byte-identical to 231d869; they were not patched as part of the tool-prompt work. That unsupported invocation did not pass; its failure logs are preserved. The supported default-feature invocation was validated separately below.

After the registration fix, all 104 thin-library tests passed using `--lib --no-default-features`; the five relocated binary-native-prompt tests passed with default features and GPU visibility empty. Workspace rustdoc passed on the combined source and again after registration correction. All logs, command arguments and failure stderr remain in broad-*, library-cpu-green.*, binary-registration-green.* and final-workspace-rustdoc.*. `final-validation.json` binds this to source trees. At that point, default-feature package validation remained pending; it has since passed under the authorized CPU-only setup below.

## Supported full package validation

The final combined `crates` tree `0e29321a193cc2fe923b1cfe778f390e4d0bf279`, as present in parent commit `57d9c1cfbaf851afa1255653aba80715681ae058`, passed the unfiltered supported default-feature package command on Spark1:

```bash
CUDA_VISIBLE_DEVICES="" ATLAS_SKIP_BUILD=1 CUDARC_CUDA_VERSION=13000 \
CARGO_TARGET_DIR=/home/pidtom/atlas-hopper-gate-full/target \
cargo test --locked -p spark-server
```

Observed exit 0: 104 library tests, 2,347 binary tests, and three closure-attestation tests passed (2,454 total). There were no failures or filtered tests. Twelve binary tests and all six live-GPU integration tests were ignored by their existing annotations. The empty doc-test target passed. Workspace rustdoc had already passed on this same crates tree. The test suite was not run with `--ignored`. Read `supported-default-full-cpu.stdout` and `.stderr` for the raw counts, and `.command.json` for the exact SSH invocation.

Before execution, the live model tests were traced to `setup_model` and CUDA backend initialization, and all six were confirmed `#[ignore]`. TUI tests were included after inspecting their `ThermalProbe`: `hardware::collect` performs only passive nvidia-smi queries plus proc/sys reads, without launching compute, creating a CUDA context, changing clocks or allocating GPU memory. This passive telemetry is permitted under the clarified Spark1 CPU-only rule. The `/gpu` unit command is explicitly absent from its test module. This gate proves CPU regression coverage with compiled PTX stubs; it does not claim live kernel validation or successful execution of the ignored model tests.

All 1,982 tracked crate, root Cargo/toolchain and native-template fixture files matched SHA-256 between the local parent snapshot and the remote owned worktree (`supported-default-source-verify.json`, zero mismatches). The owned Spark1 worktree was then removed; the production checkout and shared warm Cargo target were preserved. Recorded root free space was 5.2G before cleanup and 5.3G after (`supported-default-cleanup.stdout`). The stopping rule for this validation step is satisfied: the supported unfiltered package suite and workspace rustdoc both exited 0 on the final combined crate tree.
