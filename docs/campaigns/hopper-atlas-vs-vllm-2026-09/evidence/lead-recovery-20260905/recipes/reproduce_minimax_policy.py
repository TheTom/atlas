"""Replay the retained template oracle after reboot; no GPU or network access."""
from pathlib import Path
import gzip,hashlib,json,subprocess
from jinja2 import Environment
OUT=Path(__file__).parent
REPO=OUT.parents[2]/'atlas-campaign-code'
# This path is derived explicitly below because OUT also sits under an evidence folder.
REPO=Path('/Users/tom/Documents/New project/atlas-campaign-code')
DOCS=REPO.parent/'atlas-campaign-docs/docs/campaigns/hopper-atlas-vs-vllm-2026-09'
log=(OUT/'cross-review-output-0510.txt').read_text()
line=next(l for l in log.splitlines() if '/recipes/nvidia--MiniMax-M3-NVFP4.json:42:' in l)
fragment=line.split('.json:42:',1)[1].strip().rstrip(',')
template=json.loads('{'+fragment+'}')['chat_template_jinja']
(OUT/'minimax-m3-template.jinja').write_text(template)
assert hashlib.sha256(template.encode()).hexdigest()=='11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64'
base={'messages':[{'role':'user','content':'What is 7 + 11?'}],'add_generation_prompt':True}
results=[]
bf16=json.loads(gzip.open(DOCS/'vllm-control/weight-evidence/MiniMaxAI--MiniMax-M3.response.json.gz','rt').read())
for repo,revision,t in [('nvidia/MiniMax-M3-NVFP4','901464083161bf8612a29ff7ad29914cd4ab4a85',template),('MiniMaxAI/MiniMax-M3',bf16['sha'],bf16['config']['chat_template_jinja'])]:
 j=Environment().from_string(t)
 r={name:j.render(**base,**kwargs) for name,kwargs in [('on',{'enable_thinking':True}),('off',{'enable_thinking':False}),('enabled',{'thinking_mode':'enabled'}),('disabled',{'thinking_mode':'disabled'}),('adaptive',{'thinking_mode':'adaptive'})]}
 results.append({'repo_id':repo,'revision':revision,'template_sha256':hashlib.sha256(t.encode()).hexdigest(),'rendered_prompts':r,'checks':{'on_equals_off':r['on']==r['off'],'on_equals_enabled':r['on']==r['enabled'],'off_equals_disabled':r['off']==r['disabled'],'on_equals_adaptive':r['on']==r['adaptive'],'off_equals_adaptive':r['off']==r['adaptive']}})
record={'oracle':'on/off must match explicit enabled/disabled, and on and off must not silently render the same adaptive prompt','templates':results,'driver':[]}
for sku in ['h100','h200','b200']:
 for think in ['on','off']:
  cmd=['bash','bench/campaign/run_cell.sh','--engine','vllm','--model','minimax-m3','--sku',sku,'--workload','lat','--concurrency','1','--spec','off','--think',think,'--out','/unused-minimax-policy-recovery','--dry-run']
  r=subprocess.run(cmd,cwd=REPO,text=True,capture_output=True)
  record['driver'].append({'sku':sku,'think':think,'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
(OUT/'minimax-thinking-recovery.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'templates':[{k:v for k,v in t.items() if k!='rendered_prompts'} for t in results],'driver':[{k:v for k,v in t.items() if k not in ['stdout','stderr','command']} for t in record['driver']]},indent=2))
