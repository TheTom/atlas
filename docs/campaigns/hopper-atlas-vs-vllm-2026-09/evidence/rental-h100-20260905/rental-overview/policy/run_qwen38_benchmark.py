#!/usr/bin/env python3
"""Run one unchanged ladder after the user's narrowly scoped quality policy."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path('/workspace/atlas-rental')
SOURCE = ROOT / 'src/atlas'


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('engine', choices=('atlas', 'vllm'))
    parser.add_argument('label')
    parser.add_argument('workload', choices=('lat', 'agent'))
    args = parser.parse_args()
    if not re.fullmatch('[a-zA-Z0-9_-]+', args.label):
        parser.error('invalid label')
    out = ROOT / f'results/benchmark.qwen38.{args.engine}.{args.label}'
    url = f'http://127.0.0.1:{8888 if args.engine == "atlas" else 8000}'
    model = 'Qwen/Qwen3.8-27B-FP8'
    environment = dict(os.environ, W55_PROMPT_MODE='essay')
    environment['PATH'] = str(ROOT / 'vllm/bin') + ':' + environment.get('PATH', '')
    commands = []

    def run(name, argv, allowed=(0,), timeout=900):
        record = {'name': name, 'argv': argv, 'started': utc(), 'timeout_s': timeout}
        with (out / (name + '.log')).open('w') as log:
            result = subprocess.run(argv, cwd=SOURCE, env=environment, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        record.update(exit_code=result.returncode, finished=utc())
        commands.append(record)
        (out / 'measurement-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        print(json.dumps(record), flush=True)
        if result.returncode not in allowed:
            raise RuntimeError(f'{name} failed: {result.returncode}')

    try:
        for _ in range(930):
            if (out / 'ready.utc').exists():
                break
            if (out / 'exit-code.txt').exists():
                raise RuntimeError('server exited before readiness')
            time.sleep(1)
        else:
            raise RuntimeError('readiness deadline expired')
        compiler = subprocess.run(['pgrep', '-a', '-x', 'rustc|cargo|nvcc|ptxas'],
                                  capture_output=True, text=True)
        (out / 'compiler-occupancy-before.txt').write_text(compiler.stdout + compiler.stderr)
        if compiler.returncode != 1:
            raise RuntimeError('compiler work or occupancy query error before measurement')
        (out / 'measurement-wrapper.sha256').write_text(
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest() + '\n')
        (out / 'measurement-harness.sha').write_text(subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True))
        deadline = datetime.datetime(2026, 9, 6, 1, 40, tzinfo=datetime.timezone.utc)
        if (deadline - datetime.datetime.now(datetime.timezone.utc)).total_seconds() < 1800:
            raise RuntimeError('final export reserve forbids starting another measurement')
        for phase in ('pre', 'post'):
            gate_path = out / f'coherency-{phase}.json'
            run('coherency-' + phase, ['python3', 'bench/hopper_ab/coherency_gate.py',
                '--url', url, '--model', model, '--think', 'off', '--timeout', '120',
                '--out', str(gate_path)], allowed=(0, 1), timeout=1000)
            run('quality-policy-' + phase, ['python3', str(ROOT / 'reversal_exception.py'),
                '--source', str(SOURCE), '--coherency', str(gate_path),
                '--out', str(out / f'quality-policy-{phase}.json')], timeout=20)
            if phase == 'post':
                break
            run('endpoint-before-ladder', ['python3', 'bench/campaign/process_endpoint.py',
                'owned', '--url', url, '--record', str(out / 'owner.json'),
                '--out', str(out / 'endpoint-before-ladder.json')], timeout=20)
            isl, osl = (1024, 256) if args.workload == 'lat' else (4096, 512)
            run('ladder', [str(ROOT / 'vllm/bin/python3'),
                'bench/ladder38/harness_w55_conc_ladder.py', '--url', url,
                '--model', model, '--label', f'rental.qwen38.{args.engine}.{args.label}',
                '--out', str(out / 'ladder.json'), '--concs', '1,16', '--reps', '3',
                '--isl', str(isl), '--osl', str(osl), '--warmup', '1'], timeout=1200)
            ladder = json.loads((out / 'ladder.json').read_text())
            for rung in ladder['rungs']:
                if rung['errors_total'] != 0:
                    raise RuntimeError('ladder request errors')
                for rep in rung['reps']:
                    if rep['n_ok'] != rung['concurrency'] or any(
                            n != osl for n in rep['completion_tokens_per_req']):
                        raise RuntimeError('incomplete burst or unequal requested output work')
        (out / 'measurement-complete.json').write_text(json.dumps({
            'finished': utc(), 'workload': args.workload, 'all_requested_outputs_complete': True,
            'quality_policy_pre_and_post_passed': True, 'certification_claimed': False}, indent=2) + '\n')
    finally:
        if out.is_dir():
            (out / 'requests-complete').write_text(utc() + '\n')


if __name__ == '__main__':
    main()
