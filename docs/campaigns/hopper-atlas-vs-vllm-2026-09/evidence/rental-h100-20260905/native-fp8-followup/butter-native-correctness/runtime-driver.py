#!/usr/bin/env python3
"""One explicitly assigned, bounded Butter model window. No frozen FP8 score."""
import datetime, hashlib, json, os, pathlib, signal, socket, subprocess, sys, time, urllib.error, urllib.request
ROOT = pathlib.Path('/workspace/butter-iron-rental')
if len(sys.argv)!=3 or sys.argv[1] != '--parent-assigned-window':
    raise SystemExit('Refused: an exclusive parent-assigned GPU window is required')
build=json.loads(pathlib.Path(sys.argv[2]).read_text())
assert build['complete'] and build['source']=='dfc45a185fc36ee84a8351eef21ae1dfc56d527a'
OUT = ROOT/'results'/('butter-block-fp8-http-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
OUT.mkdir()
(OUT/'runtime-driver.py').write_bytes(pathlib.Path(__file__).read_bytes())
start=time.monotonic(); deadline=start+870
binary=pathlib.Path(build['binary'])
model=pathlib.Path('/workspace/atlas-rental/hf38/hub/models--Qwen--Qwen3.8-27B-FP8/snapshots/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a')
server=None
summary={'source':build['source'],'iron_pin':'a4c897ba2e89db49df82b9d2f2691642d8f8b697','scope':'Original official Qwen3.8 FP8 checkpoint; W8A32 block-scaled correctness baseline; full raw coherency retained with only explicit word-reversal exception','requests':[],'timing_scope':'Correctness only; parent-authorized CPU tests overlap, no performance claims'}
env=os.environ.copy()
for key in list(env):
    if key.startswith(('BUTTER_IRON_', 'BUTTER_SELECTOR_', 'IRON_CUDA_')):
        env.pop(key)
env.update(CUDA_VISIBLE_DEVICES='0',CUDA_HOME='/usr/local/cuda',CUDA_PATH='/usr/local/cuda',LD_LIBRARY_PATH='/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu',BUTTER_HOME=str(ROOT/'butter-home'),QWEN35_MARLIN='0',BUTTER_IRON_SELECTORS='1')
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(name, data): (OUT/name).write_text(json.dumps(data,indent=2)+'\n')
def capture(name,args):
    p=subprocess.run(args,text=True,capture_output=True,timeout=10)
    (OUT/(name+'.stdout')).write_text(p.stdout); (OUT/(name+'.stderr')).write_text(p.stderr)
    dump(name+'.result.json',{'argv':args,'exit':p.returncode,'utc':now()})
    if p.returncode: raise RuntimeError((args,p.returncode,p.stderr))
    return p.stdout

def timeout_handler(*unused): raise TimeoutError('bounded request wall deadline')
signal.signal(signal.SIGALRM,timeout_handler)

def request(label,body):
    assert server.poll() is None, 'Butter server exited'
    remaining=deadline-time.monotonic()
    if remaining<25: raise TimeoutError('window deadline approaching')
    dump(label+'.request.json',body)
    result={'label':label,'utc':now(),'status':None,'oracle_findings':[]}
    raw=bytearray(); events=[]; first_event=None; first_content=None
    t0=time.monotonic()
    signal.setitimer(signal.ITIMER_REAL,min(120,remaining-15))
    try:
        req=urllib.request.Request('http://127.0.0.1:8890/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=30) as resp:
            result['status']=resp.status; result['headers']=dict(resp.headers)
            if body.get('stream'):
                for line in resp:
                    raw.extend(line)
                    if line.startswith(b'data: '):
                        if first_event is None:first_event=time.monotonic()-t0
                        content=line[6:].strip()
                        if content==b'[DONE]':result['done']=True;continue
                        item=json.loads(content);events.append(item)
                        for choice in item.get('choices',[]):
                            delta=choice.get('delta',{})
                            if first_content is None and (delta.get('content') or delta.get('tool_calls')):first_content=time.monotonic()-t0
            else: raw.extend(resp.read())
        if body.get('stream'):
            result['usage']=next((e['usage'] for e in reversed(events) if e.get('usage')),None)
            result['finish_reasons']=[c['finish_reason'] for e in events for c in e.get('choices',[]) if c.get('finish_reason')]
            result['content']=''.join(c.get('delta',{}).get('content','') or '' for e in events for c in e.get('choices',[]))
            result['tool_deltas']=[c['delta']['tool_calls'] for e in events for c in e.get('choices',[]) if c.get('delta',{}).get('tool_calls')]
        else:
            obj=json.loads(raw);result['response']=obj; result['usage']=obj.get('usage')
            result['finish_reasons']=[c.get('finish_reason') for c in obj.get('choices',[])]
            result['content']=''.join(c.get('message',{}).get('content','') or '' for c in obj.get('choices',[]))
        usage=result.get('usage') or {}
        if usage.get('completion_tokens')==body['max_tokens'] and result.get('finish_reasons')!=['length']:
            result['oracle_findings'].append('Reached max_tokens but finish_reason was not length (completed tool calls assessed separately)')
        if label=='coherency-arithmetic' and result.get('content','').strip()!='41':
            result['oracle_findings'].append('Expected the answer 41 with no other text')
        tools=[t for c in result.get('response',{}).get('choices',[]) for t in c.get('message',{}).get('tool_calls',[])]
        if label=='tool-none' and tools:result['oracle_findings'].append('tool_choice none still produced tool_calls')
        if label=='tool-none' and not tools and not result.get('content','').strip():result['oracle_findings'].append('tool_choice none returned no visible answer')
        if label in ('tool-auto','tool-required'):
            if not tools:result['oracle_findings'].append('Requested weather tool was not called')
            for tool in tools:
                fn=tool.get('function',{});args=json.loads(fn.get('arguments','{}'))
                if fn.get('name')!='get_weather' or args.get('city')!='Reykjavik' or args.get('days')!=3:
                    result['oracle_findings'].append('Tool name/arguments failed exact city string and days integer schema')
    except urllib.error.HTTPError as exc:
        result['status']=exc.code;raw.extend(exc.read());result['error']=str(exc)
    except Exception as exc:
        result['error']=repr(exc)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        result.update(elapsed_s=time.monotonic()-t0,first_sse_event_s=first_event,first_content_or_tool_delta_s=first_content)
        (OUT/(label+'.raw')).write_bytes(raw);dump(label+'.result.json',result)
        summary['requests'].append(result);dump('summary.json',summary)
        print(label,json.dumps({k:result.get(k) for k in ['status','elapsed_s','finish_reasons','usage','oracle_findings','error']}),flush=True)
    if result.get('error'): raise RuntimeError('Request failed; preserve first failure and stop')
    return result

try:
    import importlib.util
    oracle_path=ROOT/'oracle-source/bench/hopper_ab/coherency_gate.py'
    spec=importlib.util.spec_from_file_location('frozen_coherency',oracle_path)
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    bad_status,bad_detail=oracle.judge_known_answer("The word backwards is **rotarefiger**",'rotaregirfer')
    assert bad_status=='FAIL',(bad_status,bad_detail)
    dump('known-bad-first.json',{'input':'The word backwards is **rotarefiger**','expected':'rotaregirfer','observed':bad_status,'detail':bad_detail,'oracle_sha256':hashlib.sha256(oracle_path.read_bytes()).hexdigest(),'utc':now()})
    print('Known-bad oracle: FAIL observed before GPU launch',flush=True)
    device=capture('device',['nvidia-smi','--query-gpu=name,uuid,compute_cap,memory.total','--format=csv,noheader'])
    assert len(device.strip().splitlines())==1 and 'GPU-75655542-902a-e1a0-4829-5772a3bec9ee' in device
    assert not capture('tenants-before',['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader']).strip()
    capture('nvidia-smi-q',['nvidia-smi','-q']);capture('df-before',['df','-h','/'])
    stat=os.statvfs(ROOT);assert stat.f_bavail*stat.f_frsize>=20*1024**3;assert (stat.f_blocks-stat.f_bfree)*stat.f_frsize<=300*10**9
    for name in ['cargo','rustc','nvcc']:
        p=subprocess.run(['pgrep','-a','-x',name],text=True,capture_output=True)
        (OUT/(name+'-before.txt')).write_text(p.stdout)
        for line in p.stdout.splitlines():
            pid=int(line.split()[0])
            try:state=pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]
            except FileNotFoundError:continue
            summary.setdefault('authorized_cpu_overlap',[]).append({'pid':pid,'state':state,'command':line})
    with socket.socket() as sock: assert sock.connect_ex(('127.0.0.1',8890))!=0,'port 8890 occupied'
    assert model.is_dir() and (model/'config.json').is_file()
    summary['binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
    assert summary['binary_sha256']==build['binary_sha256']
    proof_path=pathlib.Path('/workspace/atlas-rental/results/qwen38-download-proof/staging-proof.json')
    proof=json.loads(proof_path.read_text());assert proof['complete'] and proof['snapshot']==str(model)
    assert hashlib.sha256(proof_path.read_bytes()).hexdigest()=='6074590b1089e054afc8a4c2a23ca5e8a4184e4ff2c8ccb7898fa722cf812479'
    for file in proof['files']:
        path=model/file['path'];assert path.stat().st_size==file['size'] and str(path.resolve())==file['blob']
    summary['model_staging_proof']=proof
    dump('build-receipt.json',build)
    fixtures=ROOT/'block-fp8-oracle-fixtures';manifest=json.loads((fixtures/'manifest.json').read_text())
    for file in manifest['files']:
        data=(fixtures/file['path']).read_bytes();assert len(data)==file['bytes'] and hashlib.sha256(data).hexdigest()==file['sha256']
    dump('numerical-fixture-manifest.json',manifest)
    executable=pathlib.Path(build['numerical_test_executable']);assert hashlib.sha256(executable.read_bytes()).hexdigest()==build['numerical_test_sha256']
    numerical_env=dict(env,BUTTER_BLOCK_FP8_ORACLE_DIR=str(fixtures))
    numerical_args=[str(executable),'--ignored','--nocapture','--test-threads=1']
    with (OUT/'numerical.stdout').open('w') as stdout,(OUT/'numerical.stderr').open('w') as stderr:
        numerical=subprocess.run(numerical_args,env=numerical_env,stdout=stdout,stderr=stderr,timeout=120)
    dump('numerical.result.json',{'argv':numerical_args,'exit':numerical.returncode,'utc':now(),'test_build_source':build.get('numerical_test_source',build['source']),'current_binary_source':build['source'],'unchanged_operator_dependency_paths':build.get('numerical_unchanged_paths')})
    assert numerical.returncode==0 and '3 passed; 0 failed' in (OUT/'numerical.stdout').read_text(),'independent GPU numerical test failed'
    print('GPU NUMERICAL: 3 passed; 0 failed',flush=True)
    args=[str(binary),'serve-local','--model',str(model),'--max-context','8192','--parallel','1','--host','127.0.0.1','--port','8890']
    dump('serve.command.json',{'argv':args,'environment':{k:env[k] for k in ['CUDA_VISIBLE_DEVICES','CUDA_HOME','CUDA_PATH','LD_LIBRARY_PATH','BUTTER_HOME','QWEN35_MARLIN','BUTTER_IRON_SELECTORS']},'utc':now()})
    server=subprocess.Popen(args,env=env,cwd=ROOT/'butter',stdout=(OUT/'serve.stdout').open('wb'),stderr=(OUT/'serve.stderr').open('wb'),start_new_session=True)
    pidstat=pathlib.Path(f'/proc/{server.pid}/stat').read_text().rsplit(')',1)[1].split()
    dump('serve.identity.json',{'pid':server.pid,'pgid':server.pid,'startticks':pidstat[19],'utc':now()})
    boot=time.monotonic();health=[]
    while time.monotonic()-boot<300:
        if server.poll() is not None:raise RuntimeError(f'Butter boot exited {server.returncode}')
        try:
            with urllib.request.urlopen('http://127.0.0.1:8890/health',timeout=2) as r:
                health.append({'at_s':time.monotonic()-boot,'status':r.status,'body':r.read().decode()})
                if r.status==200:break
        except Exception as exc:health.append({'at_s':time.monotonic()-boot,'error':str(exc)})
        dump('boot.json',health)
        time.sleep(1)
    else:raise TimeoutError('Butter did not boot within 300 seconds')
    summary['time_to_ready_s']=time.monotonic()-boot;dump('boot.json',health)
    with urllib.request.urlopen('http://127.0.0.1:8890/v1/models',timeout=5) as r:(OUT/'models.json').write_bytes(r.read())
    print('Butter ready',summary['time_to_ready_s'],flush=True)
    memory=capture('loaded-vram',['nvidia-smi','--query-gpu=uuid,memory.total,memory.used,memory.free','--format=csv,noheader'])
    print('LOADED VRAM',memory.strip(),flush=True)
    first=request('readiness-one-token',{'model':str(model),'messages':[{'role':'user','content':'Hello'}],'temperature':0.0,'seed':42,'presence_penalty':0.0,'frequency_penalty':0.0,'max_tokens':1,'chat_template_kwargs':{'enable_thinking':False}})
    print('FIRST RESPONSE',repr(first.get('content')),'finish',first.get('finish_reasons'),flush=True)
    assert first.get('content','').strip(),'readiness completion was empty'

    gate_args=['python3',str(oracle_path),'--url','http://127.0.0.1:8890','--model',str(model),'--think','off','--timeout','90','--out',str(OUT/'coherency.json')]
    with (OUT/'coherency.stdout').open('w') as stdout,(OUT/'coherency.stderr').open('w') as stderr:
        gate=subprocess.run(gate_args,stdout=stdout,stderr=stderr,timeout=min(450,deadline-time.monotonic()-30))
    dump('coherency.command.json',{'argv':gate_args,'exit':gate.returncode,'utc':now()})
    full=json.loads((OUT/'coherency.json').read_text())
    known=[]
    for exchange in full['http_exchanges']:
        if exchange['check']!='known_answer_ok':continue
        body=json.loads(exchange['request_json']);prompt=body['messages'][-1]['content']
        expected=next(expect for p,expect in oracle.KNOWN_ANSWER_CASES if p==prompt)
        response=json.loads(exchange['response_body']);content=response['choices'][0]['message'].get('content') or ''
        verdict,detail=oracle.judge_known_answer(content,expected)
        known.append({'expected':expected,'verdict':verdict,'detail':detail,'content':content,'finish_reason':response['choices'][0]['finish_reason'],'degeneration_signals':oracle.degeneration_signals(content)})
    others=all(full.get(key) is True for key in ['determinism_ok','toolcall_ok','think_leak_ok'])
    exact_nonreversal=len(known)==3 and {c['expected'] for c in known}=={'391','Tokyo','rotaregirfer'} and all(c['verdict']=='OK' for c in known if c['expected']!='rotaregirfer')
    reversal=next((c for c in known if c['expected']=='rotaregirfer'),None)
    allowed=bool(others and exact_nonreversal and reversal and not reversal['degeneration_signals'] and reversal['content'].strip())
    exception={'authority':'Explicit user word-reversal exception communicated by parent; all other coherency remains required','raw_gate_passed':full['passed'],'raw_gate_exit':gate.returncode,'other_coherency_passed':others,'known_answers':known,'authorized_to_continue':allowed,'scope':'Only the refrigerator word-reversal answer is excepted; raw gate is unchanged'}
    dump('coherency-exception.json',exception);summary['coherency']=exception
    print('FULL COHERENCY',json.dumps(full['details']),'exception-authorized',allowed,flush=True)
    assert allowed,'non-excepted coherency failed; stop without a ladder'
    probe=pathlib.Path('/workspace/atlas-rental/src/atlas/bench/campaign/stream_probe.py')
    summary['stream_probe_sha256']=hashlib.sha256(probe.read_bytes()).hexdigest()
    for label,check in [('plain','determinism_ok'),('tool','toolcall_ok')]:
        exchange=next(e for e in full['http_exchanges'] if e['check']==check)
        body=json.loads(exchange['request_json']);body.update(stream=True,stream_options={'include_usage':True})
        dump(label+'-stream.request.json',body)
        argv=['python3',str(probe),'--url','http://127.0.0.1:8890/v1/chat/completions','--request-json',str(OUT/(label+'-stream.request.json')),'--out',str(OUT/(label+'-stream')),'--timeout-s','90']
        result=subprocess.run(argv,capture_output=True,text=True,timeout=min(100,deadline-time.monotonic()-15))
        (OUT/(label+'-stream.stdout')).write_text(result.stdout);(OUT/(label+'-stream.stderr')).write_text(result.stderr)
        dump(label+'-stream.command.json',{'argv':argv,'exit':result.returncode,'utc':now()})
        print('STREAM',label,'exit',result.returncode,flush=True)
        assert result.returncode==0,label+' stream structure failed'
    summary['completed']=True
except Exception as exc:
    summary['fatal_error']=repr(exc);print('STOP',repr(exc),flush=True)
finally:
    signal.setitimer(signal.ITIMER_REAL,0)
    if server is not None and server.poll() is None:
        os.killpg(server.pid,signal.SIGTERM)
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(server.pid,signal.SIGKILL);server.wait(timeout=5)
    summary['server_exit']=None if server is None else server.poll()
    p=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True,capture_output=True,timeout=10)
    (OUT/'tenants-after.csv').write_text(p.stdout);summary['gpu_released']=p.returncode==0 and not p.stdout.strip()
    subprocess.run(['df','-h','/'],stdout=(OUT/'df-after.txt').open('w'),timeout=10)
    summary.update(finished_utc=now(),elapsed_s=time.monotonic()-start);dump('summary.json',summary)
    print('GPU RELEASE',summary['gpu_released'],summary['finished_utc'],'Evidence',OUT,flush=True)
