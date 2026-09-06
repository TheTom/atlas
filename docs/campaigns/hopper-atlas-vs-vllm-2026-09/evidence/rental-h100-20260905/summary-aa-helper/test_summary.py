#!/usr/bin/env python3
"""CPU fixtures for diagnostic summary discovery; all fixture data is synthetic."""
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'measurement-summary.py'
SOURCE = ROOT.parents[2] / 'atlas-campaign-code'

class SummaryTests(unittest.TestCase):
    def run_case(self, change=None):
        with tempfile.TemporaryDirectory(prefix='summary-fixture-') as temp:
            temp = pathlib.Path(temp)
            raw, out = temp / 'raw', temp / 'derived'
            raw.mkdir()
            for name in ['benchmark.qwen38.atlas.native-lat02', 'benchmark.qwen38.atlas.native-agent01', 'benchmark.qwen38.vllm.lat01', 'benchmark.qwen38.vllm.agent01']:
                self.copy_fixture(ROOT / 'remote-results' / name, raw / name)
            for workload, old in [('lat', 'benchmark.qwen38.atlas.native-lat02'), ('agent', 'benchmark.qwen38.atlas.native-agent01')]:
                name = f'benchmark.qwen38.atlas.native-head-{workload}01'
                self.copy_fixture(raw / old, raw / name)
                p = raw / name / 'ladder.json'
                d = json.loads(p.read_text())
                d['label'] = 'SYNTHETIC TEST ONLY ' + name
                d['started_utc'] = '2099-01-01T00:00:00Z'
                p.write_text(json.dumps(d))
            if change:
                change(raw)
            before = {str(p): p.read_bytes() for p in raw.rglob('*') if p.is_file()}
            run = subprocess.run(['python3', str(SCRIPT), '--raw', str(raw), '--source', str(SOURCE), '--out', str(out)], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(before, {str(p): p.read_bytes() for p in raw.rglob('*') if p.is_file()})
            return json.loads((out / 'measurement-summary.json').read_text())

    def copy_fixture(self, source, dest):
        dest.mkdir()
        for name in ['ladder.json', 'launch.json', 'process-env.json', 'coherency-pre.json', 'coherency-post.json', 'quality-policy-pre.json', 'quality-policy-post.json', 'measurement-complete.json']:
            shutil.copyfile(source / name, dest / name)

    def test_new_labels_preserve_baseline_pairs_and_failed_gates(self):
        d = self.run_case()
        self.assertEqual(len(d['cells']), 6)
        pairs = {(x['atlas_input'], x['vllm_input']): x for x in d['comparisons']}
        for workload, old in [('lat', 'benchmark.qwen38.atlas.native-lat02'), ('agent', 'benchmark.qwen38.atlas.native-agent01')]:
            new = f'benchmark.qwen38.atlas.native-head-{workload}01'
            control = f'benchmark.qwen38.vllm.{workload}01'
            self.assertIn((old, control), pairs)
            self.assertIn((new, control), pairs)
            self.assertEqual(pairs[new, old]['input_engines'], ['atlas', 'atlas'])
            self.assertEqual(pairs[new, old]['kind'], 'atlas_native_after_vs_before')
        self.assertFalse(d['certification_claimed'])
        for c in d['cells']:
            self.assertFalse(c['gates']['coherency-post']['passed'])
            self.assertFalse(c['certification_claimed'])

    def test_empty_export_is_pending_not_silently_dropped(self):
        name = 'benchmark.qwen38.atlas.native-head-agent01'
        def change(raw):
            p = raw / name / 'ladder.json'
            d = json.loads(p.read_text()); d['rungs'] = []; d.pop('finished_utc', None)
            p.write_text(json.dumps(d))
        d = self.run_case(change)
        item = next((x for x in d['pending_sessions'] if x['directory'] == name), None)
        self.assertIsNotNone(item, 'An existing empty-rung export vanished from cells and pending')
        self.assertEqual(item['status'], 'no_completed_rung_export_yet')
        self.assertIsNotNone(item['ladder_sha256'])
        self.assertFalse(item['certification_claimed'])

    def test_vllm_repeat_has_actual_aa_pair_and_no_identity_upgrade(self):
        name = 'benchmark.qwen38.vllm.lat-repeat01'
        def change(raw):
            self.copy_fixture(raw / 'benchmark.qwen38.vllm.lat01', raw / name)
            p = raw / name / 'ladder.json'
            d = json.loads(p.read_text()); d['label'] = 'SYNTHETIC IDENTICAL VLLM REPEAT'; d['started_utc'] = '2099-02-01T00:00:00Z'
            p.write_text(json.dumps(d))
        d = self.run_case(change)
        pair = next((p for p in d['comparisons'] if p['atlas_input'] == name and p['vllm_input'] == 'benchmark.qwen38.vllm.lat01'), None)
        self.assertIsNotNone(pair, 'The actual vLLM repeat was discovered but no A/A comparison was emitted')
        self.assertEqual(pair['kind'], 'vllm_after_vs_before')
        self.assertEqual(pair['input_engines'], ['vllm', 'vllm'])
        self.assertFalse(pair['vllm_repeat_profile_parity']['immutable_engine_identity_proven'])
        self.assertTrue(pair['vllm_repeat_profile_parity']['serve_argv_except_executable_equal'])
        self.assertTrue(all(row['verdict'] == 'TIE' for row in pair['result']['rows']))
        self.assertFalse(next(c for c in d['cells'] if c['directory'] == name)['certification_claimed'])

    def test_missing_argv_preserves_unproven_parity(self):
        name = 'benchmark.qwen38.atlas.native-head-lat01'
        def change(raw):
            (raw / name / 'launch.json').unlink()
        d = self.run_case(change)
        pair = next(x for x in d['comparisons'] if x['atlas_input'] == name and x['kind'] == 'atlas_native_after_vs_before')
        self.assertIsNone(pair['native_profile_parity']['serve_argv_except_executable_equal'])
        self.assertFalse(pair['native_profile_parity']['both_captured_bf16_head'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
