# Comment-only conflict with upstream Metal CI explanation

On September 6, 2026, GitHub reported PR #895 as `CONFLICTING` / `DIRTY` at head `e12295a`. A fresh fetch of upstream main returned `3dc4369ced28207788487cc53747c115ff242c31`. The GitHub PR API's recorded base SHA remained `567b5eb`; both observations are retained rather than assuming they were identical.

`git merge-tree --write-tree --name-only HEAD 3dc4369ced28207788487cc53747c115ff242c31` returned **1**, naming only `.github/workflows/ci.yml`. The conflict was the comment above `ATLAS_SKIP_BUILD: "0"`: both branches enable the same real Metal build, but use different explanations. Upstream's explanation arrived with its runner changes. `kernel-compile.yml` merged automatically.

Commit `201a136` adopts the upstream comment exactly. No YAML value, test, runtime path or performance gate path changes. This is a normal additional commit; no merge commit or published-history rewrite is needed.

Oracle: the same merge-tree comparison must return 0 without conflicts, and the parsed workflow must equal its parent when comments are excluded. Both pass. The green comparison returned tree `f1c2ee3670776b0ebdc7e53ef44c08f5ab6296eb`. `merge-tree` only computes a prospective merge; it does not merge branches or update the checkout.

Required checks pass before publication: campaign 85, launcher 30, PTX 7, Dockerfiles 17, Atlas renderer 346, vLLM renderer 258, validator 26, assembler 16 and sanitizer 6. Formatting, typos, workflow syntax and diff checks pass. The recorded checks and YAML equality receipt are under `prepush/`. The optional shellcheck inside the PTX suite is unavailable on Spark 1; no shell file changed. The Spark 1 PTX fixture directory is removed within the same command, with 80 GB free before and after. No GPU or rental work occurs.

Stopping rule: observe the conflict, match the identical upstream explanation, prove a clean prospective merge and unchanged YAML behavior, then publish normally after required checks. Rebase only onto the existing campaign branch tip before pushing; do not merge main or force-push.

## Benchmark check is held for maintainer release

[PR benchmark gate job 101450442165](https://github.com/Avarok-Cybersecurity/atlas/actions/runs/34019156276/job/101450442165) returns exit 1 at its `/stamp` requirement. Its log states that certification and release-matrix builds are held pending that action. No benchmark regression or threshold failure was reported by this job. Keep thresholds and gate logic unchanged; maintainers own stamping and sealing.

The previously reported Metal compiler availability and missing-Seal failures remain owner dependencies. The sanitizer fix is already confirmed in GitHub CI. This audit adds no new performance claim.
