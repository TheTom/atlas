import collections, datetime, hashlib, json, pathlib, shlex, subprocess
ROOT=pathlib.Path('/tmp/atlas-rental-readiness-20260905')
BASE=ROOT/'docs/campaigns/hopper-atlas-vs-vllm-2026-09'
OUT=BASE/'evidence/dryrun-matrix'
A=json.loads((ROOT/'bench/campaign/atlas_recipes.json').read_text())
V=json.loads((ROOT/'bench/campaign/vllm_recipes.json').read_text())
W=json.loads((ROOT/'bench/hopper_ab/workloads.json').read_text())
AM={(r['model_key'],r['sku']):r for r in A['entries']}; VM={(r['model_key'],r['sku']):r for r in V['entries']}

def val(tokens,flag):
 return tokens[tokens.index(flag)+1] if flag in tokens else None

def extract_vllm(text):
 ans=[]
 for line in text.splitlines():
  line=line.removeprefix('  | ')
  if line.startswith('docker run '):
   a=shlex.split(line); p=a.index('--entrypoint'); ans.append([a[p+1]]+a[p+3:])
 return ans

def extract_atlas(text):
 return [shlex.split(l.split('rank0_command: ',1)[1]) for l in text.splitlines() if 'rank0_command: ' in l]

def expected_vllm(entry,spec):
 expected=[]
 for source in [entry['args']]+(entry.get('worker_args') or []):
  argv=list(source)
  flags=[x for x in entry.get('spec_args') or [] if x.startswith('--')]
  for flag in flags:
   while flag in argv:
    start=argv.index(flag); end=start+1
    while end<len(argv) and not argv[end].startswith('--'): end+=1
    del argv[start:end]
  if spec=='on': argv+=entry['spec_args'] or []
  expected.append(argv)
 return expected

def vllm_audit(observed,entry,spec):
 expected=expected_vllm(entry,spec)
 assert observed==expected, f'vLLM argv differs from recipe: expected {expected!r}; observed {observed!r}'

def atlas_audit(observed,entry,spec,think):
 assert len(observed)==1, 'missing rank0 command'
 argv=observed[0]
 assert argv[argv.index('serve')+1]==entry['hf_id'], 'checkpoint differs'
 for flag,expected in [('--world-size',entry['ngpus']),('--ep-size',entry['ep_size']),('--tp-size',entry['tp_size'])]:
  assert val(argv,flag)==str(expected), f'{flag} differs'
 if entry['quant']=='fp8': assert val(argv,'--fp8-kv-calibration-tokens')=='256', 'FP8 checkpoint missing calibration 256'
 assert ('--disable-thinking' in argv)==(think=='off'), 'thinking serve flag differs'
 assert ('--speculative' in argv)==(spec=='on'), 'speculation serve flag differs'
 if spec=='on': assert val(argv,'--num-drafts')==val(entry.get('spec_args') or A['spec_args'],'--num-drafts'), 'draft count differs'

def ladder_audit(text,row):
 lines=[l for l in text.splitlines() if l.startswith('$ python3 ') and shlex.split(l[2:])[1].endswith('/harness_w55_conc_ladder.py')]
 assert len(lines)==1, 'missing ladder render'
 argv=shlex.split(lines[0][2:]); shape=W['workloads'][row['workload']]
 for flag,value in [('--isl',shape['isl']),('--osl',shape['osl']),('--concs',row['concurrency']),('--reps',W['reps']),('--warmup',W['warmup'])]:
  assert val(argv,flag)==str(value), f'ladder {flag} differs'
 assert ('--enable-thinking' in argv)==(row['think']=='on'), 'ladder think policy differs'

# Execute these subprocesses before touching the observed green matrix.
if __name__=='__main__' and len(__import__('sys').argv)>1:
 mode=__import__('sys').argv[1]
 e=VM[('qwen3.6-35b-a3b-fp8','h100')]
 if mode=='known-bad-vllm':
  observed=expected_vllm(e,'on'); observed[0][observed[0].index('--tensor-parallel-size')+1]='99'; vllm_audit(observed,e,'on')
 if mode=='known-bad-atlas':
  e=AM[('nemotron-3-nano-fp8','h100')]; observed=[['spark','serve',e['hf_id'],'--world-size','1','--ep-size','1','--tp-size','1','--disable-thinking']]; atlas_audit(observed,e,'off','off')
 if mode=='known-bad-ladder':
  ladder_audit('$ python3 /tmp/harness_w55_conc_ladder.py --isl 999 --osl 256 --concs 1 --reps 3 --warmup 1',{'workload':'lat','concurrency':1,'think':'off'})
 raise SystemExit(0)

red=[]
for mode in ['known-bad-vllm','known-bad-atlas','known-bad-ladder']:
 p=subprocess.run(['python3',__file__,mode],text=True,capture_output=True)
 record={'id':mode,'command':shlex.join(['python3',__file__,mode]),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'passed':p.returncode!=0}; red.append(record)
 (OUT/(mode+'-auditor.log')).write_text('$ '+record['command']+'\nexit_code: '+str(p.returncode)+'\n--- stdout ---\n'+p.stdout+'\n--- stderr ---\n'+p.stderr)
 assert p.returncode!=0, 'auditor did not reject known-bad input'
(OUT/'auditor-red-first.json').write_text(json.dumps(red,indent=2)+'\n')
results=json.loads((OUT/'results.json').read_text()); byid={r['id']:r for r in results}; checks=collections.Counter()
for r in results:
 key=(r['model'],r['sku']); entry=AM.get(key) if r['engine']=='atlas' else VM.get(key)
 run=r['runs']['run_cell']; ctrl=r['runs'].get('vllm_control'); issues=[]; flags=[]
 if entry is None:
  expected=3
 elif r['spec']=='on' and not (entry['spec_supported'] if r['engine']=='atlas' else entry['spec_args']): expected=4
 else: expected=0
 r['expected_render_exit']=expected
 if run['exit_code']!=expected: issues.append('driver-exit-mismatch')
 if ctrl and ctrl['exit_code']!=expected: issues.append('control-exit-mismatch')
 if expected==3:
  refusal=f'no rendered profile for {r["model"]} on {r["sku"]}'
  if run['stdout'].strip()!=refusal or run['stderr']!='': issues.append('refusal-message-mismatch')
 if expected==0:
  try:
   if r['engine']=='vllm':
    for name,rr in r['runs'].items(): vllm_audit(extract_vllm(rr['stdout']),entry,r['spec']); checks['vllm_complete_argv']+=1
   else:
    atlas_audit(extract_atlas(run['stdout']),entry,r['spec'],r['think']); checks['atlas_rank0_recipe']+=1
    if entry['quant']=='fp8': checks['atlas_fp8_calibration_256']+=1
   ladder_audit(run['stdout'],r); checks['ladder_frozen_shape_and_think']+=1
  except AssertionError as exc: issues.append(str(exc))
  if r['engine']=='vllm' and key in AM and r['spec']=='on' and AM[key]['spec_supported']:
   count=val(AM[key].get('spec_args') or A['spec_args'],'--num-drafts')
   config=json.loads(val(extract_vllm(run['stdout'])[0],'--speculative-config'))
   if int(count)!=config['num_speculative_tokens']: issues.append('paired-draft-count-mismatch')
   checks['paired_spec_depth']+=1
 if r['category']=='policy-probe' and expected==0: flags.append('policy-probe-accepted')
 if r['think']=='on' and expected==0: flags.append('coherency-think-off')
 if r['engine']=='vllm' and r['model'] in ('glm-5.3','glm-5.3-flash') and r['think']=='off' and expected==0: issues.append('blocked-GLM-think-off-accepted')
 if r['engine']=='atlas' and r['model']=='qwen3-next-80b-fp8' and r['think']=='on' and expected==0: issues.append('Instruct-think-on-accepted')
 if r['engine']=='vllm' and r['model']=='kimi-k3' and expected==0:
  flags.append('Kimi-context-1048576-vs-49152')
  flags.append('manual-multinode-required')
  if r['spec']=='on': flags.append('Kimi-TP8PP2-DSpark-unverified')
 if r['engine']=='vllm' and r['model']=='minimax-m3' and r['sku']=='b200': flags.append('M3-BF16-vs-PRD-NVFP4')
 if r['engine']=='vllm' and r['model']=='nemotron-3-nano-fp8' and expected==0: flags.append('Nano-parser-not-provisioned')
 if r['engine']=='atlas' and r['model']=='qwen3-next-80b-fp8' and r['sku']=='h100': flags.append('requested-H100-topology-unallocated')
 if r['engine']=='vllm' and key in AM and entry and entry['gpus']!=AM[key]['ngpus']: flags.append('paired-GPU-count-differs')
 if expected==3 and r['atlas_expectation']!='ATLAS_UNSUPPORTED' and r['role'] not in ('negative-SKU-probe','recipe-only-probe','NVFP4-unallocated-probe'): flags.append('named-cell-missing-recipe')
 r['audit']={'issues':issues,'flags':flags}
 r['verdict']='FAIL' if issues else ('BLOCKED' if flags or expected else 'RENDER_PASS')
 if not issues and expected==3 and r['atlas_expectation']=='ATLAS_UNSUPPORTED' and r['engine']=='atlas': r['verdict']='EXPECTED_UNSUPPORTED'
 if not issues and expected==4: r['verdict']='EXPECTED_SPEC_REFUSAL'
summary={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cells':len(results),'commands':sum(len(r['runs']) for r in results),'checks':dict(checks),'verdicts':dict(collections.Counter(r['verdict'] for r in results)),'issues':dict(collections.Counter(i for r in results for i in r['audit']['issues'])),'flags':dict(collections.Counter(i for r in results for i in r['audit']['flags'])),'categories':dict(collections.Counter(r['category'] for r in results)),'known_bad_auditor':len(red),'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['bench/campaign/run_cell.sh','bench/campaign/vllm_control.sh','bench/campaign/atlas_recipes.json','bench/campaign/vllm_recipes.json','bench/hopper_ab/workloads.json','bench/hopper_ab/coherency_gate.py','bench/ladder38/harness_w55_conc_ladder.py']}}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
# Raw stdout/stderr lives in the per-cell .log; keep the machine index compact.
for r in results:
 for rr in r['runs'].values():
  for stream in ['stdout','stderr']:
   rr[stream+'_sha256']=hashlib.sha256(rr[stream].encode()).hexdigest()
   if stream=='stderr': rr['stderr_literal']=rr[stream]
   del rr[stream]
(OUT/'index.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(summary,indent=2))
