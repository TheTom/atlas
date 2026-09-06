# Record existing SSM detail profiler switches

Commit58d38ef5bb5582c33c145da62de077293fbeab19, basef08d4eafb3f56e2168bfc993a657191a4e424a1e, treeb20f14a38ba36a1ed87a12d14fd3a7d9fa4325cf. Only the process environment allowlist and tests change; no engine/kernel/schema/threshold/ladder edit or rebuild.

Actual production launch_environment rejected both ATLAS_SSM_MS_PROFILE and ATLAS_SSM_DETAIL_PROFILE for values0/1 before the addition. The same tests then passed; unlisted keys still refuse. The Linux process snapshot/capture test includes both new switches. Mac result:2 platform-independent tests passed,14 Linux-only tests explicitly skipped. Full campaign suite:85 assertions passed, including shellcheck, Python compilation and typos. Root owns subsequent Linux process verification.

## Prepared run

After the destination guard, deploy the exact tooling tree and upload `run_qwen38_ssm_detail_profile.sh`. Under the root's exclusive GPU lease:

```sh
bash /workspace/atlas-rental/run_qwen38_ssm_detail_profile.sh detailprofile01 --execute
```

The script reuses the exact7c measured binary (SHA256 verified) and copies the native-head-lat01 argv byte-for-byte. The only added environment entries are ATLAS_MS_PROFILE=1, ATLAS_SSM_MS_PROFILE=1 and ATLAS_SSM_DETAIL_PROFILE=1. The outer hook disables multi-sequence graph capture, which is required because both inner hooks require !ctx.graph_capture.

Admission,90second boot cap, unchanged17 arithmetic probe with60second cap, ownership capture and cleanup are retained. Outer limit is210seconds plus30seconds cleanup allowance. Output goes to `results/diagnostic.qwen38.ssmdetail.detailprofile01/`. No engine request was executed by this agent.

`profile-summary.json` retains whole SSM/attention/head groups. `ssm-subphase-summary.json` retains every raw phase/detail log line and groups by actual n. The whole-layer inner split is mixer versus the legacy named moe_residual bucket, which for this dense Qwen model contains FFN/residual work. Detail labels include input_norm, qkvz, recurrent_ba/conv/gdn/norm (or the existing batched variants), recurrent_total_tail, out_proj and post_norm. Missing labels are not filled with zeros. Required actual C4 subphase observations must exist or the wrapper exits2.

The parser first rejected a synthetic outer-C4 log lacking inner subphases, then accepted a complete synthetic log with exact expected mixer100us/FFN200us and recurrent_gdn5us. These are parser fixtures, not GPU measurements. Shell syntax, shellcheck, typos and dry planning passed. Wrapper SHA256 and all receipts are in receipt.json.

These nested synchronized wall times include host launch/sync and logging overhead. No frozen throughput or device-exclusive timing claim is made. On the per-sequence recurrence path the helper resets its timer after adding recurrent labels, so recurrent_total_tail is the post-return tail; inspect exact observed labels and source before adding times. Phase/detail logs lack layer IDs: group by invocation and batch width, not an invented layer identity.
