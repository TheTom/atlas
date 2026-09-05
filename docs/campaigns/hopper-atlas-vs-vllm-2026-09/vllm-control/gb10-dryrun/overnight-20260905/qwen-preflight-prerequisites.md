# Qwen overnight preflight prerequisites

The requested checkpoint requires **23,444,511,857 logical bytes (23.44 GB;
21.83 GiB)** for all 13 repository files at revision
`57926baca9a82b4d6906b43f2750d55315f5b10f`. The approximate 15 GB estimate
does not match the current inventory. Atlas `--check-kernels` loads weights
before auditing kernel lookups, so this checkpoint's audit cannot precede its
weight download unless a complete local copy already exists.

This is a source and metadata investigation for the GB10 rehearsal, not a
Hopper result or a runtime audit result. The coordinator reported that the
default Qwen HF cache on Spark2 was absent at `2026-09-05T05:02:36Z`; this
does not establish absence from every possible location. At documentation
handoff, the coordinator also reported that no Step B build had started while
the user's target question remained pending. These are coordinator-reported
observations, not independent hardware checks by this subtask.

## Metadata receipt and storage accounting

The unauthenticated [HF API request](https://huggingface.co/api/models/unsloth/Qwen3.8-27B-NVFP4?blobs=true)
returned HTTP 200 at `2026-09-05T04:59:59.102365+00:00`. The repository was
public and ungated. [qwen-weights-manifest.json](qwen-weights-manifest.json)
contains all 13 filenames, exact sizes, Git blob IDs, available LFS payload
SHA256 values and pointer sizes, response headers, source URL, timestamp,
revision, and the original API response's SHA256. The response body was not
saved as a raw file during the read-only investigation; the manifest is an
extracted metadata receipt and its hash is not the response-body hash.

| Payload category | Logical bytes |
|---|---:|
| `model.safetensors` | 22,568,192,096 |
| `model_mtp.safetensors` | 849,400,392 |
| All safetensors | 23,417,592,488 |
| All remaining files | 26,919,369 |
| Complete repository | 23,444,511,857 |

Totals sum `siblings[].size`; each LFS size agrees with its `lfs.size`.
The full-repository figure includes the MTP file, without assuming whether
this particular runtime will use it. API-advertised payload hashes have not
been verified against downloaded model files. Git blob IDs have Git object
hash semantics; LFS pointer IDs must not be mistaken for payload hashes.

These totals exclude filesystem allocation overhead, cache metadata,
incomplete transfers, Xet caches, dependencies, logs, and duplicate copies.
Measure the whole task directory and filesystem free space during the actual
download; the logical sum alone does not establish compliance with a disk
budget or a minimum-free-space requirement.

## Exact Atlas startup ordering

Source inspection used immutable commit
`8b7405ca159a6ab8bb3e593a740f4d20f93996fd`, resolved from
`fork/hopper/sm90-target-tdd-2026-09`. All source paths and line numbers below
refer to that object, read through `git show`/`git grep`, rather than the
concurrently changing checkout. Revalidate if the executable is built from a
different commit.

| Order | Source within `crates/spark-server/src/` | Action |
|---|---|---|
| 1 | `main_modules/serve.rs:143`, `:179` | Validate serve arguments, then call `load_model`. |
| 2 | `main_modules/serve_load.rs:99` | Resolve the model directory from a supplied path or the local HF cache. |
| 3 | `main_modules/serve_load.rs:120`, `:148` | Read/parse configuration and the optional HF quantization sidecar. |
| 4 | `main_modules/serve_load.rs:290` | Select the compiled target using configuration and model identity. |
| 5 | `main_modules/serve_load.rs:376` | Initialize the GPU backend. |
| 6 | `main_modules/serve_load.rs:428` | Load the actual weight store. |
| 7 | `main_modules/serve_load.rs:718` | Construct the model, including the kernel lookups to be audited. |
| 8 | `main_modules/serve_load.rs:745` | Run `audit_and_gate`. |
| 9 | `main_modules/serve_phases/kernel_gate.rs:58` | Handle `check_kernels` and exit through the check report path. |

The CLI documentation at `cli/serve_args.rs:93–97` explicitly describes
configuration, GPU initialization, weight loading, and model construction as
part of this check. It stops before the scheduler starts or a port is bound.
At `main_modules/serve_phases/kernel_gate.rs:127`, the check prints a one-line
`{"atlas_kernel_check": ...}` report before exiting. The audit exit code is
the unresolved count clamped to 255, regardless of the dangerous-allow flag.
A startup error before this report is not a kernel-audit verdict.

`main_modules/serve_phases/config.rs:76–88` gives `--model-from-path`
precedence over the positional model for filesystem resolution.
`model_resolver.rs:33–145` first accepts an existing local model directory
with configuration; otherwise, it resolves an HF ID using local cache files.
The ID route requires `models--ORG--NAME/refs/main`, the referenced snapshot,
configuration, and real safetensors. It performs no automatic HF download.
If the referenced snapshot lacks weights, it can choose another weighted
sibling snapshot. A metadata-only local directory may pass path resolution
but will fail weight loading before the audit.

Therefore, a Qwen-specific `spark serve ID --check-kernels --no-tui` cannot
provide a pre-download registry verdict on a machine without these weights.
An audit against another cached checkpoint would establish only that other
checkpoint's result. This finding does not choose the pending build hardware
target or authorize a Step B build.

## Task-owned download and cache isolation

Use one task-owned Hugging Face root and preserve the entire cache layout.
Atlas's cache-root precedence is explicit `--cache-dir`, `HF_HUB_CACHE`,
`HF_HOME/hub`, then `HOME/.cache/huggingface/hub`
(`model_resolver.rs:286–301`). Setting only `XDG_CACHE_HOME` does not isolate
this Atlas resolver.

The `hf` CLI is supplied by `huggingface_hub`; a task-owned Python virtualenv
and pip cache can contain any needed installation. No Transformers dependency
is required merely to use `hf download`. Record the installed dependency
versions before execution. The commands below are proposed invocation
templates and were not executed by this exploration. [HF CLI documentation](https://huggingface.co/docs/huggingface_hub/en/guides/cli).

```sh
export HF_HOME="${TASK_ROOT:?Set TASK_ROOT to the absolute task-owned directory}/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_XET_CACHE="$HF_HOME/xet"
export HF_ASSETS_CACHE="$HF_HOME/assets"
export HF_TOKEN_PATH="$HF_HOME/token"
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export PIP_CACHE_DIR="$TASK_ROOT/pip-cache"

hf download unsloth/Qwen3.8-27B-NVFP4 \
  --revision 57926baca9a82b4d6906b43f2750d55315f5b10f \
  --cache-dir "$HF_HUB_CACHE"
```

Set these variables before starting Python/`hf`, because the Hub library
reads its environment at import. The checkpoint is public; no login or
user-token changes are needed. Xet can use its own cache when installed;
include that directory in storage accounting. The installed library's cache
settings and incomplete downloads still need attention to the disk budget.
Do not enable offline mode during the download. [HF environment reference](https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables).

Pin the load to the snapshot returned by the download. A SHA-pinned download
need not create `refs/main`, and Atlas's sibling fallback makes the ID-only
route unsuitable for establishing this exact revision. After the complete
download and the coordinator's pending target decision, the source-supported
check invocation is:

```sh
spark serve unsloth/Qwen3.8-27B-NVFP4 \
  --model-from-path "$HF_HUB_CACHE/models--unsloth--Qwen3.8-27B-NVFP4/snapshots/57926baca9a82b4d6906b43f2750d55315f5b10f" \
  --cache-dir "$HF_HUB_CACHE" \
  --check-kernels --no-tui
```

The positional ID remains available to target selection while
`--model-from-path` pins filesystem resolution. The CLI's
`cli/serve_args.rs:123–134` documents that anonymous paths such as `/model`
can leave Qwen3.6-27B versus Qwen3.8-27B unresolved; an explicit compatible
`--kernel-target` is available when model identity cannot break that tie.
This concerns model selection, not a substitute for selecting or validating
the build's hardware target.

Mount `hub/blobs` and `hub/snapshots` together so snapshot symlinks resolve;
avoid copying only the snapshot directory or making a second payload copy
with `--local-dir`. Atlas's separate Library downloader consults
`HF_TOKEN`/`HUGGING_FACE_HUB_TOKEN`, then hardcodes
`HOME/.cache/huggingface/token` in `model_download/hf.rs:57–61`, rather than
honoring `HF_TOKEN_PATH` there. The task-owned `hf` path above avoids relying
on that downloader behavior. No existing token files were inspected.

Only this prerequisites document and its adjacent metadata manifest were
written for this follow-up. No model payload was downloaded, and no GPU,
build, kernel check, or benchmark was run by this subtask.
