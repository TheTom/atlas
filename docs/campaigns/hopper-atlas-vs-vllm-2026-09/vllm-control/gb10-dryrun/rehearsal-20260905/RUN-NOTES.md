# GB10 rehearsal execution notes

These are GB10 rehearsal artifacts, not Hopper measurements. Initial launch plans remain labelled planned; `*-launch.json` records the argv actually executed.

The Nano official vLLM recipe is adapted for GB10 with campaign deployment and parity settings: the pinned Ubuntu 24.04 image, immutable model/tokenizer revisions, mounted parser path, offline cache, LAN endpoint, 8192 context cap, and explicit prefix caching. The published Nano recipe has no verified GB10 entry. Speculation is off. Atlas uses the user-selected FP8 checkpoint with the repository fixture's nvfp4 kernel bundle and serving settings.

Both engines use the same task-owned HF cache. After all files match the manifest, the task-owned `refs/main` is set to the pinned revision. vLLM additionally receives explicit revision and tokenizer-revision arguments. The existing user cache is untouched.

The ladder remains byte-identical to its pinned source. Each ladder process restarts its nonce counter. Prefix caching is enabled on both; there is no extra cache reset or developer-mode flag. Cross-process cache reuse remains a written finding for the ladder owner. A/A retained its actual arithmetic verdict: three LOSS rows and one INVALID row; no real exact TIE occurred.

Atlas comparisons use vLLM pass A, the first lat/agent sequence, as the fixed control. Pass B is the A/A repeat; no best-performing pass was selected after seeing its results. The Atlas comparisons were not run because its coherency gate failed.

`control_remote_job.py` records `df -h /` around each download and samples disk bytes every 0.5 seconds. Soft stop thresholds reserve 5 GB below the user's 70 GB new-use cap and above the 12 GB free floor. `control_engine.py` applies the same guard while each owned engine container exists.

Boot starts immediately before `docker run`. The unchanged readiness invocation uses the same host clock and a 1800-second total deadline. If the container exits before readiness finishes, orchestration cancels only its readiness process group and records a failed boot with null readiness/token timing. In that case, in-memory HTTP polls from the cancelled gate are unavailable and explicitly marked as a schema gap. The server's exit state and logs remain preserved. There are no automatic engine retries or flag changes.

Both engines completed one launch attempt. vLLM passed coherency, ran eight ladder cells and one native cross-check; B/agent/C16 failed the 80% output-length floor (403/512 tokens). Atlas failed structured-tool coherency and produced degenerate but identical prime replies. No Atlas ladders ran.

Atlas's recipe default listener was loopback-only. The original LAN readiness observer was cancelled and replaced by a Spark 2 loopback observer without restarting the engine or changing server flags; the original start epoch was retained. Its 216.839-second total includes endpoint-correction delay and must not be compared as cold-start performance. The loading-503 transition was not observed. See atlas-endpoint-correction.json and the original launch log.

Cleanup completed after hash-verifying the remote evidence export. Both task images and containers, the shared checkpoint, venv and entire owned scratch root were removed. Initial/final df both showed 82 GiB free; detailed bytes and resource extrema are in resource-cleanup-summary.json. The original three images and graphics processes remain.
