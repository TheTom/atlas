#!/usr/bin/env python3
"""Run the existing concurrent quality oracle on a fresh owned server."""
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
import time

root = Path('/workspace/atlas-rental')
label = sys.argv[1]
if not re.fullmatch('[a-zA-Z0-9_-]+', label):
    raise SystemExit('invalid label')
out = root / f'results/benchmark.qwen38.atlas.{label}'
try:
    for _ in range(90):
        if (out / 'ready.utc').exists():
            (out / 'measurement-intent.json').write_text(json.dumps({
                'kind': 'concurrent_quality_only',
                'expected_requests': 17,
                'ladder_requested': False,
                'oracle': 'exact integer, stop finish, no tool or reasoning payload',
            }, indent=2) + '\n')
            break
        if (out / 'exit-code.txt').exists():
            raise RuntimeError('owned server exited before ready')
        time.sleep(1)
    else:
        raise RuntimeError('90-second readiness limit')
    query = subprocess.run(['pgrep', '-a', '-x', 'rustc|cargo|nvcc|ptxas'],
                           capture_output=True, text=True)
    (out / 'compiler-occupancy-quality.txt').write_text(query.stdout + query.stderr)
    if query.returncode != 1:
        raise RuntimeError('compiler occupancy or failed query')
    for name, argv in [
        ('quality-selftest', ['python3', str(root / 'concurrent_quality_probe.py'), '--selftest']),
        ('concurrent-quality', ['python3', str(root / 'concurrent_quality_probe.py'),
         '--url', 'http://127.0.0.1:8888', '--model', 'Qwen/Qwen3.8-27B-FP8',
         '--out', str(out / 'concurrent-quality')]),
        ('coherency', ['python3', str(root / 'src/atlas/bench/hopper_ab/coherency_gate.py'),
         '--url', 'http://127.0.0.1:8888', '--model', 'Qwen/Qwen3.8-27B-FP8',
         '--think', 'off', '--timeout', '120', '--out', str(out / 'coherency.json')]),
        ('quality-policy', ['python3', str(root / 'reversal_exception.py'),
         '--source', str(root / 'src/atlas'), '--coherency', str(out / 'coherency.json'),
         '--out', str(out / 'quality-policy.json')]),
    ]:
        cap = 90 if name == 'coherency' else 60
        with (out / f'{name}.log').open('w') as log:
            run = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, timeout=cap)
        (out / f'{name}.command.json').write_text(json.dumps({
            'argv': argv, 'exit_code': run.returncode, 'timeout_s': cap,
            'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }, indent=2) + '\n')
        allowed = (0, 1) if name == 'coherency' else (0,)
        if run.returncode not in allowed:
            raise RuntimeError(f'{name} failed: {run.returncode}')
finally:
    if out.is_dir():
        (out / 'requests-complete').write_text(
            datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n')
