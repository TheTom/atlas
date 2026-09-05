import concurrent.futures, datetime, hashlib, itertools, json, os, pathlib, shlex, subprocess, time
ROOT=pathlib.Path('/tmp/atlas-rental-readiness-20260905')
OUT=ROOT/'docs/campaigns/hopper-atlas-vs-vllm-2026-09/evidence/dryrun-matrix'
ENV=os.environ.copy()
for k in ['VLLM_IMAGE_DIGEST','VLLM_IMAGE','VLLM_RECIPES','ATLAS_PORT','VLLM_PORT','SPARK_BIN','IMAGE','HF_CACHE','ATLAS_NODE_RUN_DIR','DOCKER']:
 ENV.pop(k,None)
ENV['PYTHONDONTWRITEBYTECODE']='1'
ENV['RUST_LOG']='warn'
ENV['HF_CACHE']='/tmp/atlas-step-d-dryrun-hf-cache-not-created'

def run(argv):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat(); tick=time.monotonic()
 p=subprocess.run(argv,cwd=ROOT,env=ENV,text=True,capture_output=True,timeout=60)
 return {'argv':argv,'command':shlex.join(argv),'started_utc':start,'wall_seconds':round(time.monotonic()-tick,6),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def command(engine,model,sku,workload='lat',concurrency=1,spec='off',think='off',cell_id='negative'):
 return ['bash','bench/campaign/run_cell.sh','--engine',engine,'--model',model,'--sku',sku,'--workload',workload,'--concurrency',str(concurrency),'--spec',spec,'--think',think,'--out',f'/tmp/atlas-step-d-dryrun-not-created/{cell_id}','--dry-run']

def log(path,meta,runs):
 with path.open('w') as f:
  f.write(json.dumps(meta,indent=2)+'\n')
  for name,r in runs.items():
   f.write(f'\n=== {name} ===\n$ {r["command"]}\nstarted_utc: {r["started_utc"]}\nexit_code: {r["exit_code"]}\nwall_seconds: {r["wall_seconds"]}\n--- stdout ---\n{r["stdout"]}\n--- stderr ---\n{r["stderr"]}')

negatives=[]
for name,argv,expected in [
 ('missing-recipe-atlas',command('atlas','d2-known-missing-model','h100'),3),
 ('missing-recipe-vllm',command('vllm','d2-known-missing-model','h100'),3),
 ('invalid-spec',command('vllm','nemotron-3-nano-fp8','h100',spec='invalid'),2),
 ('nano-spec-direct',['bash','bench/campaign/vllm_control.sh','nemotron-3-nano-fp8','h100','--spec','on','--dry-run'],4),
 ('nano-spec-through-driver',command('vllm','nemotron-3-nano-fp8','h100',spec='on'),4),
 ('nano-spec-atlas',command('atlas','nemotron-3-nano-fp8','h100',spec='on'),4),
]:
 r=run(argv); meta={'id':name,'oracle_expected_exit':expected,'observed_exit':r['exit_code'],'oracle_passed':r['exit_code']==expected}; negatives.append({**meta,'run':r})
 log(OUT/f'known-bad-{name}.log',meta,{'known-bad':r})
(OUT/'known-bad.json').write_text(json.dumps(negatives,indent=2)+'\n')
print('known-bad',[(x['id'],x['observed_exit'],x['oracle_passed']) for x in negatives],flush=True)

# Every named model/SKU in the PRD, plus a separately labelled recipe-only envelope.
rows=[]
def add(model,skus,source,role,atlas_expectation='runnable',key_status='canonical'):
 for sku in skus.split(): rows.append(dict(model=model,sku=sku,prd_source=source,role=role,atlas_expectation=atlas_expectation,key_status=key_status))
add('nemotron-3-nano-fp8','h100 h200 b200','3.1 L61; 6.1 L160; 7 L189','plumbing')
add('nemotron-3-super-fp8','h100 h200 b200','3.1 L62; 5 L127; 6.1 L161; 7 L187-188','P0')
add('qwen3.6-35b-a3b-fp8','h100 h200 b200','3.1 L63; 6.1 L162; 7 L190; 12','P0-compile-status-conflict')
add('qwen3-next-80b-fp8','h100 h200 b200','3.1 L64; 6.1 L163; 7 L191','P1')
add('deepseek-v4-flash','h200 b200','3.1 L65; 6.1 L164; 7 L195','P1')
add('glm-5.3-flash','h200','3.1 L66; 4 L101; 5 L127; 16 L312','P1-vllm-reference','ATLAS_UNSUPPORTED')
add('glm-5.3','h200','3.2 L77; 4 L101; 7 L192; 16 L312','Phase-D-vllm-reference','ATLAS_UNSUPPORTED')
add('glm-4.5-air-fp8','h100 h200','3.1 L68; 4 L101; 7 L193; 16 L312','canary-vllm-reference','ATLAS_UNSUPPORTED')
add('kimi-k3','b200','3.1 L67; 3.2 L76; 7 L194; 16 L311','Phase-D-vllm-reference','ATLAS_UNSUPPORTED')
add('minimax-m2.7','h200','3.2 L73; 5 L125','Phase-D-conditional','conditional','unallocated-proposal')
add('qwen3.8-flash-next-fp8','h100 h200 b200','3.2 L74; 5 L127','Phase-D-vllm-reference','ATLAS_UNSUPPORTED')
add('minimax-m3','h200 b200','3.2 L75','Phase-D-vllm-reference','ATLAS_UNSUPPORTED')
add('qwen3.8-27b-fp8','h200','16 L309','first-paid-cell','runnable','unallocated-proposal')
# These recipe JSON SKUs have no corresponding PRD booking; they are completeness probes only.
add('glm-5.3-flash','h100 b200','recipe JSON only; PRD 3.1 names H200','recipe-only-probe','ATLAS_UNSUPPORTED')
add('glm-5.3','h100 b200','recipe JSON only; PRD 3.2 names H200','recipe-only-probe','ATLAS_UNSUPPORTED')
add('deepseek-v4-flash','h100','3.1 L65; 8 L212 explicit no-H100-recipe','negative-SKU-probe','unsupported-SKU')
add('minimax-m3','h100','3.2 L75; 8 L212 explicit no-H100-recipe vs current JSON profile','negative-SKU-probe','ATLAS_UNSUPPORTED')
# No canonical key or quantized artifact is allocated for the P0 NVFP4 overflow rows.
add('nemotron-3-super-nvfp4','b200','3.1 L69; 5 L125; 8 L214','NVFP4-unallocated-probe','ATLAS_UNSUPPORTED','unallocated-proposal')
add('qwen3.6-35b-a3b-nvfp4','b200','3.1 L63,L69; 5 L125; 8 L214','NVFP4-unallocated-probe','ATLAS_UNSUPPORTED','unallocated-proposal')


def policy(row,spec,think):
 model=row['model']; reasons=[]; category='scoring-envelope'
 if row['role'].endswith('probe'): category='policy-probe'; reasons.append(row['role'])
 if row['key_status']!='canonical': reasons.append('canonical model key not allocated by recipe JSON')
 if model=='nemotron-3-nano-fp8' and spec=='on': category='policy-probe'; reasons.append('Nano has no MTP: spec off required (6.1 L160)')
 if model=='nemotron-3-super-fp8' and spec=='on': category='conditional-alternative'; reasons.append('spec on conflicts with Atlas support; default off (6.1 L161 vs 7 L187)')
 if model=='qwen3-next-80b-fp8' and think=='on': category='policy-probe'; reasons.append('Instruct supports only non-thinking (6.1 L163)')
 if model=='deepseek-v4-flash' and spec=='on': category='policy-probe'; reasons.append('scored pair requires spec off (6.1 L164; 7 L195)')
 if model in ('glm-5.3','glm-5.3-flash') and think=='off': category='policy-probe'; reasons.append('always-thinking; think off blocked pending frozen policy (4 L101)')
 if model=='glm-4.5-air-fp8' and spec=='on': category='policy-probe'; reasons.append('Air spec off required (7 L193)')
 if model=='kimi-k3':
  if think=='off': category='policy-probe'; reasons.append('Kimi scored row requires think on (3.2 L76)')
  if spec=='on': category='conditional-alternative'; reasons.append('DSpark second row only; recipe excludes TP8+PP2 (3.2 L76;7 L194)')
 if model=='minimax-m2.7' and spec=='on': category='policy-probe'; reasons.append('no speculative policy frozen for conditional M2.7 row')
 return category,reasons

cells=[]
for row in rows:
 for engine,workload,concurrency,spec,think in itertools.product(['atlas','vllm'],['lat','agent'],[1,16],['off','on'],['off','on']):
  cid=f'{engine}.{row["model"]}.{row["sku"]}.{workload}.c{concurrency}.spec{spec}.think{think}'
  category,notes=policy(row,spec,think)
  cells.append({**row,'id':cid,'engine':engine,'workload':workload,'concurrency':concurrency,'spec':spec,'think':think,'category':category,'policy_notes':notes})
(OUT/'enumeration.json').write_text(json.dumps({'source_code_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_docs_sha':'0b21f2a','rows':rows,'cells':cells},indent=2)+'\n')


def cell_run(c):
 r=run(command(c['engine'],c['model'],c['sku'],c['workload'],c['concurrency'],c['spec'],c['think'],c['id']))
 runs={'run_cell':r}
 if c['engine']=='vllm': runs['vllm_control']=run(['bash','bench/campaign/vllm_control.sh',c['model'],c['sku'],'--spec',c['spec'],'--dry-run'])
 log(OUT/(c['id']+'.log'),c,runs)
 return {**c,'runs':runs}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for result in pool.map(cell_run,cells):
  results.append(result)
  if len(results)%80==0: print('rendered',len(results),'/',len(cells),flush=True)
(OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print('complete',len(results),flush=True)
