#!/usr/bin/env python3
"""Derive diagnostic tables from immutable rental ladders; never certify them."""
import argparse
import copy
import hashlib
import json
import datetime
import itertools
import pathlib
import statistics
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text()) if path.exists() else None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def mean(reps, key):
    values = [r.get(key) for r in reps]
    if not values or any(not isinstance(v, (float, int)) for v in values):
        return None
    return statistics.fmean(values)


def workload_key(header):
    keys = ("isl", "osl", "temperature", "seed", "chat_template_kwargs", "reps", "warmup", "driver_sha256")
    return tuple(json.dumps(header.get(k), sort_keys=True) for k in keys)


def cell(path):
    raw = read(path)
    directory = path.parent
    env = read(directory / "process-env.json") or {}
    artifact = read(directory / "artifact.json")
    launch = read(directory / "launch-ready.json") or read(directory / "launch.json")
    argv = (artifact or {}).get("serve_command") or (launch or {}).get("argv")
    argv_path = directory / "serve.argv"
    if argv is None and argv_path.exists():
        argv = argv_path.read_text().rstrip("\0").split("\0")
    engine = "vllm" if "vllm" in directory.name else "atlas"
    native = env.get("ATLAS_DENSE_FP8") == "1"
    gates = {}
    for name in ("coherency", "coherency-pre", "coherency-post"):
        gate = read(directory / (name + ".json"))
        if gate:
            gates[name] = {k: gate.get(k) for k in (
                "passed", "determinism_ok", "toolcall_ok", "think_leak_ok", "known_answer_ok")}
            gates[name]["details"] = gate.get("details")
            gates[name]["sha256"] = sha(directory / (name + ".json"))
    policies = {name: read(directory / (name + ".json")) for name in (
        "quality-policy-pre", "quality-policy-post") if (directory / (name + ".json")).exists()}
    if engine == "vllm":
        precision = "Original FP8 block weights; dynamic W8A8; auto/BF16 KV"
    elif native:
        precision = "Original FP8 overlay; mixed W8A8/W8A16; BF16 head only when captured argv confirms; FP8 KV"
    else:
        precision = "Default Atlas: NVFP4 attention/FFN/head, native FP8 GDN; FP8 KV"
    stop = read(directory / "operator-budget-stop.json")
    status = ("finished_ladder" if raw.get("finished_utc") else
              "interrupted_session" if stop else "unfinished_ladder")
    rungs = []
    for rung in raw["rungs"]:
        reps = rung.get("reps", [])
        rungs.append({
            "concurrency": rung["concurrency"], "tok_s_mean": rung.get("tok_s_mean"),
            "timed_reps_complete": len(reps) == raw.get("reps"),
            "tok_s_spread_pct": rung.get("tok_s_spread_pct"),
            "ttft_p50_ms": mean(reps, "ttft_p50_ms"),
            "ttft_p99_ms": mean(reps, "ttft_p99_ms"),
            "tpot_p50_ms": mean(reps, "tpot_p50_ms"),
            "errors_total": rung.get("errors_total"),
            "timed_reps": copy.deepcopy(reps),
        })
    return {
        "directory": directory.name, "engine": engine, "native_fp8_profile": native,
        "session_status": status, "operator_budget_stop": stop,
        "process_identity": None if not launch else {
            k: launch.get(k) for k in ("pid", "boot_id", "start_ticks", "executable", "executable_sha256")},
        "native_engine_identity": (artifact or {}).get("engine_version"),
        "identity_note": "The captured Python executable hash is process evidence, not vLLM engine identity." if engine == "vllm" else None,
        "concurrent_quality": read(directory / "concurrent-quality/summary.json"),
        "precision": precision, "ladder_path": str(path), "ladder_sha256": sha(path),
        "header": {k: v for k, v in raw.items() if k != "rungs"}, "rungs": rungs,
        "gates": gates, "exception_policies": policies,
        "serve_argv": argv,
        "observed_serve_flags": {flag: argv[argv.index(flag) + 1] for flag in (
            "--lm-head-dtype", "--kv-cache-dtype", "--max-batch-size", "--max-num-seqs")
            if argv and flag in argv and argv.index(flag) + 1 < len(argv)},
        "unobserved_frozen_concurrencies": sorted({1, 16} - {r["concurrency"] for r in rungs}),
        "evidence_file_sha256": {name: sha(directory / name) for name in (
            "artifact.json", "launch.json", "serve.argv", "process-env.json",
            "harness.sha", "measurement-harness.sha", "available-spark.sha256",
            "nvidia-smi-q.txt", "measurement-complete.json", "launch-ready.json",
            "executed-spark.sha256", "operator-budget-stop.json",
            "concurrent-quality/summary.json") if (directory / name).exists()},
        "precision_profile_environment": {key: env[key] for key in (
            "ATLAS_DENSE_FP8", "ATLAS_FP8_SINGLE_SCALE", "ATLAS_CUTLASS_NVFP4_GEMM",
            "ATLAS_CUBLAS_GEMM") if key in env},
        "original_artifact": None if artifact is None else {
            k: artifact.get(k) for k in ("verdict", "failing_stage", "notes", "model",
                                       "engine_version", "paired_cell", "ptx_gate_receipt_sha256")},
        "boot": read(directory / "boot.json"),
        "measurement_complete": read(directory / "measurement-complete.json"),
        "certification_claimed": False,
    }


def execute(name, argv, out, commands):
    result = subprocess.run(argv, text=True, capture_output=True)
    (out / (name + ".stdout")).write_text(result.stdout)
    (out / (name + ".stderr")).write_text(result.stderr)
    record = {"name": name, "argv": argv, "exit_code": result.returncode,
              "stdout_path": name + ".stdout", "stderr_path": name + ".stderr"}
    commands.append(record)
    print(f"{name}: exit {result.returncode}")
    return result


def fmt(value):
    return "—" if value is None else f"{value:.3f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=pathlib.Path, default=HERE / "remote-results")
    parser.add_argument("--source", type=pathlib.Path,
                        default=HERE.parents[2] / "atlas-campaign-code")
    parser.add_argument("--out", type=pathlib.Path, default=HERE / "derived-measurements")
    args = parser.parse_args()
    compare = args.source / "bench/hopper_ab/compare.py"
    if not compare.exists():
        parser.error("--source must be the Atlas checkout containing bench/hopper_ab/compare.py")
    args.out.mkdir(parents=True, exist_ok=True)
    paths = sorted(p for p in args.raw.glob("*qwen38*/ladder.json") if read(p).get("rungs"))
    pending = []
    for directory in sorted(args.raw.glob("benchmark.qwen38*")):
        if not directory.is_dir():
            continue
        ladder_path = directory / "ladder.json"
        exported = read(ladder_path)
        if exported is None or not exported.get("rungs"):
            pending.append({"directory": directory.name,
                            "status": "no_ladder_export_yet" if exported is None else "no_completed_rung_export_yet",
                            "ladder_sha256": sha(ladder_path) if exported is not None else None,
                            "ladder_header": None if exported is None else {k: v for k, v in exported.items() if k != "rungs"},
                            "launch": read(directory / "launch-ready.json") or read(directory / "launch.json"),
                            "boot": read(directory / "boot.json"),
                            "concurrent_quality": read(directory / "concurrent-quality/summary.json"),
                            "certification_claimed": False})
    cells = [cell(p) for p in paths]
    raw_hashes = {str(p): sha(p) for p in paths}
    atlas = [c for c in cells if c["engine"] == "atlas"]
    vllm = [c for c in cells if c["engine"] == "vllm"]
    commands, comparisons = [], []
    matching_pairs = [(a, v, "atlas_vs_vllm") for a in atlas for v in vllm
                      if workload_key(a["header"]) == workload_key(v["header"])]
    # This is an after/before comparison through the unchanged tool. Its legacy
    # --vllm input name does not make the baseline engine vLLM.
    native = [c for c in atlas if c["native_fp8_profile"]]
    native.sort(key=lambda c: c["header"].get("started_utc", ""))
    for before, after in itertools.combinations(native, 2):
        if workload_key(before["header"]) == workload_key(after["header"]):
            matching_pairs.append((after, before, "atlas_native_after_vs_before"))
    repeats = sorted(vllm, key=lambda c: c["header"].get("started_utc", ""))
    for before, after in itertools.combinations(repeats, 2):
        if workload_key(before["header"]) == workload_key(after["header"]):
            matching_pairs.append((after, before, "vllm_after_vs_before"))
    if matching_pairs:
        first_a, first_b, _ = matching_pairs[0]
        original = read(pathlib.Path(first_b["ladder_path"]))
        bad = copy.deepcopy(original)
        bad["osl"] += 1
        bad_path = args.out / "known-bad-osl.json"
        save(bad_path, bad)
        red = execute("known-bad-osl", ["python3", str(compare), "--atlas",
                      first_a["ladder_path"], "--vllm", str(bad_path)], args.out, commands)
        if red.returncode != 2 or "osl:" not in red.stderr or "REFUSED:" not in red.stderr:
            raise RuntimeError("Known-bad OSL did not refuse; positive comparisons are blocked")
        selftest = execute("compare-selftest", ["python3", str(compare), "--selftest"], args.out, commands)
        if selftest.returncode:
            raise RuntimeError("Existing compare.py selftest failed; comparisons are blocked")
        for a, v, kind in matching_pairs:
            name = "compare-" + a["directory"] + "-vs-" + v["directory"]
            result_path = args.out / (name + ".json")
            result = execute(name, ["python3", str(compare), "--atlas", a["ladder_path"],
                             "--vllm", v["ladder_path"], "--out-json", str(result_path),
                             "--out-md", str(args.out / (name + ".md"))], args.out, commands)
            parity = None
            if kind == "atlas_native_after_vs_before":
                parity = {
                    "both_native_fp8_environment": a["native_fp8_profile"] and v["native_fp8_profile"],
                    "both_captured_bf16_head": all(c["observed_serve_flags"].get("--lm-head-dtype") == "bf16" for c in (a, v)),
                    "serve_argv_except_executable_equal": (a["serve_argv"][1:] == v["serve_argv"][1:]
                                                         if a["serve_argv"] and v["serve_argv"] else None),
                    "selected_precision_environment_equal": a["precision_profile_environment"] == v["precision_profile_environment"],
                }
            repeat_parity = None
            if kind == "vllm_after_vs_before":
                repeat_parity = {
                    "serve_argv_except_executable_equal": (a["serve_argv"][1:] == v["serve_argv"][1:]
                                                         if a["serve_argv"] and v["serve_argv"] else None),
                    "selected_precision_environment_equal": a["precision_profile_environment"] == v["precision_profile_environment"],
                    "immutable_engine_identity_proven": False,
                }
            comparisons.append({"name": name, "kind": kind, "native_profile_parity": parity,
                                "vllm_repeat_profile_parity": repeat_parity, "atlas_input": a["directory"],
                                "vllm_input": v["directory"], "input_engines": [a["engine"], v["engine"]],
                                "input_session_statuses": [a["session_status"], v["session_status"]],
                                "exit_code": result.returncode,
                                "result": read(result_path) if result.returncode == 0 else None})
    for c in cells:
        artifact = pathlib.Path(c["ladder_path"]).parent / "artifact.json"
        if artifact.exists():
            execute("validate-" + c["directory"], ["python3", str(args.source / "bench/campaign/validate_artifact.py"),
                    str(artifact)], args.out, commands)
    assert raw_hashes == {str(p): sha(p) for p in paths}, "Raw ladder changed during report"
    receipt = {"certification_claimed": False, "raw_ladders_unchanged": True,
               "script_sha256": sha(pathlib.Path(__file__)), "compare_sha256": sha(compare),
               "harness_source_sha256": sha(args.source / "bench/ladder38/harness_w55_conc_ladder.py"),
               "source_head": subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip(),
               "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "cells": cells, "pending_sessions": pending,
               "comparisons": comparisons, "commands": commands}
    save(args.out / "measurement-summary.json", receipt)
    lines = ["# Single H100 Qwen3.8 diagnostic measurements", "",
             "**Not certified campaign data.** Original NO-GO artifacts and original failed coherency gates remain unchanged. A successful compare.py exit establishes only its workload-header and rung checks; it does not certify engine identity, model revision, precision, or coherency.", "",
             "All latency headlines below are arithmetic means of the recorded per-repetition percentiles. They are not pooled percentiles. C1 p99 equals the single request in each repetition. Throughput is the harness's mean of timed repetition rates, including prefill. Raw timed repetitions and per-request completion counts are retained verbatim in measurement-summary.json. The harness's prompt_tokens_per_req field is a sorted set of observed counts, not a per-request array.", "",
             "| Cell | ISL/OSL | Session | C | tok/s mean | TTFT p50 ms | TTFT p99 ms | TPOT p50 ms | Measured prompt counts | Completion counts | Original gate |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |"]
    for c in cells:
        gate = "; ".join(f"{k}={v['passed']}" for k, v in c["gates"].items())
        for rung in c["rungs"]:
            reps = rung["timed_reps"]
            prompts = sorted({v for r in reps for v in r.get("prompt_tokens_per_req", [])})
            completions = sorted({v for r in reps for v in r.get("completion_tokens_per_req", [])})
            lines.append(f"| {c['directory']} | {c['header']['isl']}/{c['header']['osl']} | {c['session_status']} | {rung['concurrency']} | {fmt(rung['tok_s_mean'])} | {fmt(rung['ttft_p50_ms'])} | {fmt(rung['ttft_p99_ms'])} | {fmt(rung['tpot_p50_ms'])} | {prompts} | {completions} | {gate} |")
    lines += ["", "Nominal latency shape is ISL 1024 / OSL 256; agent shape is ISL 4096 / OSL 512. Shape appears beside every cell, and only matching workload headers are compared. The actual observed prompt length must be read from the table rather than assumed to be 1024. C16 is offered concurrency; Atlas's capacity profile permits four active decode sequences with the rest queued, whereas vLLM's capacity cap is 512. Warmup outputs are not present in ladder JSON; no warmup percentile series is reconstructed.", ""]
    for c in cells:
        lines += [f"## {c['directory']}", "", c["precision"] + ".", ""]
        lines += [f"Session status: **{c['session_status']}**. Unobserved frozen concurrencies: {c['unobserved_frozen_concurrencies']}. The presence of a complete rung does not make an interrupted ladder complete.", ""]
        if c["native_fp8_profile"]:
            lines += ["Captured native flags: `" + json.dumps(c["observed_serve_flags"], sort_keys=True) + "`. Executable: `" + json.dumps(c["process_identity"], sort_keys=True) + "`.", ""]
        if c["operator_budget_stop"]:
            lines += ["Operator budget stop: " + c["operator_budget_stop"].get("reason", "See raw receipt") + " Full action and process evidence remain in the JSON receipt.", ""]
        if c["concurrent_quality"]:
            quality = c["concurrent_quality"]
            control, concurrent = quality.get("control", {}), quality.get("concurrent", {})
            lines += [f"Separate arithmetic/protocol diagnostic: C1={control.get('passed')}, C16={concurrent.get('passed')}; observed client HTTP overlap={concurrent.get('max_overlapping_client_http_attempts')}. This does not replace the frozen coherency gate or establish simultaneous GPU rows.", ""]
        artifact = c["original_artifact"]
        if artifact:
            lines += [f"Original artifact: **{artifact['verdict']}**, failing stage `{artifact['failing_stage']}`. {artifact['notes']}", ""]
        else:
            lines += ["No campaign artifact is present in this measurement directory; no certification is inferred from the ladder.", ""]
        if c["exception_policies"]:
            lines += ["The user-authorized word-reversal exception permits these diagnostic measurements. It does not turn the original known-answer gate into a pass. Exact policy JSON and gate details are retained in measurement-summary.json.", ""]
        lines += ["| Rep | C | Wall s | Actual prompt total | Actual completion total | TTFT p50/p99 ms | TPOT p50 ms | tok/s | Finish reasons |",
                  "| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |"]
        for rung in c["rungs"]:
            for rep in rung["timed_reps"]:
                lines.append(f"| {rep.get('rep')} | {rung['concurrency']} | {fmt(rep.get('wall_s'))} | {rep.get('prompt_tokens')} | {rep.get('completion_tokens')} | {fmt(rep.get('ttft_p50_ms'))}/{fmt(rep.get('ttft_p99_ms'))} | {fmt(rep.get('tpot_p50_ms'))} | {fmt(rep.get('tok_s'))} | {rep.get('finish_reasons')} |")
        lines.append("")
    lines += ["## Existing comparison tool receipts", "",
              "Known-bad input is a derived copy with only OSL increased by1; originals were hash-checked unchanged. Its exit2 and exact stderr are saved before positive comparisons. Output WIN/LOSS/TIE labels are the tool's throughput arithmetic, not a certified or precision-matched campaign conclusion.", ""]
    for comparison in comparisons:
        lines += [f"- [{comparison['name']}]({comparison['name']}.stdout): exit {comparison['exit_code']}; {comparison['kind']}; input status {comparison['input_session_statuses']}."]
        if comparison['kind'] == 'atlas_native_after_vs_before':
            lines += ["  Both inputs are Atlas. The tool's legacy Atlas column is the later build and its vLLM column is the earlier build. Neither raw input is relabeled or edited. Captured profile checks: `" + json.dumps(comparison["native_profile_parity"], sort_keys=True) + "`. Missing concurrencies on both inputs are still absent even when compare.py has no NO-PAIR row to display."]
        if comparison['kind'] == 'vllm_after_vs_before':
            lines += ["  Both inputs are vLLM: legacy Atlas column is the later run and vLLM column the earlier run. These actual WIN/LOSS/TIE verdicts are preserved. TIE requires exactly ratio1.0; the identical-input selftest is not a noise-tolerance oracle for independent repeats. Captured profile checks: `" + json.dumps(comparison["vllm_repeat_profile_parity"], sort_keys=True) + "`. No immutable vLLM implementation identity is inferred."]
    lines += ["", "## Pending exports", ""]
    for item in pending:
        quality = item["concurrent_quality"] or {}
        control = quality.get("control", {})
        concurrent = quality.get("concurrent", {})
        lines += [f"- {item['directory']}: {item['status']}; no completed rung exported. Concurrent-quality control={control.get('passed')}, C16={concurrent.get('passed')}, observed client HTTP overlap={concurrent.get('max_overlapping_client_http_attempts')}. This is a quality diagnostic, not a throughput rung or proof of simultaneous GPU rows."]
    for c in cells:
        if c["session_status"] != "finished_ladder":
            lines += [f"- {c['directory']}: {c['session_status']}; complete exported rungs={[r['concurrency'] for r in c['rungs'] if r['timed_reps_complete']]}; unobserved frozen concurrencies={c['unobserved_frozen_concurrencies']}; post-coherency present={'coherency-post' in c['gates']}."]
    if not pending and all(c["session_status"] == "finished_ladder" for c in cells):
        lines += ["All discovered ladder files have finished timestamps; missing rungs and missing artifacts remain separately listed."]
    lines += ["", "Before native Atlas results can be described as checkpoint-native, its captured environment must show ATLAS_DENSE_FP8=1, argv must preserve the checkpoint BF16 head, and the build must include the multi-row native FFN dispatch repair. Arithmetic remains engine-specific (Atlas W8A8/W8A16, vLLM dynamic W8A8, Butter W8A32). KV precision also differs in the existing profiles. The known source audit is ../tooling-fixes/native-fp8-batched-ffn/PRECISION-AUDIT.md.", "",
              "Missing rungs stay NO-PAIR. Interrupted sessions retain their original stop reason and missing post-gate; finished_utc is never synthesized. Run this script again after the native ladder and its launch/coherency evidence have been exported; it does not edit or repair missing provenance."]
    (args.out / "MEASUREMENTS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
