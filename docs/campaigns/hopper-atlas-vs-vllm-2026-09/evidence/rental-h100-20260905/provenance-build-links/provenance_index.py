#!/usr/bin/env python3
"""Index retained rental observations; never synthesize a campaign artifact."""
import hashlib
import json
import pathlib
import re
import subprocess

BASE = pathlib.Path('/Users/tom/Documents/New project')
CAMPAIGN = BASE / 'atlas-campaign-docs/docs/campaigns/hopper-atlas-vs-vllm-2026-09'
EVIDENCE = CAMPAIGN / 'evidence/rental-h100-20260905'
CODE = BASE / 'atlas-campaign-code'

def read(p):
    return json.loads(p.read_text()) if p.exists() else None

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def ref(p):
    return str(p.relative_to(CAMPAIGN))

def first(directory, names):
    return next((directory / n for n in names if (directory / n).exists()), None)

staging = {}
for p in EVIDENCE.rglob('*staging*json'):
    d = read(p)
    if isinstance(d, dict) and d.get('complete') and d.get('revision'):
        staging.setdefault(d['revision'], []).append(ref(p))

builds = {}
for build in EVIDENCE.rglob('build.json'):
    digest = build.parent / 'spark.sha256'
    if digest.exists():
        recorded = read(build)
        value = digest.read_text().split()[0]
        if re.fullmatch('[0-9a-f]{64}', value) and recorded.get('source_commit'):
            builds.setdefault(value, {'source': recorded['source_commit'], 'build_receipt': ref(build), 'binary_hash_receipt': ref(digest)})

# Duplicate export folders share the owned PID/start and same executable. Keep
# the most complete raw folder and list all aliases instead of creating a run.
groups = {}
for marker in list(EVIDENCE.rglob('serve.argv')) + list(EVIDENCE.rglob('serve.command.json')):
    directory = marker.parent
    lp = first(directory, ['launch-ready.json', 'launch.json', 'process-launch.json', 'serve.identity.json'])
    launch = read(lp) if lp else {}
    key = ('owned', launch.get('pid'), str(launch.get('start_ticks', launch.get('startticks')))) if launch.get('pid') else ('unowned', directory.name)
    groups.setdefault(key, set()).add(directory)

rows = []
for aliases in groups.values():
    directory = sorted(aliases, key=lambda p: (-sum(x.is_file() for x in p.rglob('*')), len(str(p)), str(p)))[0]
    name = directory.name
    engine = 'butter' if 'butter' in str(directory) else 'vllm' if 'vllm' in name else 'atlas'
    lp = first(directory, ['launch-ready.json', 'launch.json', 'process-launch.json', 'serve.identity.json'])
    launch = read(lp) if lp else {}
    artifact = read(directory / 'artifact.json') or {}
    summary = read(directory / 'summary.json') or {}
    serve = read(directory / 'serve.command.json') or {}
    argv = launch.get('argv') or serve.get('argv')
    argv_path = first(directory, ['serve.argv', 'serve.command.json'])
    argv_origin = 'owned process capture' if launch.get('argv') else 'recorded launch command; no owned argv capture'
    if argv is None and argv_path and argv_path.name == 'serve.argv':
        argv = argv_path.read_bytes().decode().rstrip('\0').split('\0')
    argv = argv or []
    env_path = first(directory, ['process-env.json', 'serve.command.json', 'serve.env'])
    model = artifact.get('model') or {}
    snapshots = [x for x in argv if '/snapshots/' in x]
    pin = next((m.group(1) for x in snapshots if (m := re.search(r'/snapshots/([0-9a-f]{40})(?:/|$)', x))), None)
    if pin is None:
        pin = model.get('revision')
    source = None
    source_origin = None
    for arg in argv[:1]:
        m = re.search(r'/bin/([0-9a-f]{40})/', arg)
        if m:
            source, source_origin = m.group(1), 'source-named build path plus owned executable hash'
    if engine == 'butter':
        source = summary.get('source') or (read(directory / 'build-receipt.json') or {}).get('source')
        source_origin = 'explicit source build receipt'
    binary = launch.get('executable_sha256') or summary.get('binary_sha256') or (artifact.get('engine_version') or {}).get('binary_sha256')
    build_link = builds.get(binary) if engine == 'atlas' else None
    if build_link:
        if source:
            assert source == build_link['source']
        source = build_link['source']
        source_origin = 'matching captured executable SHA256 and completed build receipt'
    hardware = artifact.get('hardware') or {}
    device = first(directory, ['nvidia-smi-q.txt', 'nvidia-smi-q.stdout'])
    driver = hardware.get('driver')
    if device:
        match = re.search(r'Driver Version\s*:\s*([^\s]+)', device.read_text())
        driver = match.group(1) if match else driver
    ladder = read(directory / 'ladder.json') or {}
    harness_ref = first(directory, ['measurement-harness.sha', 'harness.sha', 'harness-source.stdout'])
    harness_git = harness_ref.read_text().strip() if harness_ref else (artifact.get('harness') or {}).get('git_sha')
    harness_git = summary.get('harness_source') or harness_git
    harness_hash = ladder.get('driver_sha256') or summary.get('harness_sha256')
    harness_hash_origin = 'actual ladder header or explicit driver receipt' if harness_hash else None
    if not harness_hash and harness_git and re.fullmatch('[0-9a-f]{40}', harness_git):
        r = subprocess.run(['git', 'show', harness_git + ':bench/ladder38/harness_w55_conc_ladder.py'], cwd=CODE, capture_output=True)
        if r.returncode == 0:
            harness_hash = hashlib.sha256(r.stdout).hexdigest()
            harness_hash_origin = 'Git blob at recorded harness revision; no ladder execution inferred'
    gates = {}
    for filename in ['coherency.json', 'coherency-pre.json', 'coherency-post.json']:
        g = read(directory / filename)
        if g is not None:
            gates[filename] = {'passed': g.get('passed'), 'path': ref(directory / filename)}
    policies = [ref(directory / n) for n in ['quality-policy-pre.json', 'quality-policy-post.json', 'coherency-exception.json'] if (directory / n).exists()]
    outcome = summary.get('fatal_error') or ('finished ladder' if ladder.get('finished_utc') else 'partial ladder' if ladder.get('rungs') else 'no completed ladder')
    row = {'session': name, 'engine': engine, 'raw_directory': ref(directory), 'duplicate_exports': [ref(p) for p in sorted(aliases) if p != directory], 'outcome': outcome, 'artifact_verdict': artifact.get('verdict'), 'artifact_failing_stage': artifact.get('failing_stage'), 'source_build_sha': source, 'source_origin': source_origin, 'source_build_records': build_link, 'engine_binary_sha256': binary if engine != 'vllm' else None, 'engine_binary_hash_origin': ('owned capture' if launch.get('executable_sha256') else 'retained build/artifact declaration') if engine != 'vllm' else None, 'process_executable_sha256': launch.get('executable_sha256'), 'vllm_immutable_implementation_identity': 'unknown' if engine == 'vllm' else 'not applicable', 'image_digest': None, 'image_note': 'Native process; no image identity substituted.', 'argv': argv, 'argv_origin': argv_origin, 'argv_record': ref(lp) if lp and launch.get('argv') else ref(argv_path) if argv_path else None, 'environment_record': ref(env_path) if env_path else None, 'owned_capture': ref(lp) if lp else None, 'served_snapshot_argument': snapshots[0] if snapshots else None, 'observed_checkpoint_pin': pin, 'matching_staging_proofs': staging.get(pin, []), 'original_artifact_model': model or None, 'gpu': hardware.get('gpu') or ('NVIDIA H100 80GB HBM3' if device else None), 'driver': driver, 'nvidia_smi_q_record': ref(device) if device else None, 'nvidia_smi_q_sha256': sha(device) if device else None, 'harness_git_sha': harness_git, 'frozen_harness_sha256': harness_hash, 'harness_hash_origin': harness_hash_origin, 'raw_gates': gates, 'separate_policies': policies, 'certification_claimed': False}
    row['explicit_gaps'] = [key for key in ['source_build_sha', 'engine_binary_sha256', 'environment_record', 'observed_checkpoint_pin', 'nvidia_smi_q_sha256', 'frozen_harness_sha256'] if row[key] is None]
    if engine == 'vllm':
        row['explicit_gaps'].append('immutable vLLM implementation identity; Python hash is not engine identity')
    if not lp:
        row['explicit_gaps'].append('No owned serve process capture: command may be preflight-only or launch refused')
    rows.append(row)

supplements = []
for path in sorted(EVIDENCE.rglob('*.section10.json')):
    d = read(path)
    supplements.append({'cell': d.get('cell', d.get('engine')), 'record': ref(path), 'sha256': sha(path), 'run_complete': d.get('run_complete'), 'rung_complete': d.get('rung_complete'), 'certification_claimed': False})

out = EVIDENCE / 'CELL-PROVENANCE-INDEX.json'
result = {'record_type': 'documentation provenance index; not a campaign artifact', 'scope': 'Every retained serving session with a raw argv/serve-command record, including refused, partial and complete attempts; supplemental rung records are indexed separately. Numerical-only examples remain in the linked acceptance manifests and do not have served checkpoints.', 'hardware_scope': 'Single H100 only; not GB10 rehearsal or multi-GPU results.', 'identity_rule': 'Null means unproven/not captured; an artifact or launcher declaration does not replace actual owned process capture. A source-named executable path is source-build evidence, distinct from an engine-declared Git field. vLLM interpreter hashes never become engine hashes.', 'capacity_rule': 'Atlas native active batch4/slots128 versus vLLM sequence cap512; these are different capacities, not evidence512 active requests. Butter failed performance attempts use server parallel16/context8192 even for offered C1; earlier short correctness windows use parallel1.', 'checkpoint_rule': 'Snapshot argument/pin and matching independent staging proof are indexed; original artifact null pins are preserved.', 'sessions': sorted(rows, key=lambda r:r['session']), 'supplemental_cells': supplements}
out.write_text(json.dumps(result, indent=2) + '\n')
lines = ['# Single-H100 cell provenance index', '', 'This is an index of raw observations, not a replacement campaign artifact. Null fields in the [machine-readable index](evidence/rental-h100-20260905/CELL-PROVENANCE-INDEX.json) mean unproven or not captured. Failed and interrupted sessions remain present. Raw coherency false and the separate reversal exception are never combined into certification.', '', 'Atlas native tables use active batch4/slots128; vLLM uses a512-sequence cap. The failed Butter performance attempts serve parallel16/context8,192, including offered C1; earlier short correctness windows use parallel1. Native process image digests stay null. Python executable hashes are process evidence only, not vLLM implementation identity. Checkpoint snapshot arguments and independent staging proofs are distinct from untouched artifact pins.', '', '| Serving session | Outcome | Engine binary SHA256 | Source build SHA | Device / argv / environment |', '|---|---|---|---|---|']
for r in result['sessions']:
    binary = r['engine_binary_sha256'] or ('Unknown vLLM implementation' if r['engine']=='vllm' else 'Unproven')
    source = r['source_build_sha'][:12] if r['source_build_sha'] else 'Unproven'
    if re.fullmatch('[0-9a-f]{64}', binary):
        binary = binary[:12]
    lines.append(f"| [{r['session']}]({r['raw_directory']}) | {r['artifact_verdict'] or r['outcome']} | {binary} | {source} | [Raw records]({r['raw_directory']}); explicit gaps in JSON |")
lines += ['', 'Original default-profile artifact NO-GO and null model revisions remain intact. A raw serve command without an owned process capture is labeled as such; it does not prove weights loaded. A frozen-harness hash resolved from a recorded Git revision identifies the source file and does not assert a ladder ran.', '', '| Supplemental cell | Complete rung / run | Evidence |', '|---|---|---|']
for r in supplements:
    lines.append(f"| {r['cell']} | {r['rung_complete']} / {r['run_complete']} | [Section10 supplement]({r['record']}) |")
lines += ['', 'Numerical-only example commands, test-binary hashes and tolerances remain in the [native FFN acceptance manifest](evidence/rental-h100-20260905/native-fp8-fixed-premeasurement/MANIFEST.json). They do not load the served checkpoint or establish full-model performance. This index must be refreshed only from finished exported sessions before publication.']
(CAMPAIGN / 'RENTAL-H100-PROVENANCE.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'sessions':len(rows),'supplemental_cells':len(supplements),'sessions_with_gaps':[{k:r[k] for k in ['session','explicit_gaps']} for r in rows if r['explicit_gaps']]},indent=2))
