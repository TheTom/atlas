#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Step D3 evidence collector: model metadata only; never downloads files."""

import argparse
import hashlib
import json
import platform
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import httpx
import huggingface_hub
from huggingface_hub import HfApi, set_client_factory


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    receipt = {
        "repo_id": args.repo,
        "started_utc": utc(),
        "python_version": platform.python_version(),
        "huggingface_hub_version": huggingface_hub.__version__,
        "httpx_version": httpx.__version__,
        "authentication": False,
        "api_call": "HfApi(token=False).model_info(repo_id, files_metadata=True, token=False, timeout=60)",
        "revision_argument": None,
        "revision_meaning": "Current default-branch head at request time, not proof of loaded bytes",
        "http_responses": [],
    }

    def capture(response):
        raw = response.read()
        name = f"response-{len(receipt['http_responses']) + 1}.json"
        (args.out / name).write_bytes(raw)
        receipt["http_responses"].append({
            "url": str(response.request.url),
            "method": response.request.method,
            "status_code": response.status_code,
            "captured_utc": utc(),
            "body_path": name,
            "body_bytes": len(raw),
            "body_sha256": hashlib.sha256(raw).hexdigest(),
            "headers": {k: v for k, v in response.headers.items()
                        if k.lower() in {"content-type", "content-length", "etag", "date", "x-request-id"}},
        })

    set_client_factory(lambda: httpx.Client(follow_redirects=True, event_hooks={"response": [capture]}))
    start = time.monotonic()
    code = 0
    try:
        info = HfApi(token=False).model_info(args.repo, files_metadata=True, token=False, timeout=60)
        receipt.update({"status": "ok", "sha": info.sha, "gated": info.gated,
                        "private": info.private, "sibling_count": len(info.siblings or [])})
        print(json.dumps({k: receipt[k] for k in ("repo_id", "status", "sha", "gated", "private", "sibling_count")}, sort_keys=True))
    except Exception as exc:
        code = 2
        receipt.update({"status": "error", "error_type": type(exc).__name__, "error": str(exc)})
        traceback.print_exc()
    finally:
        receipt.update({"finished_utc": utc(), "wall_seconds": time.monotonic() - start,
                        "exit_code": code})
        (args.out / "request.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
