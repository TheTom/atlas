# CI follow-up: sanitizer pipe failure and unavailable Metal compiler

Observed September 6, 2026 on PR #895 at `64b468bf2d0602c9695dfb09f667e7608352cac6`. The rental remains destroyed. This work uses local CPU checks and Spark 1 CPU-only shell/PTX tests; it adds no GPU performance result.

## Fixed: long PR bodies can abort categorization

[The advisory categorization job](https://github.com/Avarok-Cybersecurity/atlas/actions/runs/34014529502/job/101438934720) failed during `Sanitize the PR body` with exit 1 and `Unable to flush stdout: Broken pipe`. Its pipeline writes sanitized text through `head -c 2000`. The early-closing consumer can break the upstream writer, and `set -euo pipefail` correctly treats that as failure.

[Commit e12295a](https://github.com/Avarok-Cybersecurity/atlas/commit/e12295af5dfbd3a7f08320b0aecb5b93b4cdf67a) moves the byte truncation into the existing Perl process, after comment removal. The process already consumed its full input with `-0777`; the change does not add a new unbounded read. Control stripping, the 2,000-byte limit, literal treatment of PR text, randomized output framing and real failure propagation remain intact. CI now executes six regression tests against the actual workflow step before processing a PR body.

Oracle: every valid body must produce exactly its sanitized first 2,000 bytes and a complete `GITHUB_OUTPUT` record; a real upstream error must still stop the step. The defect is timing-dependent: single attempts with 60,000 bytes and with the actual 11,567-byte PR body passed locally. Those observations are retained. A Linux input sweep then reproduced exit 141 with missing workflow output; the regression suite reproduced five failing boundary cases before the fix.

```text
Before, Spark 1 CPU-only:
python3 scripts/ci_pr_body_test.py
Ran 6 tests in 0.167s
FAILED (failures=5)
AssertionError: 141 != 0

After, Spark 1 CPU-only:
python3 scripts/ci_pr_body_test.py
Ran 6 tests in 0.159s
OK
```

The same six tests pass on macOS. Coverage includes 24 trials across byte/pipe boundaries, empty/short/newline framing, control characters and multiline HTML comments, UTF-8 byte truncation, inert shell metacharacters, and a producer failure that must retain exit 73. Stopping rule: observe the old workflow fail, execute the unchanged tests green on Linux and macOS, pass required checks and publish; await the GitHub rerun.

## Blocked on runner setup: real Metal compilation

[The Metal rerun](https://github.com/Avarok-Cybersecurity/atlas/actions/runs/34014529502/job/101444073917) used the corrected `ATLAS_SKIP_BUILD=0` setting on `apple-48gb-metal`. Both compile-only checks passed, then real kernel compilation failed before any parity tests ran:

```text
xcrun: error: unable to find utility "metal", not a developer tool or in PATH
Kernel compilation failed:
xcrun metal compile failed for .../kernels/metal/common/noop_smoke.metal
Process completed with exit code 101.
```

The previous empty-registry defect is fixed; this rerun exposes a separate toolchain availability problem in the runner environment. The log does not distinguish a missing installation from an incorrect developer-directory selection. The workflow's existing comment claiming the compiler is supplied by Command Line Tools is insufficient evidence that this runner has it.

The runner owner should record the following under the same account/environment as the Actions service:

```sh
xcode-select -p
xcodebuild -version
xcrun --sdk macosx --find metal
xcrun --sdk macosx --find metallib
xcrun --sdk macosx metal --version
```

Select a complete installed Xcode toolchain as appropriate for that host. For Xcode versions using separate components, Apple documents `xcodebuild -downloadComponent metalToolchain` in [Downloading and installing additional Xcode components](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components). This is an owner provisioning instruction, not an operation performed on the shared runner.

Oracle: compiler discovery succeeds and the real Metal parity job passes with no backend skips. Local Apple Metal previously passed 35 tests with five checkpoint-dependent tests ignored, but that does not prove the CI runner is repaired. Stopping rule: record the exact build failure and owner action; do not restore stubs, skip the job, relax the gate or attempt undocumented access to the shared runner.

## Other checks and cleanup

Required checks on the sanitizer fix all pass: campaign 85, launcher 30, PTX 7, datacenter Dockerfiles 17, Atlas renderer 346/346, vLLM renderer 258/258, artifact validator 26/26 and assembler 16/16. Formatting, typos, relevant shellcheck, workflow syntax and diff checks exit 0. The optional shellcheck inside the Spark 1 PTX suite is unavailable there; both PTX scripts pass the local warning-level shellcheck. No runtime, kernel or performance gate paths changed.

The owned Spark 1 fixture directory (4.6 MB) was removed; disk reads 80 GB available before and after cleanup. No warm checkout, GPU, Spark 2 or rental access occurred. Raw commands and results are adjacent, with required-check receipts in `prepush/` and a SHA256 manifest.

The current-head seal job reports no codeowner Seal. This remains a maintainer requirement, unchanged from the prior audit. Hopper/B200 x86_64 compilation, docs, coverage and B200 PTX checks passed at this head. Compilation status does not establish artifact runtime correctness, GPU results or a performance certification.
