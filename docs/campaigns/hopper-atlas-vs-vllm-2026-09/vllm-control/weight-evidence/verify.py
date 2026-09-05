#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Verify the saved HF metadata and byte totals without downloading weights."""

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(data):
    files = data["siblings"]
    require(bool(files), "empty file list")
    names = [entry["rfilename"] for entry in files]
    require(len(names) == len(set(names)), "duplicate repository path")
    for entry in files:
        size = entry.get("size")
        require(type(size) is int and size >= 0, "missing or invalid file size")
        if "lfs" in entry:
            require(entry["lfs"]["size"] == size, "LFS payload size differs")
    tensors = [entry for entry in files if entry["rfilename"].endswith(".safetensors")]
    return {
        "file_count": len(files),
        "all_files_bytes": sum(entry["size"] for entry in files),
        "safetensors_file_count": len(tensors),
        "safetensors_bytes": sum(entry["size"] for entry in tensors),
    }


def verify_record(row, data):
    require(row["http_status"] == 200, "API request was not successful")
    require(data["id"] == row["canonical_id"], "canonical repository ID differs")
    require(data["sha"] == row["revision"], "revision differs")
    require(bool(re.fullmatch("[0-9a-f]{40}", row["revision"])), "revision is not a full SHA")
    for key, value in summarize(data).items():
        require(row[key] == value, f"{key} differs from saved API metadata")


def verify(base):
    index = json.loads((base / "index.json").read_text())
    ledger_meta = index["file_ledger"]
    ledger_raw = (base / ledger_meta["file"]).read_bytes()
    require(hashlib.sha256(ledger_raw).hexdigest() == ledger_meta["sha256"], "ledger checksum differs")
    ledger = {row["hf_id"]: row for row in json.loads(ledger_raw)["models"]}
    ids = [row["hf_id"] for row in index["models"]]
    require(len(ids) == len(set(ids)), "duplicate model ID")
    require(set(ids) == set(ledger), "ledger coverage differs")
    for row in index["models"]:
        packed = (base / row["response_file"]).read_bytes()
        require(len(packed) == row["compressed_bytes"], "compressed length differs")
        require(hashlib.sha256(packed).hexdigest() == row["compressed_sha256"], "compressed checksum differs")
        raw = gzip.decompress(packed)
        require(len(raw) == row["response_bytes"], "response length differs")
        require(hashlib.sha256(raw).hexdigest() == row["response_sha256"], "response checksum differs")
        data = json.loads(raw)
        verify_record(row, data)
        require(ledger[row["hf_id"]]["revision"] == data["sha"], "ledger revision differs")
        require(ledger[row["hf_id"]]["files"] == data["siblings"], "ledger files differ")
    print(f"PASS: {len(ids)} API responses, hashes, revisions, file ledgers and exact byte totals")


def selftest():
    data = {"id": "fixture/model", "sha": "a" * 40, "siblings": [
        {"rfilename": "model.safetensors", "size": 10, "lfs": {"size": 10}},
        {"rfilename": "config.json", "size": 3},
    ]}
    row = {"http_status": 200, "canonical_id": data["id"], "revision": data["sha"], **summarize(data)}
    bad_data = copy.deepcopy(data)
    del bad_data["siblings"][0]["size"]
    bad_lfs = copy.deepcopy(data)
    bad_lfs["siblings"][0]["lfs"]["size"] = 1
    cases = [
        ("missing size rejected", row, bad_data),
        ("LFS pointer/payload mismatch rejected", row, bad_lfs),
        ("incorrect total rejected", {**row, "all_files_bytes": 12}, data),
        ("wrong revision rejected", {**row, "revision": "b" * 40}, data),
    ]
    for label, candidate, source in cases:
        try:
            verify_record(candidate, source)
        except ValueError as exc:
            print(f"PASS negative: {label}: {exc}")
        else:
            raise AssertionError(f"instrument accepted bad fixture: {label}")
    verify_record(row, data)
    print("PASS positive: 13 total bytes includes 10 safetensors bytes plus 3 config bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        verify(Path(__file__).resolve().parent)
