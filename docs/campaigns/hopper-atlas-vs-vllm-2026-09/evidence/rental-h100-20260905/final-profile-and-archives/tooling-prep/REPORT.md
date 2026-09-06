# Record the existing multi-sequence profiler

Commit `73809eafe8fa0bf0c4ad3bccdfe908dc242f20b4`, base `7c786cc50455dee52c11c3bf4097de945fbb8f6a`, tree `072708d1df73c0bdcebf449512db7c40b61426ef`. Only the environment allowlist and its tests change. There are no crate, kernel, schema, threshold, recipe or ladder edits and no rebuild is required.

The production environment function rejected ATLAS_MS_PROFILE before the change. The new cross-platform regression reproduced that error for values0 and1; unknown-key refusal already passed. After adding the one key, both tests pass; unknown keys still fail. The Linux actual-process snapshot/capture test now includes this flag. On Mac it is among the14 explicitly skipped Linux-only tests; it has not been claimed as observed Linux evidence here.

Full Mac campaign suite:85 assertions passed, including shellcheck, Python compilation, JSON parsing and typos. Process suite:2 passed,14 skipped. The parent's final Linux process suite must complete after remaining measured sessions stop.

## Prepared diagnostic

After the parent's destination guard, upload `run_qwen38_ms_profile.sh` to `/workspace/atlas-rental/` and deploy the exact tooling tree above. Then under an exclusive GPU diagnostic lease:

```sh
bash /workspace/atlas-rental/run_qwen38_ms_profile.sh msprofile01 --execute
```

The label must be unused. Without --execute the wrapper only prints a plan. It requires the exact tooling tree and copies `benchmark.qwen38.atlas.native-head-lat01/serve.argv` byte-for-byte. That pins the original native-FP8 configuration, BF16 head, max batch4 and unchanged7c binary (verified SHA256). It adds only ATLAS_MS_PROFILE=1 to the captured environment.

Existing GPU/port admission precedes launch. Boot has90seconds; the unchanged17 arithmetic probe has60seconds. A GNU timeout sends TERM at210seconds and allows30seconds for the owner-aware cleanup trap, for a240second outer cap. No retry or frozen ladder runs. Outputs live in `results/diagnostic.qwen38.msprofile.msprofile01/`, including exact argv/env, boot, ownership capture, raw quality exchanges, raw serve log, grouped profiler summary, stop result and before/after disk/GPU telemetry.

The parser requires an actual n4/padded4 observation. A synthetic n2-only log was red (exit2), then an n4 log was green (exit0) with exact expected bucket values. This validates parsing only. Shell syntax, shellcheck and typos pass; the existing arithmetic oracle selftest rejects9 known-bad cases before2 acceptances. This agent has not run the real diagnostic.

The profiler disables multi-sequence graphs and measures synchronized device-inclusive wall time with host launch/sync overhead. SSM and attention buckets include their complete transformer blocks, including FFN; the head bucket includes final normalization. Report distributions/step counts separately by n and padded_n. These times are attribution evidence, not comparable frozen throughput or pure CUDA-event measurements. Preserve the existing original coherency failure and explicit reversal exception.
