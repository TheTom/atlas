#!/usr/bin/env python3
"""Bounded client-concurrency quality diagnostic; not a scoring harness."""
import argparse
import datetime
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
import uuid

PAIRS = [(17, 23), (23, 19), (31, 7), (29, 13), (41, 11), (37, 17),
         (43, 19), (47, 23), (53, 7), (59, 11), (61, 13), (67, 17),
         (71, 19), (73, 23), (79, 29), (83, 31)]
MAX_BODY = 65536


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def request_body(model, pair, nonce):
    a, b = pair
    return {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'Return only the exact integer answer. No explanation, reasoning, tags or punctuation.'},
            {'role': 'user', 'content': f'Request nonce: {nonce}\nWhat is {a} * {b}?'},
        ],
        'temperature': 0.0, 'seed': 42, 'max_tokens': 32, 'stream': False,
        'chat_template_kwargs': {'enable_thinking': False},
    }


def judge(status, complete, body, expected):
    failures = []
    if status != 200:
        failures.append(f'HTTP status {status}, expected 200')
    if not complete:
        failures.append('response body not proven complete')
    try:
        parsed = json.loads(body)
        choices = parsed.get('choices')
        if not isinstance(choices, list) or len(choices) != 1:
            raise ValueError('expected exactly one choice')
        choice = choices[0]
        message = choice['message']
        content = message.get('content')
        if not isinstance(content, str) or content.strip() != str(expected):
            failures.append(f'final content is not exactly {expected}')
        if message.get('role') != 'assistant':
            failures.append('message role is not assistant')
        if message.get('tool_calls') or message.get('function_call'):
            failures.append('unexpected tool/function call')
        if message.get('reasoning_content') or message.get('reasoning'):
            failures.append('unexpected reasoning payload with thinking disabled')
        if choice.get('finish_reason') != 'stop':
            failures.append('completion did not end with stop')
        return {'passed': not failures, 'failures': failures,
                'content': content, 'finish_reason': choice.get('finish_reason'),
                'usage': parsed.get('usage')}
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        failures.append('invalid completion JSON: ' + str(error))
        return {'passed': False, 'failures': failures}


def worker(url, payload, directory, ready, start_event, socket_timeout):
    directory = Path(directory)
    ready.send(('ready', {'pid': os.getpid()}))
    start_event.wait()
    started = time.monotonic_ns()
    ready.send(('started', {'monotonic_ns': started, 'utc': utc()}))
    status = None
    headers = []
    complete = False
    failure = None
    total = 0
    try:
        req = urllib.request.Request(url.rstrip('/') + '/v1/chat/completions',
                                     data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json'})
        # Ignore proxy environment for this explicitly selected diagnostic URL.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            response = opener.open(req, timeout=socket_timeout)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            status = response.status
            headers = list(response.headers.items())
            save(directory / 'response-headers.json', {'status': status, 'headers': headers})
            reader = getattr(response, 'read1', response.read)
            with (directory / 'response.body').open('wb') as raw:
                while True:
                    chunk = reader(min(4096, MAX_BODY + 1 - total))
                    if not chunk:
                        complete = True
                        break
                    raw.write(chunk)
                    raw.flush()
                    total += len(chunk)
                    if total > MAX_BODY:
                        raise ValueError('response exceeds 64 KiB diagnostic cap')
            length = response.headers.get('Content-Length')
            if length is not None and int(length) != total:
                complete = False
                raise ValueError('Content-Length does not match complete body')
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    ready.send(('done', {'status': status, 'headers': headers, 'complete': complete,
                         'transport_error': failure, 'bytes': total,
                         'started_ns': started, 'finished_ns': time.monotonic_ns(),
                         'finished_utc': utc()}))
    ready.close()


def stop_child(process):
    # These are child Process handles created by this probe, never engine PIDs.
    process.join(timeout=0.1)
    if process.is_alive():
        process.terminate()
    process.join(timeout=0.5)
    if process.is_alive():
        process.kill()
        process.join(timeout=0.5)
    if process.is_alive():
        raise RuntimeError('owned request child could not be reaped')


def run_batch(url, model, out, pairs, prefix, seconds):
    ctx = mp.get_context('spawn')
    event = ctx.Event()
    children = []
    setup_deadline = time.monotonic() + 10
    for index, pair in enumerate(pairs):
        name = f'{prefix}-{index:02d}'
        directory = out / name
        directory.mkdir()
        nonce = uuid.uuid4().hex
        payload = request_body(model, pair, nonce)
        save(directory / 'request.json', payload)
        receiver, sender = ctx.Pipe(duplex=False)
        process = ctx.Process(target=worker,
                             args=(url, payload, str(directory), sender, event, min(seconds, 10)))
        process.start()
        sender.close()
        children.append({'process': process, 'pipe': receiver, 'directory': directory,
                         'id': name, 'pair': pair, 'nonce': nonce, 'ready': False,
                         'started': None, 'result': None})
    released_ns = None
    deadline = setup_deadline
    try:
        while any(child['result'] is None for child in children):
            for child in children:
                if child['result'] is not None:
                    continue
                while child['pipe'].poll():
                    try:
                        kind, payload = child['pipe'].recv()
                    except EOFError:
                        break
                    if kind == 'ready': child['ready'] = True
                    elif kind == 'started': child['started'] = payload
                    elif kind == 'done': child['result'] = payload
                if (child['result'] is None and not child['process'].is_alive()
                        and not child['pipe'].poll()):
                    child['result'] = {'status': None, 'complete': False,
                                       'transport_error': 'request child exited without result',
                                       'finished_ns': time.monotonic_ns(), 'finished_utc': utc()}
            if released_ns is None and all(c['ready'] for c in children):
                released_ns = time.monotonic_ns()
                event.set()
                deadline = time.monotonic() + seconds
            if time.monotonic() >= deadline:
                for child in children:
                    if child['result'] is None:
                        child['result'] = {'status': None, 'complete': False,
                                           'transport_error': 'owned request wall deadline exceeded',
                                           'finished_ns': time.monotonic_ns(), 'finished_utc': utc()}
                break
            time.sleep(0.005)
    finally:
        for child in children:
            stop_child(child['process'])
            child['pipe'].close()
    rows = []
    intervals = []
    for child in children:
        result = child['result']
        header_path = child['directory'] / 'response-headers.json'
        if result.get('status') is None and header_path.exists():
            captured_headers = json.loads(header_path.read_text())
            result.update(captured_headers)
        raw_path = child['directory'] / 'response.body'
        raw = raw_path.read_bytes() if raw_path.exists() else b''
        verdict = judge(result.get('status'), result.get('complete', False), raw,
                        child['pair'][0] * child['pair'][1])
        if result.get('transport_error'):
            verdict['passed'] = False
            verdict['failures'].append(result['transport_error'])
        start = child['started']
        if start:
            intervals.append((start['monotonic_ns'], result['finished_ns']))
        row = {'id': child['id'], 'operands': child['pair'], 'nonce': child['nonce'],
               'expected': child['pair'][0] * child['pair'][1], 'started': start,
               'elapsed_s': ((result['finished_ns'] - start['monotonic_ns']) / 1e9) if start else None,
               'response_sha256': hashlib.sha256(raw).hexdigest(),
               'raw_response_file': str(raw_path.relative_to(out)),
               'transport': result, 'oracle': verdict, 'child_exit': child['process'].exitcode}
        save(child['directory'] / 'result.json', row)
        rows.append(row)
    active = maximum = 0
    for _, delta in sorted([(s, 1) for s, _ in intervals] + [(e, -1) for _, e in intervals]):
        active += delta
        maximum = max(maximum, active)
    return {'label': prefix, 'requested_concurrency': len(pairs), 'released_ns': released_ns,
            'max_overlapping_client_http_attempts': maximum,
            'requested_overlap_observed': maximum == len(pairs), 'rows': rows,
            'passed': all(r['oracle']['passed'] for r in rows)}


def selftest():
    def completion(content='391', **extra):
        message = {'role': 'assistant', 'content': content, **extra}
        return json.dumps({'choices': [{'message': message, 'finish_reason': 'stop'}]}).encode()
    bad = [(500, True, completion()), (200, False, completion()),
           (200, True, b'{'), (200, True, completion('437')),
           (200, True, completion('<think>x</think>391')),
           (200, True, completion('The answer is 391.')),
           (200, True, completion(reasoning_content='hidden reasoning')),
           (200, True, completion(tool_calls=[{'id': 'foreign'}])),
           (200, True, completion().replace(b'"stop"', b'"length"'))]
    for status, complete, body in bad:
        assert not judge(status, complete, body, 391)['passed'], 'known-bad oracle admitted'
    assert judge(200, True, completion(), 391)['passed']
    assert judge(200, True, completion(' 391\n'), 391)['passed']
    print(f'{len(bad)} known-bad refusals before two exact-answer acceptances')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url')
    parser.add_argument('--model')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.url or not args.model or args.out is None:
        parser.error('--url, --model and --out are required')
    args.out.mkdir(parents=True, exist_ok=False)
    started = utc()
    control = run_batch(args.url, args.model, args.out, [PAIRS[0]], 'c1', 10)
    concurrent = run_batch(args.url, args.model, args.out, PAIRS, 'c16', 20)
    report = {'started_utc': started, 'finished_utc': utc(), 'url': args.url,
              'model': args.model, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scope': 'Diagnostic only; exact arithmetic, HTTP and protocol oracle. Client HTTP-attempt overlap does not prove server admission, active batch size or simultaneous GPU rows.',
              'stopping_rule': 'One C1 plus one C16 batch only; no retries. Owned request children have wall deadlines; all results retained even if the control fails.',
              'control': control, 'concurrent': concurrent,
              'quality_passed': control['passed'] and concurrent['passed'],
              'passed': control['passed'] and concurrent['passed'] and concurrent['requested_overlap_observed']}
    save(args.out / 'summary.json', report)
    print(json.dumps({'passed': report['passed'], 'max_overlap': concurrent['max_overlapping_client_http_attempts'],
                      'failed_ids': [r['id'] for b in [control, concurrent] for r in b['rows'] if not r['oracle']['passed']],
                      'out': str(args.out)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
