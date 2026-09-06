#!/usr/bin/env python3
"""One unchanged latency ladder repeat; parent owns the ready server and cleanup."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/workspace/atlas-rental')
SOURCE = ROOT / 'src/atlas'


def validate(ladder):
    assert ladder['isl'] == 1024 and ladder['osl'] == 256, 'ISL/OSL mismatch'
    assert ladder.get('finished_utc'), 'unfinished ladder'
    assert ladder['reps'] == 3 and ladder['warmup'] == 1, 'changed repetition policy'
    assert sorted(r['concurrency'] for r in ladder['rungs']) == [1, 16], 'missing or duplicate rung'
    for rung in ladder['rungs']:
        assert rung['errors_total'] == 0, 'request errors'
        assert len(rung['reps']) == 3, 'missing timed repetition'
        for rep in rung['reps']:
            c = rung['concurrency']
            assert rep['n_ok'] == c, 'incomplete burst'
            assert len(rep['completion_tokens_per_req']) == c, 'missing output count'
            assert all(n == 256 for n in rep['completion_tokens_per_req']), 'output length mismatch'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session-dir', type=Path, required=True)
    parser.add_argument('--budget-seconds', type=int, default=180)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        fixture = {'isl': 1024, 'osl': 256, 'reps': 3, 'warmup': 1, 'finished_utc': 'fixture', 'rungs': [
            {'concurrency': c, 'errors_total': 0, 'reps': [
                {'n_ok': c, 'completion_tokens_per_req': [256] * c} for _ in range(3)]}
            for c in (1, 16)]}
        for bad in ('missing-rung', 'osl', 'output-count'):
            value = copy.deepcopy(fixture)
            if bad == 'missing-rung': value['rungs'].pop()
            elif bad == 'osl': value['osl'] = 255
            else: value['rungs'][1]['reps'][0]['completion_tokens_per_req'].pop()
            try: validate(value)
            except AssertionError: pass
            else: raise AssertionError('known-bad admitted: ' + bad)
        validate(fixture)
        print('3 known-bad refusals before complete two-rung acceptance')
        return 0
    out = args.session_dir
    assert out.is_dir() and (out / 'ready.utc').is_file(), 'ready owned session required'
    assert not (out / 'ladder.json').exists(), 'never overwrite a prior ladder'
    deadline = time.monotonic() + args.budget_seconds
    commands = []
    environment = dict(os.environ, W55_PROMPT_MODE='essay')
    environment['PATH'] = str(ROOT / 'vllm/bin') + ':' + environment.get('PATH', '')
    (out / 'aa-environment.json').write_text(json.dumps({'W55_PROMPT_MODE': 'essay',
        'PATH': environment['PATH']}, indent=2) + '\n')
    def run(name, argv, limit, allowed=(0,)):
        remaining = deadline - time.monotonic()
        if remaining < 5: raise TimeoutError('A/A child deadline exhausted')
        record = {'name': name, 'argv': argv, 'timeout_s': min(limit, remaining)}
        commands.append(record)
        (out / 'aa-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        try:
            with (out / (name + '.log')).open('w') as log:
                result = subprocess.run(argv, cwd=SOURCE, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=record['timeout_s'])
            record['exit'] = result.returncode
        except subprocess.TimeoutExpired:
            record['exit'] = 124
            raise
        finally:
            (out / 'aa-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if result.returncode not in allowed: raise RuntimeError(name + ' failed')
    run('aa-validator-selftest', ['python3', str(Path(__file__)), '--session-dir', str(out), '--selftest'], 5)
    for phase in ('pre', 'post'):
        gate = out / ('coherency-' + phase + '.json')
        run('coherency-' + phase, ['python3', 'bench/hopper_ab/coherency_gate.py', '--url',
            'http://127.0.0.1:8000', '--model', 'Qwen/Qwen3.8-27B-FP8', '--think', 'off',
            '--timeout', '40', '--out', str(gate)], 45, (0, 1))
        run('quality-policy-' + phase, ['python3', str(ROOT / 'reversal_exception.py'),
            '--source', str(SOURCE), '--coherency', str(gate), '--out',
            str(out / ('quality-policy-' + phase + '.json'))], 10)
        if phase == 'post': break
        run('endpoint-before-ladder', ['python3', 'bench/campaign/process_endpoint.py', 'owned',
            '--url', 'http://127.0.0.1:8000', '--record', str(out / 'owner.json'),
            '--out', str(out / 'endpoint-before-ladder.json')], 10)
        run('ladder', [str(ROOT / 'vllm/bin/python3'), 'bench/ladder38/harness_w55_conc_ladder.py',
            '--url', 'http://127.0.0.1:8000', '--model', 'Qwen/Qwen3.8-27B-FP8',
            '--label', 'rental.qwen38.vllm.' + out.name, '--out', str(out / 'ladder.json'),
            '--concs', '1,16', '--reps', '3', '--isl', '1024', '--osl', '256', '--warmup', '1'], 90)
        validate(json.loads((out / 'ladder.json').read_text()))
    (out / 'aa-complete.json').write_text(json.dumps({'complete': True,
        'scope': 'vLLM latency repeat; original gates retained, explicit reversal policy applied',
        'certification_claimed': False, 'commands': commands}, indent=2) + '\n')
    original = ROOT / 'results/benchmark.qwen38.vllm.lat01/ladder.json'
    validate(json.loads(original.read_text()))
    bad = json.loads((out / 'ladder.json').read_text())
    bad['osl'] = 257
    bad_path = out / 'aa-known-bad-osl.json'
    bad_path.write_text(json.dumps(bad, indent=2) + '\n')
    run('aa-compare-known-bad', ['python3', 'bench/hopper_ab/compare.py', '--atlas',
        str(bad_path), '--vllm', str(original)], 5, (2,))
    run('aa-compare', ['python3', 'bench/hopper_ab/compare.py', '--atlas',
        str(out / 'ladder.json'), '--vllm', str(original), '--out-json',
        str(out / 'aa-compare.json'), '--out-md', str(out / 'aa-compare.md')], 5)
    (out / 'aa-comparison-labels.txt').write_text('Both engines are vLLM. Legacy Atlas column is the new repeat; vLLM column is lat01. Raw labels unchanged. A tie is not presumed.\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
