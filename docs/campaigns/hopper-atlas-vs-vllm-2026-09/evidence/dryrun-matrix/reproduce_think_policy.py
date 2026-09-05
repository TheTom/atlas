"""CPU-only reproduction: a think-on cell's coherency gate still asks for think-off."""
import importlib.util,json,os,pathlib,shlex,subprocess,sys,tempfile
sys.dont_write_bytecode=True
ROOT=pathlib.Path('/tmp/atlas-rental-readiness-20260905')
OUT=ROOT/'docs/campaigns/hopper-atlas-vs-vllm-2026-09/evidence/dryrun-matrix'
SRC=ROOT/'bench/hopper_ab/coherency_gate.py'
spec=importlib.util.spec_from_file_location('gate_observation',SRC); gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
records=[]
with tempfile.TemporaryDirectory(prefix='atlas-d2-think-policy-') as td:
 stub=pathlib.Path(td)/'stub.py'
 # Reuse the gate's own HTTP fixture; only this temporary fixture is altered.
 # It has a deliberately broken think-on path and the normal clean think-off path.
 stub.write_text(gate.STUB.replace('if MODE == "empty":', 'if MODE == "empty" or req.get("chat_template_kwargs", {}).get("enable_thinking") is True:'))
 for mode in ['wrong-answer','clean']:
  port=gate._free_port(); proc=subprocess.Popen(['python3',str(stub),str(port),mode,str(gate.FIXTURES)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   gate._await_bind(port)
   argv=['python3',str(SRC),'--url',f'http://127.0.0.1:{port}','--model','D2-POLICY-SENSITIVE-STUB','--timeout','5','--out',str(OUT/f'think-policy-{mode}.json')]
   run=subprocess.run(argv,cwd=ROOT,env=env,text=True,capture_output=True)
   result=json.loads((OUT/f'think-policy-{mode}.json').read_text())
   policies=[json.loads(e['request_json'])['chat_template_kwargs']['enable_thinking'] for e in result['http_exchanges']]
   record={'mode':mode,'command':shlex.join(argv),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'passed':result['passed'],'observed_request_thinking':policies}
   if mode=='clean':
    payload=gate.body('D2-POLICY-SENSITIVE-STUB',gate.DETERMINISM_PROMPT,chat_template_kwargs={'enable_thinking':True})
    exchanges=[]; response=gate.post(f'http://127.0.0.1:{port}',payload,5,exchanges)
    record['think_on_direct_request']=exchanges
    record['think_on_direct_response']=response
    record['think_on_broken']=gate.content_of(response)==''
   records.append(record)
  finally:
   proc.terminate();proc.communicate(timeout=10)
assert records[0]['exit_code']==1 and records[0]['passed'] is False
assert records[1]['exit_code']==0 and records[1]['passed'] is True
assert records[1]['observed_request_thinking']==[False]*7 and records[1]['think_on_broken']
(OUT/'think-policy-observation.json').write_text(json.dumps(records,indent=2)+'\n')
for r in records:
 print('$',r['command']);print('exit:',r['exit_code']);print('stdout:',r['stdout']);print('stderr:',repr(r['stderr']));print('request enable_thinking:',r['observed_request_thinking'])
print('OBSERVED: known-wrong answers fail, then the gate passes seven think-off requests although the same stub returns empty content for think-on.')
