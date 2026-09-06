#!/usr/bin/env python3
"""Prepare or run one fresh-server cross-check within a ten-minute window."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

ROOT = Path('/workspace/atlas-rental')
EXPECTED = {
    'run_vllm_crosscheck.py': 'd2334551e4bb0c370cf6a9d8e9c33a3984d75d3891917ebafa344b871e97a1c1',
    'serve_qwen38_benchmark.sh': '12d7ac339ef15d6ccd1e4bd3d7da59e6448300509099c0e5ba80ccda626c1808',
}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def stop_child_group(child):
    """Only signal the session created by this wrapper's own Popen call."""
    if child is not None and child.poll() is None:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--lat-aa', action='store_true', help='Repeat the frozen latency ladder first if budget permits')
    args = parser.parse_args()
    if not re.fullmatch('[a-zA-Z0-9_-]+', args.label):
        parser.error('label must contain only letters, digits, underscore or hyphen')
    session = ROOT / f'results/benchmark.qwen38.vllm.{args.label}'
    control = ROOT / f'results/crosscheck-control.{args.label}'
    serve = ['bash', str(ROOT / 'serve_qwen38_benchmark.sh'), 'vllm', args.label, 'off']
    client = ['python3', str(ROOT / 'run_vllm_crosscheck.py'), '--session-dir',
              str(session), '--out', str(session / 'crosscheck'), '--num-prompts', '8', '--execute']
    plan = {'serve_argv': serve, 'client_argv': client, 'session': str(session),
            'control': str(control), 'expected_helper_sha256': EXPECTED,
            'wall_budget_seconds': 600, 'boot_budget_seconds': 300,
            'client_budget_seconds': 240, 'cleanup_reserve_seconds': 65,
            'certification_claimed': False, 'execution_requested': args.execute,
            'latency_aa_requested': args.lat_aa}
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return 0
    if session.exists() or control.exists():
        parser.error('fresh label required; existing evidence is never overwritten')
    for name, expected in EXPECTED.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            parser.error(f'{name} changed; review the new helper before execution')
    control.mkdir(mode=0o700)
    started = time.monotonic()
    deadline = started + 600
    env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    plan.update(started_utc=utc(), wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                inherited_environment_overrides={'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'})
    server = client_process = aa_process = None
    status = 1
    def record():
        (control / 'receipt.json').write_text(json.dumps(plan, indent=2) + '\n')
    def run(name, argv, timeout):
        with (control / (name + '.log')).open('w') as log:
            result = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        plan[name] = {'argv': argv, 'exit': result.returncode}
        record()
        return result.returncode
    def interrupted(number, frame):
        raise InterruptedError(f'received signal {number}')
    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(number, interrupted)
    record()
    try:
        if run('compiler-before', ['pgrep', '-a', '-x', 'rustc|cargo|nvcc|ptxas'], 5) != 1:
            raise RuntimeError('compiler occupancy or query error; no server started')
        if run('df-before', ['df', '-h', '/'], 5):
            raise RuntimeError('disk telemetry failed')
        # Existing server wrapper performs idle-GPU admission and endpoint ownership.
        with (control / 'serve-wrapper.log').open('w') as log:
            server = subprocess.Popen(serve, env=env, stdout=log, stderr=subprocess.STDOUT,
                                      start_new_session=True)
        plan['serve_wrapper_pid'] = server.pid
        record()
        boot_deadline = min(time.monotonic() + 300, deadline - 65)
        while not (session / 'ready.utc').is_file():
            if server.poll() is not None:
                raise RuntimeError(f'server wrapper exited before readiness: {server.returncode}')
            if time.monotonic() >= boot_deadline:
                raise TimeoutError('fresh-server boot exceeded 300-second budget')
            time.sleep(0.5)
        if run('compiler-ready', ['pgrep', '-a', '-x', 'rustc|cargo|nvcc|ptxas'], 5) != 1:
            raise RuntimeError('compiler occupancy or query error before measurement')
        if args.lat_aa:
            remaining = deadline - time.monotonic()
            if remaining >= 345:
                aa_argv = ['python3', str(ROOT / 'run_vllm_lat_aa.py'), '--session-dir',
                           str(session), '--budget-seconds', '180']
                plan['aa_argv'] = aa_argv
                plan['aa_helper_sha256'] = hashlib.sha256((ROOT / 'run_vllm_lat_aa.py').read_bytes()).hexdigest()
                record()
                with (control / 'latency-aa.log').open('w') as log:
                    aa_process = subprocess.Popen(aa_argv, env=env, stdout=log,
                        stderr=subprocess.STDOUT, start_new_session=True)
                aa_status = aa_process.wait(timeout=185)
                plan['latency-aa'] = {'argv': aa_argv, 'exit': aa_status}
                record()
                if aa_status:
                    raise RuntimeError(f'latency A/A failed: {aa_status}; retained result, no cross-check')
                plan['latency_aa_completed'] = True
            else:
                plan['latency_aa_omitted'] = {'remaining_s': remaining,
                    'required_s': 345, 'reason': 'preserve cross-check and cleanup budgets'}
                record()
        allowance = min(240, deadline - time.monotonic() - 65)
        if allowance < (90 if plan.get('latency_aa_completed') else 200):
            raise TimeoutError('insufficient client window before cleanup reserve')
        with (control / 'crosscheck.log').open('w') as log:
            client_process = subprocess.Popen(client, env=env, stdout=log, stderr=subprocess.STDOUT,
                                               start_new_session=True)
        status = client_process.wait(timeout=allowance)
        plan['client_exit'] = status
        client_receipt = session / 'crosscheck/receipt.json'
        if client_receipt.is_file():
            observed = json.loads(client_receipt.read_text())
            plan['endpoint_before_exit'] = observed.get('endpoint_before_exit')
            plan['endpoint_after_exit'] = observed.get('endpoint_after_exit')
            if status == 0 and (plan['endpoint_before_exit'] != 0 or plan['endpoint_after_exit'] != 0):
                status = 2
        elif status == 0:
            plan['error'] = 'client exited successfully without its evidence receipt'
            status = 2
    except (RuntimeError, TimeoutError, subprocess.TimeoutExpired, InterruptedError) as exc:
        plan['error'] = str(exc)
        status = 124 if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)) else 1
    finally:
        for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(number, signal.SIG_IGN)
        stop_child_group(client_process)
        stop_child_group(aa_process)
        if session.is_dir():
            (session / 'requests-complete').write_text(utc() + '\n')
        # The engine is a separate session. Stop only through the captured owner record.
        owner = session / 'owner.json'
        if owner.is_file():
            cleanup = ['python3', str(ROOT / 'src/atlas/bench/campaign/process_launch.py'),
                       'stop', '--record', str(owner), '--timeout', '15']
            try:
                if run('owned-stop', cleanup, 25):
                    status = 2
            except subprocess.TimeoutExpired:
                plan['cleanup_error'] = 'owned stop timed out; manual owner-based inspection required'
                status = 2
        if server is not None:
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                stop_child_group(server)
            plan['serve_wrapper_exit'] = server.returncode
            if status == 0 and server.returncode != 0:
                status = 2
        for name, argv in [('tenants-after', ['nvidia-smi', '--query-compute-apps=pid,process_name',
                                              '--format=csv,noheader']), ('df-after', ['df', '-h', '/'])]:
            try:
                if run(name, argv, 5):
                    status = 2
            except subprocess.TimeoutExpired:
                plan[name] = {'error': 'telemetry timeout'}
                status = 2
        plan.update(finished_utc=utc(), wall_seconds=time.monotonic() - started, exit=status)
        record()
    return status


if __name__ == '__main__':
    raise SystemExit(main())
