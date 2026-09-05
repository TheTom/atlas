#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Download one pinned public checkpoint into the task-owned offline cache."""
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent


def digest(path, git_blob=False):
    size = path.stat().st_size
    h = hashlib.sha1() if git_blob else hashlib.sha256()
    if git_blob:
        h.update(f"blob {size}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ledger = json.loads((ROOT / sys.argv[1]).read_text())
    baseline = json.loads((ROOT / "baseline.json").read_text())["used"]
    from control_remote_job import permitted, snapshot
    repo = ROOT / "hf/hub" / ("models--" + ledger["hf_id"].replace("/", "--"))
    target = repo / "snapshots" / ledger["revision"]
    records = []
    for entry in ledger["files"]:
        relative = Path(entry["rfilename"])
        assert not relative.is_absolute() and ".." not in relative.parts
        destination = target / relative
        assert not destination.exists(), f"refuse to overwrite {destination}"
        sample = snapshot()
        assert permitted(baseline, sample["used"], sample["available"])
        assert sample["available"] - entry["size"] >= 16_000_000_000
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".incomplete")
        url = "https://huggingface.co/" + ledger["hf_id"] + "/resolve/" + ledger["revision"] + "/" + urllib.parse.quote(str(relative))
        with urllib.request.urlopen(url, timeout=90) as response, temporary.open("xb") as output:
            while chunk := response.read(8 * 1024 * 1024):
                sample = snapshot()
                assert permitted(baseline, sample["used"], sample["available"])
                output.write(chunk)
        lfs = entry.get("lfs")
        expected = lfs["sha256"] if lfs else entry["blobId"]
        observed = digest(temporary, git_blob=not lfs)
        assert temporary.stat().st_size == entry["size"] and observed == expected, str(relative)
        temporary.replace(destination)
        records.append({"path": str(relative), "bytes": entry["size"], "digest": observed, "passed": True})
        print(json.dumps(records[-1]), flush=True)
    (repo / "refs").mkdir(exist_ok=True)
    (repo / "refs/main").write_text(ledger["revision"])
    receipt = {"scope": "GB10 rehearsal only", "model": ledger["hf_id"], "revision": ledger["revision"], "snapshot": str(target), "files": records, "passed": True}
    (ROOT / (sys.argv[1] + ".verified.json")).write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
