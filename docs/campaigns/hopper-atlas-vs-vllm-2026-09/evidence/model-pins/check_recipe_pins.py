#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Observe recipe pin omissions. This is an evidence probe, not a runner fix."""

import json
import sys

from assemble_pins import draft_models, revision_arg

document = json.load(open(sys.argv[1]))
missing_commands = 0
missing_drafts = 0
for entry in document["entries"]:
    for rank, tokens in enumerate([entry["args"]] + (entry.get("worker_args") or [])):
        if revision_arg(tokens) is None:
            missing_commands += 1
            print(f"UNPINNED primary: {entry['model_key']}/{entry['sku']} node-rank={rank} "
                  f"repo={entry['hf_id']} missing --revision", file=sys.stderr)
    for repo, config in draft_models(entry).items():
        if config.get("revision") is None:
            missing_drafts += 1
            print(f"UNPINNED draft: {entry['model_key']}/{entry['sku']} repo={repo} "
                  "missing speculative-config revision", file=sys.stderr)
print(f"Observed {missing_commands} unpinned primary commands across "
      f"{len(document['entries'])} profiles; {missing_drafts} unpinned draft-profile references.")
sys.exit(1 if missing_commands or missing_drafts else 0)
