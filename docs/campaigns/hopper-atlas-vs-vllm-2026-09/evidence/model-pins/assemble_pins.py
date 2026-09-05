#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Derive the model-key inventory from captured Hub metadata, without network."""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parent / "model-pins-2026-09-05.json"
SHA = re.compile(r"^[0-9a-f]{40}$")


def load(path):
    return json.loads(path.read_text())


def checked_payload(raw, expected_hash, expected_repo, expected_sha):
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("response SHA256 mismatch")
    data = json.loads(raw)
    if data.get("id") != expected_repo:
        raise ValueError("repository identity mismatch")
    if not SHA.fullmatch(data.get("sha", "")) or data["sha"] != expected_sha:
        raise ValueError("revision missing or mismatched")
    files = data.get("siblings")
    if not isinstance(files, list) or not files:
        raise ValueError("empty file inventory")
    names = set()
    for item in files:
        name = item["rfilename"]
        if name in names:
            raise ValueError("duplicate file path")
        names.add(name)
        size = item.get("size")
        if type(size) is not int or size < 0:
            raise ValueError("missing or invalid file size")
        if item.get("lfs") is not None and item["lfs"].get("size") != size:
            raise ValueError("LFS payload size mismatch")
    if not any(f["rfilename"].endswith(".safetensors") for f in files):
        raise ValueError("no safetensors weights")
    # Every captured repository uses safetensors. Refuse an ambiguous mixed
    # weight inventory instead of silently omitting another weight format.
    suspicious = (".bin", ".pt", ".pth", ".gguf", ".h5", ".msgpack")
    if any(f["rfilename"].endswith(suspicious) for f in files):
        raise ValueError("other possible weight format requires explicit classification")
    return data


def selftest():
    good = {"id": "fixture/model", "sha": "a" * 40,
            "siblings": [{"rfilename": "model.safetensors", "size": 13,
                          "lfs": {"size": 13}}, {"rfilename": "config.json", "size": 2}]}
    mutations = {
        "missing size": lambda d: d["siblings"][0].pop("size"),
        "LFS pointer/payload disagreement": lambda d: d["siblings"][0]["lfs"].update(size=4),
        "wrong revision": lambda d: d.update(sha="b" * 40),
        "duplicate file": lambda d: d["siblings"].append(d["siblings"][0]),
        "mixed weight format": lambda d: d["siblings"].append({"rfilename": "pytorch_model.bin", "size": 100}),
    }
    for name, mutate in mutations.items():
        bad = copy.deepcopy(good)
        mutate(bad)
        raw = json.dumps(bad).encode()
        try:
            checked_payload(raw, hashlib.sha256(raw).hexdigest(), "fixture/model", "a" * 40)
        except ValueError as exc:
            print(f"RED observed: {name}: {exc}")
        else:
            raise AssertionError(f"known-bad input accepted: {name}")
    raw = json.dumps(good).encode()
    try:
        checked_payload(raw, "0" * 64, "fixture/model", "a" * 40)
    except ValueError as exc:
        print(f"RED observed: wrong response hash: {exc}")
    else:
        raise AssertionError("wrong hash accepted")
    checked_payload(raw, hashlib.sha256(raw).hexdigest(), "fixture/model", "a" * 40)
    print("PASS: 6 known-bad metadata fixtures rejected before 1 positive fixture")


def seconds(byte_count):
    return {str(rate): round(byte_count * 8 / (rate * 1_000_000_000), 3)
            for rate in (2, 10, 25)}


def revision_arg(tokens):
    for i, token in enumerate(tokens):
        if token == "--revision":
            return tokens[i + 1]
        if token.startswith("--revision="):
            return token.split("=", 1)[1]
    return None


def draft_models(entry):
    found = {}
    for field in ("args", "spec_args"):
        tokens = entry.get(field) or []
        for i, token in enumerate(tokens):
            if token == "--speculative-config":
                config = json.loads(tokens[i + 1])
                if config.get("model"):
                    found[config["model"]] = config
    return found


def assemble():
    sources = load(HERE / "source.json")
    entries = {engine: load(HERE / f"{engine}_recipes.json")["entries"]
               for engine in ("atlas", "vllm")}
    metadata = {}
    for path in sorted((HERE / "repositories").glob("*/request.json")):
        request = load(path)
        if request["status"] != "ok":
            metadata[request["repo_id"]] = {"repo_id": request["repo_id"],
                "revision": None, "weight_bytes": None, "gated": None,
                "license": None, "status": "unknown", "error": request.get("error")}
            continue
        response = request["http_responses"][-1]
        assert response["status_code"] == 200
        raw = (path.parent / response["body_path"]).read_bytes()
        data = checked_payload(raw, response["body_sha256"], request["repo_id"], request["sha"])
        card = data.get("cardData") or {}
        weights = [f for f in data["siblings"] if f["rfilename"].endswith(".safetensors")]
        weight_bytes = sum(f["size"] for f in weights)
        total_bytes = sum(f["size"] for f in data["siblings"])
        prefix = "model-pins/" + str(path.parent.relative_to(HERE))
        metadata[data["id"]] = {
            "repo_id": data["id"], "source_repo_id": data["id"],
            "revision": data["sha"], "revision_kind": "observed_default_branch_head",
            "observed_utc": request["finished_utc"], "status": "ok",
            "gated": data.get("gated"), "private": data.get("private"),
            "license": {"id": card.get("license"), "name": card.get("license_name"),
                        "link": card.get("license_link"), "source": "Hub API cardData; license text not downloaded"},
            "upstream_base_model_ids": card.get("base_model"),
            "upstream_base_model_revision": None,
            "upstream_revision_reason": "Not supplied by the captured card metadata; not the artifact revision above",
            "weight_format": "safetensors", "weight_file_count": len(weights),
            "weight_bytes": weight_bytes, "repository_file_count": len(data["siblings"]),
            "repository_payload_bytes": total_bytes,
            "weight_download_seconds_at_gbit_s": seconds(weight_bytes),
            "repository_download_seconds_at_gbit_s": seconds(total_bytes),
            "download_time_assumptions": "bytes*8/(decimal Gbit/s*1e9), sustained link-rate lower bound; no overhead, throttling, decompression or filesystem cost",
            "request_evidence": prefix + "/request.json",
            "raw_response_evidence": prefix + "/" + response["body_path"],
            "raw_response_sha256": response["body_sha256"],
            "files": [{"path": f["rfilename"], "size_bytes": f["size"],
                       "lfs_sha256": (f.get("lfs") or {}).get("sha256"),
                       "weight": f["rfilename"].endswith(".safetensors")}
                      for f in data["siblings"]],
        }
    records = []
    keys = sorted({e["model_key"] for group in entries.values() for e in group})
    for key in keys:
        grouped = {engine: [e for e in group if e["model_key"] == key]
                   for engine, group in entries.items()}
        profiles = []
        artifact_ids = set()
        comparisons = []
        primary = (grouped["vllm"] or grouped["atlas"])[0]["hf_id"]
        for engine, group in grouped.items():
            for entry in group:
                artifact_ids.add(entry["hf_id"])
                drafts = draft_models(entry)
                artifact_ids.update(drafts)
                commands = [entry["args"]] + (entry.get("worker_args") or []) if engine == "vllm" else []
                profiles.append({
                    "engine": engine, "sku": entry["sku"], "repo_id": entry["hf_id"],
                    "quant": entry["quant"], "proposed_revision": metadata[entry["hf_id"]]["revision"],
                    "recipe_source": f"bench/campaign/{engine}_recipes.json",
                    "recipe_entry_index": entries[engine].index(entry),
                    "revision_in_recipe": [revision_arg(c) for c in commands] if commands else None,
                    "command_count": len(commands),
                    "proposed_primary_flag": "--revision " + metadata[entry["hf_id"]]["revision"] if engine == "vllm" else None,
                    "spec_supported": bool(entry.get("spec_args")) if engine == "vllm" else entry["spec_supported"],
                    "external_speculative_artifacts": [{"repo_id": repo, "recipe_config": cfg,
                         "proposed_revision": metadata[repo]["revision"],
                         "proposed_pinned_spec_config": dict(cfg, revision=metadata[repo]["revision"]),
                         "revision_in_spec_config": cfg.get("revision"),
                         "pinning_status": "not pinned; draft pin must be wired separately from primary --revision"}
                        for repo, cfg in drafts.items()],
                    "pairable_as_declared": entry.get("pairable"),
                })
        for a in grouped["atlas"]:
            v = next((v for v in grouped["vllm"] if v["sku"] == a["sku"]), None)
            comparisons.append({"sku": a["sku"], "atlas_repo_id": a["hf_id"],
                "vllm_repo_id": v["hf_id"] if v else None,
                "same_checkpoint_as_same_sku_vllm": a["hf_id"] == v["hf_id"] if v else None,
                "different_from_primary_vllm_artifact": a["hf_id"] != primary,
                "reason": "same HF checkpoint ID; the Atlas kernel bundle is not a different weight artifact" if v and a["hf_id"] == v["hf_id"] else
                          "No vLLM profile on this SKU; GB10 NVFP4 is a separate rehearsal artifact" if a["hf_id"] != primary else
                          "No vLLM profile on this SKU; same checkpoint ID as scored vLLM profiles"})
        historical = {"revision": "9bee19446c0dfd01f356e10979d225b2a6621944",
                      "observed_utc": "2026-09-05T02:40:54/2026-09-05T02:40:56Z",
                      "source": "vllm-control/WEIGHTS-MANIFEST.md historical inventory",
                      "matches_current_metadata": metadata[primary]["revision"] == "9bee19446c0dfd01f356e10979d225b2a6621944"} if key == "nemotron-3-nano-fp8" else None
        records.append({"schema": 1, "model_key": key, "source": sources,
            "primary_repo_id": primary, "revision": metadata[primary]["revision"],
            "weight_bytes": metadata[primary]["weight_bytes"],
            "gated": metadata[primary]["gated"], "license": metadata[primary]["license"],
            "loaded_bytes_proven": False,
            "pin_semantics": "Metadata candidate only. A later run must prove it passed/loaded this revision; do not populate artifact.model.revision from this file alone.",
            "historical_nano_rehearsal_pin": historical,
            "atlas_supported_recipe_present": bool(grouped["atlas"]),
            "atlas_vs_vllm": comparisons,
            "profiles": profiles,
            "artifacts": [metadata[repo] for repo in sorted(artifact_ids)]})
    OUTPUT.write_text(json.dumps(records, indent=2) + "\n")
    print(f"PASS: {len(metadata)} captured repositories passed response hash, revision, unique-file and payload-size oracles")
    print(f"WROTE: {len(records)} model-key objects, {sum(len(r['profiles']) for r in records)} profiles")
    print(f"MISSING PRIMARY REVISION: {sum(1 for r in records for p in r['profiles'] if p['engine'] == 'vllm' and any(x is None for x in p['revision_in_recipe']))} vLLM profiles")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else assemble()
