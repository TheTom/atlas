#!/usr/bin/env python3
"""Prepare, or explicitly execute, one bounded vLLM client cross-check cell."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

MODEL = "Qwen/Qwen3.8-27B-FP8"
REVISION = "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"
RENTAL = Path("/workspace/atlas-rental")
TOKENIZER = RENTAL / "hf38/hub/models--Qwen--Qwen3.8-27B-FP8/snapshots" / REVISION


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def command(out, prompts):
    return [str(RENTAL / "vllm/bin/vllm"), "bench", "serve",
            "--backend", "openai", "--base-url", "http://127.0.0.1:8000",
            "--endpoint", "/v1/completions", "--model", MODEL,
            "--tokenizer", str(TOKENIZER), "--dataset-name", "random",
            "--random-input-len", "1024", "--random-output-len", "256",
            "--random-range-ratio", "0.0", "--num-prompts", str(prompts),
            "--max-concurrency", "1", "--request-rate", "inf",
            "--num-warmups", "1", "--ready-check-timeout-sec", "10",
            "--seed", "42", "--temperature", "0", "--ignore-eos",
            "--extra-body", json.dumps({"seed": 42, "presence_penalty": 0.0,
                                         "frequency_penalty": 0.0}, separators=(",", ":")),
            "--percentile-metrics", "ttft,tpot,itl,e2el", "--metric-percentiles", "50,99",
            "--label", "qwen38-native-vllm-random-crosscheck",
            "--save-result", "--save-detailed", "--result-dir", str(out),
            "--result-filename", "vllm-bench-raw.json", "--disable-tqdm"]


def capture(argv, path, env, timeout=20):
    result = subprocess.run(argv, text=True, capture_output=True, env=env, timeout=timeout)
    path.with_suffix(".stdout").write_text(result.stdout)
    path.with_suffix(".stderr").write_text(result.stderr)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=RENTAL / "src/atlas")
    parser.add_argument("--session-dir", type=Path, required=True,
                        help="Ready vLLM benchmark session containing its owner.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--num-prompts", type=int, default=8)
    parser.add_argument("--execute", action="store_true",
                        help="Run only when the parent grants the GPU measurement window")
    args = parser.parse_args()
    if not 8 <= args.num_prompts <= 16:
        parser.error("cross-check requires 8–16 measured prompts")
    argv = command(args.out, args.num_prompts)
    plan = {"argv": argv, "measured_requests": args.num_prompts,
            "additional_requests": "one readiness test plus one explicit warmup",
            "maximum_client_concurrency": 1, "nominal_input_output": [1024, 256],
            "content": "Random completions; differs from frozen essay chat workload",
            "eos_policy": "ignore_eos=true; differs from the frozen ladder",
            "certification_claimed": False, "timeout_seconds": 180,
            "execution_requested": args.execute, "owner_record": str(args.session_dir / "owner.json")}
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return 0
    if args.out.exists():
        parser.error("output directory already exists; preserve prior cross-check results")
    if not (TOKENIZER / "tokenizer.json").is_file():
        parser.error("pinned tokenizer must already be local; this helper never downloads it")
    owner = args.session_dir / "owner.json"
    if not owner.is_file():
        parser.error("session has no owner.json; no benchmark request will be sent")
    args.out.mkdir(parents=True)
    env = dict(os.environ)
    env.update(CUDA_VISIBLE_DEVICES="", HF_HOME=str(RENTAL / "hf38"),
               HF_HUB_CACHE=str(RENTAL / "hf38/hub"), HF_HUB_OFFLINE="1",
               TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    recorded_env = {key: env[key] for key in (
        "CUDA_VISIBLE_DEVICES", "HF_HOME", "HF_HUB_CACHE", "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE", "TOKENIZERS_PARALLELISM")}
    plan.update(started_utc=utc(), environment=recorded_env,
                helper_sha256=digest(Path(__file__)), owner_sha256=digest(owner))
    write(args.out / "receipt.json", plan)
    write(args.out / "argv.json", argv)
    write(args.out / "environment.json", recorded_env)
    # The existing endpoint ownership gate checks the captured vLLM process.
    # CUDA is hidden only from this CPU client, not changed in the server.
    endpoint_argv = ["python3", str(args.source / "bench/campaign/process_endpoint.py"),
                     "owned", "--url", "http://127.0.0.1:8000", "--record", str(owner),
                     "--out", str(args.out / "endpoint-before.json")]
    status = capture(endpoint_argv, args.out / "endpoint-before", env)
    plan["endpoint_before_exit"] = status
    write(args.out / "receipt.json", plan)
    if status:
        return status
    capture(["nvidia-smi", "-q"], args.out / "nvidia-smi-q", env)
    capture(["df", "-h", "/workspace"], args.out / "df-before", env)
    try:
        with (args.out / "bench.stdout").open("w") as stdout, (args.out / "bench.stderr").open("w") as stderr:
            result = subprocess.run(argv, env=env, stdout=stdout, stderr=stderr, timeout=180)
        status = result.returncode
    except subprocess.TimeoutExpired:
        status = 124
    plan.update(finished_utc=utc(), benchmark_exit=status)
    raw = args.out / "vllm-bench-raw.json"
    if raw.exists():
        plan["raw_json_sha256"] = digest(raw)
        data = json.loads(raw.read_text())
        plan["observed"] = {key: data.get(key) for key in (
            "completed", "failed", "total_input_tokens", "total_output_tokens",
            "input_lens", "output_lens", "output_throughput", "median_ttft_ms",
            "median_tpot_ms", "p50_ttft_ms", "p99_ttft_ms", "errors")}
    after_argv = endpoint_argv[:-1] + [str(args.out / "endpoint-after.json")]
    plan["endpoint_after_exit"] = capture(after_argv, args.out / "endpoint-after", env)
    capture(["df", "-h", "/workspace"], args.out / "df-after", env)
    write(args.out / "receipt.json", plan)
    return status


if __name__ == "__main__":
    sys.exit(main())
