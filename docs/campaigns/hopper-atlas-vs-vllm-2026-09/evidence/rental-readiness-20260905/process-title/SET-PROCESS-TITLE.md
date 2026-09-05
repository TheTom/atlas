# Preserve ownership through vLLM worker renaming

Primary package documentation says setproctitle can overwrite Linux `/proc/PID/environ`; `SPT_NOENV` preserves it. Source: https://pypi.org/project/setproctitle/ (environment variables), corroborated by the vLLM 0.28 sources retained here. Parent argv verification remains strict; only children rename in the selected single-API-parent launch.

Observed on Spark1, CPU only: setproctitle 1.3.7 renamed the dummy child to `VLLM::EngineCore_DP0` and zeroed the environment bytes, including ATLAS_CAMPAIGN_RUN_TOKEN. The real-process test failed red at that missing marker. Manager launch now supplies the fixed non-secret `SPT_NOENV=1`, records it in allowlisted environment, and refuses explicit conflicting values. Green: the renamed child retains the ownership token, parent capture keeps its exact original argv, and pidfd cleanup stops the owned parent/child.

Dependency proof: PyPI metadata pinned version 1.3.7; aarch64 CPython 3.12 wheel SHA256 `6915964a6dda07920a1159321dcd6d94fc7fc526f815ca08a8063aeca3c204f1`, 33,736 bytes. Installed with --no-cache-dir --no-deps --only-binary=:all: --require-hashes inside an owned venv. No shared environment or GPU imports. The 11-case Linux suite passes; a test-side ESRCH observation race was corrected to treat an already-exited process as stopped, with the failed output retained separately.

Commands, raw output, exit codes, package metadata, file hashes and storage observations are retained. The owned 16MB staging/venv was removed after the tests. No runtime engine/benchmark result is claimed.
