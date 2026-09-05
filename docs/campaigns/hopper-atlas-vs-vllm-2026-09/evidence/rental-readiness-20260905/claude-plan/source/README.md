# rental-kit

Everything needed to land on a rented CUDA box, get Atlas and vLLM running, benchmark them
against each other, and get the results off the machine before the meter stops. The box is
ephemeral and the clock is expensive; every script here is idempotent and re-runnable after
a disconnect.

Source of truth lives on the Mac at `~/dev/rental-kit/`. Copy the whole directory to the
node (`rsync -az ~/dev/rental-kit/ root@<node>:/root/`) and work from there inside `tmux`.

---

## Branch rule

**The node builds from `rental/h100-<date>` cut off the PR tip. Codex cherry-picks into
#895 afterward. Never push to `hopper/sm90-target-tdd-2026-09` during a rental.**

A rental node is a scratch environment: half-finished kernels, hand-edited constants, and
`git commit -am wip` at 3am. None of that belongs on the campaign branch. Cut
`rental/h100-<date>` from the PR tip on arrival, commit freely to it, push it as a *record*,
and let the cherry-pick into #895 be a deliberate act performed later with a clear head.

> Note: `bootstrap.sh` defaults `ATLAS_BRANCH=hopper/sm90-target-tdd-2026-09`. That is a
> read-only clone to get the tip onto the box, which is fine. Immediately after bootstrap,
> `git -C /root/src/atlas switch -c rental/h100-$(date +%Y%m%d)` before you touch anything.
> All Atlas remotes point at the `TheTom/atlas` fork of `Avarok-Cybersecurity/atlas`.

---

## Order of operations

| # | Step | Script | Gate |
|---|------|--------|------|
| 1 | Is this box worth paying for? | `preflight_node.sh` | exit 0 or **destroy the instance now** |
| 2 | Install CUDA 13, NCCL, Rust, clone Atlas | `bootstrap.sh` | `bootstrap complete` |
| 3 | Cut the rental branch | `git switch -c rental/h100-<date>` | — |
| 4 | Start weights downloading into the shared `$HF_HOME` cache (background, slow) | `dl_queue.sh` | `QUEUE_DONE` |
| 5 | Build the server while weights land | `build_spark.sh` | `BUILD_OK` |
| 6 | Install the control engine | `install_vllm.sh` | prints vLLM + torch + sm |
| 7 | Start result sync (on the **Mac**, leave running) | `sync_results.sh` | `synced` every 5 min |
| 8 | Correctness before speed | `logit_diff.py` | exit 0 |
| 9 | If it crashed | `fault_triage.sh` | named kernel or Xid |
| 10 | If it is merely slow | `profile_decode.sh` | top-15 kernel table |

Steps 4 and 5 overlap: downloads are network-bound and the build is CPU-bound, so run them
in two tmux panes. **Step 8 gates step 10** — never publish a throughput number for an
engine you have not proven emits the right tokens. A fast wrong answer is worth nothing,
and "it looked coherent" is not a measurement.

---

## Scripts

### `preflight_node.sh`
Read-only go/no-go check, run before spending a cent on downloads. It turns the abort rules
into pass/fail assertions: GPU count and compute capability (the Hopper target is `sm_90a`,
so CC 9.0 exactly), driver ≥ 580 because Atlas links the CUDA 13 runtime and a 12.x driver
dies at `cuInit` long before any PTX matters, NVLink presence on multi-GPU boxes, no foreign
compute processes already squatting on the cards, and enough free disk that Super FP8's 120
GiB will actually fit. It also probes HuggingFace, GitHub, and the NVIDIA apt repo for
reachability without downloading anything. Exit 0 means go; exit 1 prints the FAIL lines and
you should destroy the instance rather than debug it.

### `bootstrap.sh`
Brings a bare Ubuntu 24.04 container up to a working Atlas build environment: apt base
packages, the NVIDIA apt keyring, `cuda-toolkit-13-0`, NCCL ≥ 2.28 built against CUDA 13
(Atlas needs the symmetric-memory APIs), rustup, a shallow clone of the Atlas fork, and a
`huggingface_hub[hf_xet]` venv. It also pins `HF_HOME=/root/hf` in `env.sh` so Atlas and
vLLM share one weight cache — a 300 GB disk cannot hold two copies of Super. Every stage drops a marker in `/root/.bootstrap-done/` and
is skipped on re-run, so a disconnect costs you nothing — delete a marker to redo just that
stage. Writes `/root/env.sh`, which every later script sources.

### `build_spark.sh`
Builds the `spark` server binary for one hardware/model target: about 4 minutes cold, 1
minute warm on a many-core host. Sets `ATLAS_TARGET_HW` / `ATLAS_TARGET_MODEL` /
`ATLAS_TARGET_QUANT` so the right kernel set is compiled in, builds with `--features
cuda,nccl`, then copies the binary to `/root/bin/spark-<hw>-<model>` and appends its sha256
to `/root/results/binaries.sha256`. Keep those hashes: when two benchmark runs disagree, the
first question is whether they ran the same binary.

### `dl_queue.sh`
Resumable weight-download queue via `hf_xet` (~46 MiB/s observed), downloading into the
**shared** `$HF_HOME` cache (default `/root/hf`) rather than per-engine `--local-dir` trees,
so Atlas and vLLM read the same bytes and each model is stored once. Models are referenced
downstream by HuggingFace id, not by path. Completed repos are marked with a `.complete`
sentinel under `$HF_HOME/done/` and skipped, and each repo is deferred rather than started
if free disk is below its size plus 40 GiB of headroom — a download that fills the root
filesystem takes the whole box down with it. Retries forever on failure, so it survives the
flaky-network hour. Re-run it after any restart.

### `install_vllm.sh`
Installs vLLM into `/root/vllm-venv` with `uv` (no Docker inside the container), then prints
the vLLM version, torch version, linked CUDA version, and the detected SM. vLLM is the
*control* engine: it is the thing Atlas gets compared against, so record those four values
next to every number you publish.

### `sync_results.sh`
Runs **on the Mac, not the node.** Rsyncs `/root/results/` off the box every 5 minutes and
prints a timestamp per cycle. The node is ephemeral and often overlay-backed, so anything
not synced is one instance-kill away from gone. Start it in its own terminal at the
beginning of the day and leave it running until the instance is destroyed.

### `logit_diff.py` — the "runs but wrong" oracle
Compares Atlas and vLLM token by token on the four fixed coherency-gate prompts at
temperature 0, seed 42, thinking disabled. For each position it checks argmax equality (at
temperature 0 the emitted token *is* the argmax), top-K Jaccard overlap, and the absolute
logprob delta of the token Atlas chose looked up in vLLM's top-K. It reports first
divergence index, argmax agreement fraction, mean Jaccard, and the two decoded strings up to
the divergence plus 8 tokens, so a numerics bug reads as "diverges at index 12" instead of
as two paragraphs you squint at. `--raw` also runs `/v1/completions` with the plain prompt
text, which removes the chat template from the picture — a divergence that appears on the
chat endpoint but not the raw one is a template bug, not a kernel bug. A server that returns
`logprobs: null` is reported as *oracle unavailable* with exit 2 and is never scored as
agreement. Exit 0 agree, 1 diverged, 2 no oracle. `--out report.json` retains every raw
request and response. `--selftest` runs the whole thing against in-process canned servers
with no GPU and no network.

```bash
python3 logit_diff.py --selftest
python3 logit_diff.py --a http://127.0.0.1:8888 --b http://127.0.0.1:8000 \
    --model-a nemotron-nano --model-b nemotron-nano --max-tokens 64 --top-k 5 \
    --raw --out /root/results/logit_diff.json
```

### `fault_triage.sh` — the "CUDA error 700 at a sync point" reflex
An async CUDA fault is reported at whatever sync point happens to come next, which is almost
never the launch that caused it, so the stack you get is noise. This runs three narrowing
steps into `./fault-triage-<epoch>/`: (1) a serialised replay with `CUDA_LAUNCH_BLOCKING=1`
and `RUST_LOG=debug`, prompts sent one at a time at concurrency 1, which moves the error
report back onto the offending launch and removes batching as a variable, then extracts the
first line matching `CUDA|cuda|error|panic` with 20 lines of context; (2) if
`compute-sanitizer` is present, one prompt at `max_tokens 8` under `--tool memcheck`, which
names the kernel and the access — this is 10–50x slower and is for Nano-sized models only,
it will not finish on Super inside the rental window; (3) `nvidia-smi -q` and a `dmesg` tail
for Xid lines, which outrank anything in the application log — an Xid 79 means the GPU fell
off the bus and no amount of code reading will help. Ends with a one-screen summary naming
which step produced the first error and the kernel if the sanitizer named one. `--dry-run`
prints every command, touches no GPU, and works on a laptop.

The model argument takes either a local path or a HuggingFace id out of the shared
`$HF_HOME` cache. The serve argv defaults to `serve <model> --no-tui --gpu-ordinal 0 --bind 127.0.0.1 --port <port>` (the form verified on the RTX box). Override with `--serve-args` when a model needs extra flags (for example `--kv-cache-dtype bf16`).

```bash
bash fault_triage.sh /root/bin/spark-hopper-nemotron nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 --dry-run
bash fault_triage.sh /root/bin/spark-hopper-nemotron nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 \
    --model-id nemotron-nano --serve-args "serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 --port 8899"
```

### `profile_decode.sh` — the "runs but slow" tool
Profiles where decode time actually goes and reports the top 15 kernels by total GPU time
alongside the tokens/s the driver achieved in the same window. **Read the header comment
before the rental day**: Nsight Systems most likely cannot attach to an already-running
server, because CUDA tracing is CUPTI injected at process start, and `--attach` takes a
session id from `nsys launch` rather than a bare PID. That claim is **unverified** — `nsys`
is not installed on the Mac this was written on — so instead of shipping a guess the script
probes the installed `nsys profile --help` at runtime and prints what it finds. Run it with
`--dry-run` on the node early; the probe output is the real answer and it costs two seconds.
Three modes: default is **load only** (drives load, reports real tokens/s, captures no GPU
trace, and says so in a box you cannot miss); `--launch "<spark serve ...>"` is the mode that
actually works, starting the server under `nsys profile -t cuda,nvtx -y <warmup> -d
<seconds>` where `-y` delays collection past weight loading so the window contains decode;
`--attach-pid` probes for support and refuses without `--force-attach`, because a flag
existing is not proof it means what you hope. Load comes from the bundled `loadgen.py`.
Exit 3 if `nsys` is missing (it prints the exact `apt-get install -y
cuda-nsight-systems-13-0` line), 4 if attach was requested but is unsupported.

```bash
bash profile_decode.sh http://127.0.0.1:8888 nemotron-nano --dry-run
bash profile_decode.sh http://127.0.0.1:8888 nemotron-nano --seconds 30 --concurrency 8 \
    --launch "/root/bin/spark-hopper-nemotron serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 --no-tui --gpu-ordinal 0 --bind 127.0.0.1 --port 8888"
```

### `loadgen.py`
The load driver `profile_decode.sh` shells out to, also useful alone for a quick throughput
number. Sends `--concurrency` parallel non-streaming chat requests for a fixed duration
using the ~1024-token prompt in `warmup_1024.txt` when that file exists and a built-in
repeated paragraph otherwise. Requests still in flight at the deadline are awaited but
excluded from the rate, so the tail does not inflate the number. Token counts come from
`usage.completion_tokens`; if a server omits `usage` the fallback is `len(text)/4` and the
output says so explicitly rather than silently mixing the two. Reports mean/p50/p99 latency
alongside tokens/s. `--selftest` covers it offline.

### `cuattr.py`, `hfsize.py`
Two small probes. `cuattr.py` calls into `libcuda.so.1` directly to dump per-device compute
capability and the integrated/pageable-access/concurrent-managed attributes — useful when
`nvidia-smi` and the runtime disagree about what the device is. `hfsize.py` queries the
HuggingFace API for a repo's blob sizes so you know what a download will cost in disk and
minutes before `dl_queue.sh` starts it.

---

## Offline checks

Every tool proves itself without a GPU, so you find out the tooling is broken here rather
than at hour three of a rental:

```bash
python3 logit_diff.py --selftest     # red: divergence, null logprobs, dead server; then green
python3 loadgen.py --selftest        # red: HTTP 500; then green
bash fault_triage.sh /root/bin/spark nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 --dry-run
bash profile_decode.sh http://127.0.0.1:8888 model --dry-run
shellcheck -S warning ./*.sh
```
