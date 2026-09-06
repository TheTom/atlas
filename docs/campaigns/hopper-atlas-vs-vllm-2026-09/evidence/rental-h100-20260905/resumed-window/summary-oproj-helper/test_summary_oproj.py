#!/usr/bin/env python3
"""Synthetic CPU fixtures for resumed labels and explicit quality-only intent."""
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('summary_fixtures', ROOT / 'tooling-fixes/measurement-summary-head-labels/test_summary.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)

class ResumedSummaryTests(fixtures.SummaryTests):
    def make_oproj(self, raw, *, pending=False):
        name='benchmark.qwen38.atlas.native-oproj-lat01'
        self.copy_fixture(raw/'benchmark.qwen38.atlas.native-head-lat01', raw/name)
        p=raw/name/'ladder.json';d=json.loads(p.read_text());d['started_utc']='2099-03-01T00:00:00Z';d['label']='SYNTHETIC OPROJ ONLY'
        if pending:d['rungs']=[];d.pop('finished_utc',None)
        p.write_text(json.dumps(d));return name

    def test_oproj_partial_is_retained(self):
        d=self.run_case(lambda raw:self.make_oproj(raw,pending=True))
        item=next(x for x in d['pending_sessions'] if x['directory'].endswith('native-oproj-lat01'))
        self.assertEqual(item['status'],'no_completed_rung_export_yet')
        self.assertFalse(item['certification_claimed'])

    def test_oproj_complete_pairs_preserve_old_heads(self):
        d=self.run_case(self.make_oproj)
        pairs={(p['atlas_input'],p['vllm_input']):p for p in d['comparisons']}
        new='benchmark.qwen38.atlas.native-oproj-lat01';old='benchmark.qwen38.atlas.native-head-lat01';control='benchmark.qwen38.vllm.lat01'
        self.assertIn((new,old),pairs);self.assertIn((new,control),pairs);self.assertIn((old,control),pairs)
        self.assertEqual(pairs[new,old]['kind'],'atlas_native_after_vs_before')

    def quality_case(self, *, observed=False, bad_row=False, command_exit=0):
        name='benchmark.qwen38.atlas.native-oproj-quality01'
        def change(raw):
            p=raw/name;p.mkdir();(p/'measurement-intent.json').write_text(json.dumps({'kind':'concurrent_quality_only','expected_requests':17,'ladder_requested':False}))
            (p/'requests-complete').write_text('SYNTHETIC cleanup marker only')
            if observed:
                q=ROOT/'remote-results/benchmark.qwen38.atlas.native-head-lat01/concurrent-quality/summary.json'
                (p/'concurrent-quality').mkdir();summary=json.loads(q.read_text())
                if bad_row:summary['concurrent']['rows'][0]['oracle']['passed']=False
                (p/'concurrent-quality/summary.json').write_text(json.dumps(summary))
                (p/'concurrent-quality.command.json').write_text(json.dumps({'exit_code':command_exit}))
                (p/'coherency.json').write_text(json.dumps({'passed':False,'synthetic_only':'sole reversal'}))
                (p/'coherency.command.json').write_text(json.dumps({'exit_code':1}))
                (p/'quality-policy.json').write_text(json.dumps({'proceed_with_performance_testing':True,'original_gate_passed':False,'certification_claimed':False}))
                (p/'quality-policy.command.json').write_text(json.dumps({'exit_code':0}))
        return name,self.run_case(change)

    def test_quality_only_marker_does_not_become_pending_ladder_or_pass(self):
        name,d=self.quality_case()
        self.assertNotIn(name,[x['directory'] for x in d['pending_sessions']])
        item=next(x for x in d['diagnostic_sessions'] if x['directory']==name)
        self.assertFalse(item['request_oracle_observed_passed'])
        self.assertFalse(item['certification_claimed'])

    def test_quality_pass_requires_observed_rows_and_command(self):
        name,d=self.quality_case(observed=True)
        item=next(x for x in d['diagnostic_sessions'] if x['directory']==name)
        self.assertTrue(item['request_oracle_observed_passed'])
        self.assertEqual(item['observed_request_count'],17)
        self.assertNotIn(name,[x['directory'] for x in d['cells']])

    def test_bad_row_or_failed_command_keeps_quality_false(self):
        for kwargs in [{'bad_row':True},{'command_exit':1}]:
            with self.subTest(**kwargs):
                name,d=self.quality_case(observed=True,**kwargs)
                item=next(x for x in d['diagnostic_sessions'] if x['directory']==name)
                self.assertFalse(item['request_oracle_observed_passed'])

    def test_quality_coherency_false_and_policy_remain_separate(self):
        name,d=self.quality_case(observed=True)
        item=next(x for x in d['diagnostic_sessions'] if x['directory']==name)
        self.assertFalse(item['coherency']['passed'])
        self.assertEqual(item['coherency_command']['exit_code'],1)
        self.assertTrue(item['exception_policy']['proceed_with_performance_testing'])
        self.assertFalse(item['certification_claimed'])

if __name__=='__main__':unittest.main(verbosity=2)
