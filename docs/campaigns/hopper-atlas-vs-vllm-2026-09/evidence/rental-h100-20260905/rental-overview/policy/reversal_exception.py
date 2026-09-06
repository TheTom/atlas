#!/usr/bin/env python3
"""Apply the user's rental-only reversal exception without changing gate JSON."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def load_gate(source):
    path = Path(source) / 'bench/hopper_ab/coherency_gate.py'
    spec = importlib.util.spec_from_file_location('rental_gate', path)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return gate


def evaluate(report, gate):
    for key in ('determinism_ok', 'toolcall_ok', 'think_leak_ok'):
        if report.get(key) is not True:
            raise ValueError('non-reversal gate failed or missing: ' + key)
    if report.get('request_policy') != gate.request_policy('off'):
        raise ValueError('thinking policy is not the measured off policy')
    exchanges = report.get('http_exchanges', [])
    if len(exchanges) != 7 or any(x.get('response_status') != 200 or
                                 x.get('response_complete') is not True for x in exchanges):
        raise ValueError('missing or incomplete successful gate exchanges')
    known = [x for x in exchanges if x.get('check') == 'known_answer_ok']
    if len(known) != len(gate.KNOWN_ANSWER_CASES):
        raise ValueError('known-answer evidence is incomplete')
    rows = []
    for exchange, (prompt, expected) in zip(known, gate.KNOWN_ANSWER_CASES):
        request = json.loads(exchange['request_json'])
        original = gate.body(report['model'], prompt, think='off', messages=[
            {'role': 'system', 'content': gate.KNOWN_ANSWER_SYSTEM},
            {'role': 'user', 'content': prompt}])
        if request != original:
            raise ValueError('known-answer request differs from the frozen request')
        response = json.loads(exchange['response_body'])
        text, _ = gate.completion_of(response)
        status, detail = gate.judge_known_answer(text, expected)
        if status != 'OK' and (expected != 'rotaregirfer' or
                              not (detail.startswith('answer not stated:') or
                                   status == 'WORKING-ONLY')):
            raise ValueError(f'additional quality failure: {expected}: {status}: {detail}')
        rows.append({'expected': expected, 'status': status, 'detail': detail})
    return {'policy': 'user-authorized-rental-word-reversal-exception',
            'original_gate_passed': report.get('passed'),
            'proceed_with_performance_testing': True, 'known_answers': rows,
            'certification_claimed': False}


def selftest(report, gate):
    mutations = []
    for key in ('determinism_ok', 'toolcall_ok', 'think_leak_ok'):
        bad = copy.deepcopy(report); bad[key] = False; mutations.append(bad)
    bad = copy.deepcopy(report); bad['http_exchanges'].pop(); mutations.append(bad)
    for expected in ('391', 'Tokyo', 'rotaregirfer'):
        bad = copy.deepcopy(report)
        index = [e for e in bad['http_exchanges'] if e['check'] == 'known_answer_ok'][
            ['391', 'Tokyo', 'rotaregirfer'].index(expected)]
        body = json.loads(index['response_body'])
        body['choices'][0]['message']['content'] = '\x00' * 100 if expected == 'rotaregirfer' else 'Wrong answer.'
        index['response_body'] = json.dumps(body); mutations.append(bad)
    for bad in mutations:
        try:
            evaluate(bad, gate)
        except (ValueError, KeyError):
            continue
        raise AssertionError('known-bad additional failure was admitted')
    evaluate(report, gate)
    print(f'{len(mutations)} known-bad refusals before one live-evidence acceptance')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--coherency', required=True)
    parser.add_argument('--out')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    path = Path(args.coherency)
    report = json.loads(path.read_text())
    gate = load_gate(args.source)
    if args.selftest:
        selftest(report, gate)
    else:
        result = evaluate(report, gate)
        result['original_gate_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        result['original_gate_path'] = str(path)
        Path(args.out).write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))


if __name__ == '__main__':
    main()
