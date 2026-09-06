# Native vLLM engine identity: supplemental evidence, gate preserved

The installed vLLM package declares version0.28.0 and commit `g2cf0a6915`. After preserving the raw declaration, `2cf0a6915` is a valid short engine-declared source revision under the schema's7–40 lowercase-hex pattern. It is not by itself an immutable identity for all implementation bytes that served a request. No artifact, harness, schema or CERTIFIED rule was changed.

Read-only evidence captured2026-09-05T22:43:56.784859Z:

- Package `/workspace/atlas-rental/vllm/lib/python3.12/site-packages/vllm/_version.py`, SHA256 `63904896f9449a84bac95c17567eb1dea3592783ac3aa13916f5928b9458e9ac`, contains literal chained assignments for version and commit. AST literal parsing executed no package code.
- `vllm-0.28.0.dist-info` metadata agrees on version. Its RECORD has7276 entries; manifest SHA256 `19df57fcb5024ff94dfbfcc115f07a857b7300d663a80006b3c05551f1c969b1`.
- The version file and `/workspace/atlas-rental/vllm/bin/vllm` content hashes and lengths match their RECORD entries. Only those two files were content-verified. The248-byte console script imports `vllm.entrypoints.cli.main`; its shebang names this virtual environment's Python. Its hash identifies that import shim, not vLLM's Python modules and compiled extensions.
- `pyvenv.cfg` declares Python3.12.3 and `include-system-site-packages=false`.
- An explicit-path stdlib metadata inventory captured196 installed distributions without importing vLLM, torch, CUDA, or any runtime package. Versions include torch2.13.0, transformers5.16.1, triton3.7.1, xgrammar0.2.3 and flashinfer-python0.6.16.post3. This is a name/version inventory, not verification of every dependency's installed bytes or install origin.

The supplemental files are copied under `remote-results/native-vllm-environment-20260905T224356Z/`: distribution-versions.json, distribution-versions.txt and version-and-record-receipt.json. `installed-read.json` retains the exact read-only SSH command/script, exit0, stdout and stderr. No remote files were written; no heavy package scan, engine import, GPU call or HTTP request occurred. The read used a fixed installed directory; it was not bound to an owned process's effective import resolution or to a before/after run fingerprint.

## Current path and counterexamples

`cell_identity.sh:83-90` deliberately leaves native-vLLM identity unset. `process_launch_proc.py` captures the actual interpreter, `/proc` argv, ownership and selected environment; `process_model_evidence.py` verifies model launch identity only and says so explicitly. `cell_assemble.py:368-372` can store a supplied engine-declared commit and version, but currently has no verified Python-package identity input. `artifact.schema.json:112-141` defines git_sha as an engine-declared revision and binary_sha256 as the local engine binary hash. It does not define a package-manifest field.

`validate_artifact.py:244-262` additionally requires image_digest or binary_sha256 for CERTIFIED. Therefore filling only git_sha and vllm_version would preserve useful source metadata but would still fail the build-identity gate. A dependency name/version inventory and version-file hash do not close that gap.

The CPU counterexamples use the actual validator against an otherwise-valid certified fixture:

| Attempt | Existing validator | Provenance verdict |
|---|---|---|
| Declared git_sha2cf0a6915 and version0.28.0; build hashes null | Rejects, expected engine-identity error | Insufficient to certify |
| Version-file hash placed in binary_sha256 | Accepts field syntax | Invalid engine provenance |
| Console-entrypoint hash placed in binary_sha256 | Accepts field syntax | Invalid engine provenance |
| Actual captured Python interpreter hash placed in binary_sha256 | Accepts field syntax | Invalid engine provenance |

`declared-git-only.json` retains the red command-level condition and exact error. The other files are deliberately forged local fixtures demonstrating that a well-formed hash is not evidence of the claimed subject. They are not campaign measurements. The real `capture_engine_identity` function was also executed locally for native-vLLM mode with interpreter and console-script paths; both checks pass by leaving every engine identity field unset (`capture-python-refusal.json`, `capture-console-refusal.json`). The current pipeline correctly avoids those substitutions. The schema validator checks field structure; the capture/assembler boundary must supply truthful subjects.

## Future explicit package-identity proposal

A future schema change could add a separately named native-package identity, leaving image_digest and binary_sha256 null. It should fingerprint a canonical manifest of actual installed vLLM implementation files, including compiled extensions, and retain the declared version/commit, RECORD digest and dependency inventory as supporting provenance. Hashing RECORD alone is insufficient: its listed files may have changed. Hashing only `_version.py` is insufficient: all other engine code can change while that file remains fixed.

Capture must resolve the package from the same supported interpreter/entrypoint and effective import environment as the owned launched process, verify ownership and freshness, and detect package changes during the run. Import-shadowing, a foreign virtual environment, stale owner/PID, package-file mutation with unchanged metadata, metadata-only version matches, missing native extensions, unknown/dirty commit declarations and mixed before/after inventories are required negative cases. For dependency identity, version inventory alone should remain explicitly weaker than full installed-byte verification.

The assembler should accept this new identity only after validating that sidecar and process binding; the validator could then recognize the explicitly defined third identity form. This deserves a scoped schema/assembler change with red-first tests, not reuse of an existing field with different semantics. None of that work is needed to retain valid raw measurements now; those remain uncertified while immutable engine identity or other required gates are absent.

Stopping rule met: actual installed declarations and two RECORD entries verified; schema/capture/assembler behavior traced; revision-only refusal and false-subject hash counterexamples observed; supplemental metadata retained. No code changes or new certification claims.
