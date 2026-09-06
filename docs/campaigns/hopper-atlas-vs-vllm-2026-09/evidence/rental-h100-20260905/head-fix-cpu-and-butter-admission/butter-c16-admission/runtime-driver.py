#!/usr/bin/env python3
"""Owned, bounded native FP8 latency window; the frozen client stays unchanged."""
import argparse
import concurrent.futures
import datetime
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import signal
import socket
import subprocess
import threading
import time
import urllib.request

ROOT = Path('/workspace/butter-iron-rental')
ATLAS = Path('/workspace/atlas-rental')
SOURCE = ATLAS / 'src/atlas'
MODEL = ATLAS / 'hf38/hub/models--Qwen--Qwen3.8-27B-FP8/snapshots/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a'
HEAD = 'dfc45a185fc36ee84a8351eef21ae1dfc56d527a'
BINARY_SHA = 'da3e60000d55a2aaca67c04b09cd0400553444e45653d911ae828f06103cf606'
HARNESS_SHA = '7a78f205e168a6ded92a6de270c46c59ea6e4dd18616c3927b98433128343fbb'
GPU_UUID = 'GPU-75655542-902a-e1a0-4829-5772a3bec9ee'

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def require_capacity(free_mib, before_sessions):
    threshold=29*1024 if before_sessions else 8*1024
    if free_mib < threshold: raise ValueError(f'capacity refused: free {free_mib}MiB < {threshold}MiB')

def require_tokens(prompt_tokens, completion_tokens, expected_output):
    if prompt_tokens !=1193 or completion_tokens !=expected_output:
        raise ValueError(f'token parity refused: prompt={prompt_tokens}, output={completion_tokens}, expected1193/{expected_output}')

def c16_budget_stop(elapsed_s, first_rep_wall_s=None, completed_reps=0):
    """A rental budget policy, not an estimate of an unobserved warmup time."""
    if elapsed_s >= 300:
        return 'C16 phase reached its300s hard budget'
    if completed_reps == 0 and elapsed_s >= 150:
        return 'No completed measured C16 burst after150s of warmup plus first rep; conservative budget stop'
    if first_rep_wall_s is not None and completed_reps < 3:
        projected = elapsed_s + (3-completed_reps)*first_rep_wall_s
        if projected > 300:
            return f'Observed C16 burst projects phase to{projected:.1f}s >300s budget'
    return None

def selftest():
    red=0
    for fn,args in [(require_capacity,(29*1024-1,True)),(require_capacity,(8*1024-1,False)),
                    (require_tokens,(1192,256,256)),(require_tokens,(1193,255,256))]:
        try: fn(*args)
        except ValueError: red+=1
        else: raise AssertionError('known-bad admission accepted')
    require_capacity(29*1024,True);require_capacity(8*1024,False);require_tokens(1193,256,256)
    assert c16_budget_stop(151) is not None
    assert c16_budget_stop(80,76,1) is None
    assert c16_budget_stop(160,80,1) is not None
    assert c16_budget_stop(299,20,2) is not None
    assert c16_budget_stop(300,1,3) is not None
    assert c16_budget_stop(149) is None
    assert c16_budget_stop(80,20,3) is None
    return {'known_bad_refusals':red,'valid_boundary_acceptances':3,'c16_budget_cases':7}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--selftest',action='store_true')
    ap.add_argument('--parent-assigned-window',action='store_true')
    ap.add_argument('--build-receipt')
    ap.add_argument('--work-cap-s',type=int,default=870)
    args=ap.parse_args()
    red=selftest()
    if args.selftest: print(json.dumps(red));return
    if not args.parent_assigned_window or not args.build_receipt:ap.error('exclusive parent GPU lease and verified build receipt required')
    if not 120<=args.work_cap_s<=1170:ap.error('work cap must be120..1170s; cleanup needs30s outside it')
    started=time.monotonic();deadline=started+args.work_cap_s
    out=ROOT/'results'/('butter-block-fp8-lat-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    out.mkdir();(out/'runtime-driver.py').write_bytes(Path(__file__).read_bytes())
    summary={'source':HEAD,'started_utc':utc(),'profile':{'parallel':16,'context':8192,'weight_compute':'originalE4M3FN/BF16-block128 multipliers; W8A32 CUDA-core','kv':'rawF32','spec':'off','think':'off'},'certification_claimed':False,'admission_selftest':red}
    server=None;children=[];monitor=None;monitor_stop=threading.Event();memory_fault=threading.Event()
    env=dict(os.environ,W55_PROMPT_MODE='essay',CUDA_VISIBLE_DEVICES='0',CUDA_HOME='/usr/local/cuda',CUDA_PATH='/usr/local/cuda',LD_LIBRARY_PATH='/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu',BUTTER_HOME=str(ROOT/'butter-home'),QWEN35_MARLIN='0',BUTTER_IRON_SELECTORS='1',PYTHONUNBUFFERED='1')
    for key in list(env):
        if key.startswith(('BUTTER_SELECTOR_','IRON_CUDA_')) or (key.startswith('BUTTER_IRON_') and key!='BUTTER_IRON_SELECTORS'):env.pop(key)
    def dump(name,data):(out/name).write_text(json.dumps(data,indent=2)+'\n')
    def capture(name,argv):
        p=subprocess.run(argv,capture_output=True,text=True,timeout=10)
        (out/(name+'.stdout')).write_text(p.stdout);(out/(name+'.stderr')).write_text(p.stderr)
        dump(name+'.command.json',{'argv':argv,'exit':p.returncode,'utc':utc()})
        if p.returncode:raise RuntimeError(f'{name} failed {p.returncode}: {p.stderr}')
        return p.stdout
    def free_memory():
        return int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=10).strip())
    def stop_owned(p):
        if p.poll() is not None:return
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
    def run(name,argv,cap,allowed=(0,)):
        start=time.monotonic();record={'argv':argv,'started_utc':utc(),'timeout_s':cap}
        c16_started=None
        def audit_ladder_budget():
            nonlocal c16_started
            stdout_path=out/'ladder.stdout'
            if not stdout_path.exists():return
            log=stdout_path.read_text(errors='replace')
            if c16_started is None and re.search(r'C=\s*1 SERIES ',log):
                # The frozen client flushes this line immediately before writing its C1 JSON.
                c16_started=time.monotonic()
                dump('c16-budget-start.json',{'utc':utc(),'first_rep_observation_cap_s':150,'c16_phase_cap_s':300,'c16_warmup_is_not_separately_observable':True})
            ladder_path=out/'ladder.json'
            if c16_started is not None and ladder_path.exists():
                try:
                    record_json=json.loads(ladder_path.read_text())
                    if record_json.get('rungs') and record_json['rungs'][0]['concurrency']==1 and not (out/'completed-c1.json').exists():
                        c1=dict(record_json,rungs=[record_json['rungs'][0]])
                        dump('completed-c1.json',c1)
                except json.JSONDecodeError:pass
            if c16_started is None:return
            reps=re.findall(r'C=\s*16 rep(\d+)\s+tok/s=\s*([0-9.]+)\s+wall=\s*([0-9.]+)s',log)
            elapsed=time.monotonic()-c16_started
            reason=c16_budget_stop(elapsed,float(reps[0][2]) if reps else None,len(reps))
            if reason:
                dump('c16-budget-stop.json',{'reason':reason,'utc':utc(),'phase_elapsed_s':elapsed,'completed_measured_rep_lines':reps,'scope':'Conservative rental-time stop; warmup timings are not separately exposed by the unchanged client'})
                raise TimeoutError(reason)

        with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
            p=subprocess.Popen(argv,cwd=SOURCE,env=env,stdout=stdout,stderr=stderr,start_new_session=True);children.append(p)
            end=min(deadline,time.monotonic()+cap)
            try:
                while p.poll() is None:
                    if time.monotonic()>=end:raise TimeoutError(name+' deadline')
                    if memory_fault.is_set():raise RuntimeError('memory monitor saw <4GiB free or a query failure')
                    if name=='ladder':audit_ladder_budget()
                    if server is not None and server.poll() is not None:raise RuntimeError('owned server exited')
                    time.sleep(1)
                if name=='ladder':audit_ladder_budget()
                if p.returncode not in allowed:raise RuntimeError(f'{name} exit{p.returncode}')
            finally:
                stop_owned(p);record.update(exit=p.returncode,elapsed_s=time.monotonic()-start,finished_utc=utc());dump(name+'.command.json',record)
        print(name,json.dumps(record),flush=True)
    def monitor_memory():
        with (out/'memory-samples.jsonl').open('w') as f:
            while not monitor_stop.is_set():
                try:
                    free=free_memory();row={'utc':utc(),'free_mib':free}
                    if free<4*1024:memory_fault.set()
                except Exception as exc:row={'utc':utc(),'error':repr(exc)};memory_fault.set()
                f.write(json.dumps(row)+'\n');f.flush();monitor_stop.wait(5)
    def gate(phase):
        path=out/('coherency-'+phase+'.json')
        run('coherency-'+phase,['python3',str(SOURCE/'bench/hopper_ab/coherency_gate.py'),'--url','http://127.0.0.1:8890','--model',str(MODEL),'--think','off','--timeout','90','--out',str(path)],300,(0,1))
        run('quality-policy-'+phase,['python3',str(ATLAS/'reversal_exception.py'),'--source',str(SOURCE),'--coherency',str(path),'--out',str(out/('quality-policy-'+phase+'.json'))],15)
    try:
        build=json.loads(Path(args.build_receipt).read_text());assert build['complete'] and build['source']==HEAD
        binary=Path(build['binary']);assert sha(binary)==build['binary_sha256']==BINARY_SHA
        dump('build-receipt.json',build)
        harness=SOURCE/'bench/ladder38/harness_w55_conc_ladder.py';assert sha(harness)==HARNESS_SHA
        summary.update(binary_sha256=BINARY_SHA,harness_sha256=HARNESS_SHA,harness_source=capture('harness-source',['git','-C',str(SOURCE),'rev-parse','HEAD']).strip())
        proof=ATLAS/'results/qwen38-download-proof/staging-proof.json';assert sha(proof)=='6074590b1089e054afc8a4c2a23ca5e8a4184e4ff2c8ccb7898fa722cf812479'
        weights=json.loads(proof.read_text());assert weights['complete'] and weights['snapshot']==str(MODEL)
        for file in weights['files']:
            path=MODEL/file['path'];assert path.stat().st_size==file['size'] and str(path.resolve())==file['blob']
        dump('checkpoint-staging-proof.json',weights)
        device=capture('device',['nvidia-smi','--query-gpu=name,uuid,compute_cap,memory.total','--format=csv,noheader']);assert len(device.strip().splitlines())==1 and GPU_UUID in device
        assert not capture('tenants-before',['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader']).strip()
        capture('nvidia-smi-q',['nvidia-smi','-q']);capture('df-before',['df','-h','/'])
        st=os.statvfs(ROOT);assert st.f_bavail*st.f_frsize>=20*1024**3 and (st.f_blocks-st.f_bfree)*st.f_frsize<=300*10**9
        cpu=subprocess.run(['pgrep','-a','-x','cargo|rustc|nvcc|ptxas'],capture_output=True,text=True)
        (out/'compiler-before.txt').write_text(cpu.stdout+cpu.stderr);assert cpu.returncode==1,'CPU compilation prevents performance admission'
        with socket.socket() as s:assert s.connect_ex(('127.0.0.1',8890))!=0,'port8890 already bound'
        oracle=load_module('frozen_coherency',SOURCE/'bench/hopper_ab/coherency_gate.py')
        bad=oracle.judge_known_answer('The word backwards is **rotarefiger**','rotaregirfer');assert bad[0]=='FAIL'
        dump('known-bad-first.json',{'observed':bad,'utc':utc()})
        argv=[str(binary),'serve-local','--model',str(MODEL),'--max-context','8192','--parallel','16','--host','127.0.0.1','--port','8890']
        dump('serve.command.json',{'argv':argv,'env':{k:env[k] for k in ['CUDA_VISIBLE_DEVICES','CUDA_HOME','CUDA_PATH','LD_LIBRARY_PATH','BUTTER_HOME','QWEN35_MARLIN','BUTTER_IRON_SELECTORS','W55_PROMPT_MODE']},'utc':utc()})
        server=subprocess.Popen(argv,cwd=ROOT/'butter',env=env,stdout=(out/'serve.stdout').open('wb'),stderr=(out/'serve.stderr').open('wb'),start_new_session=True)
        stat=Path(f'/proc/{server.pid}/stat').read_text().rsplit(')',1)[1].split();dump('serve.identity.json',{'pid':server.pid,'pgid':server.pid,'startticks':stat[19],'utc':utc()})
        boot=time.monotonic();health=[]
        while time.monotonic()-boot<300:
            if server.poll() is not None:raise RuntimeError(f'boot exit{server.returncode}')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8890/health',timeout=2) as r:
                    health.append({'at_s':time.monotonic()-boot,'status':r.status,'body':r.read().decode()})
                    if r.status==200:break
            except Exception as exc:health.append({'at_s':time.monotonic()-boot,'error':str(exc)})
            dump('boot.json',health);time.sleep(1)
        else:raise TimeoutError('boot300s cap')
        dump('boot.json',health);summary['time_to_ready_s']=time.monotonic()-boot
        with urllib.request.urlopen('http://127.0.0.1:8890/v1/models',timeout=5) as r:(out/'models.json').write_bytes(r.read())
        monitor=threading.Thread(target=monitor_memory,daemon=True);monitor.start()
        gate('pre')
        free=free_memory();require_capacity(free,True);dump('capacity-before.json',{'free_mib':free,'required_mib':29*1024,'utc':utc()})
        # Separate high nonces keep capacity requests disjoint from the frozen client's sequence.
        # Generate prompts in one helper process that imports the frozen client unchanged.
        helper=out/'capacity-client.py'
        helper.write_text('''import asyncio, importlib.util, json, pathlib, sys\nimport aiohttp\np=pathlib.Path(sys.argv[1]);s=importlib.util.spec_from_file_location("frozen",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m._seq=899999\nasync def main():\n async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0,force_close=True)) as session:\n  result=await m.run_rep(session,"http://127.0.0.1:8890/v1/chat/completions",sys.argv[2],16,1024,1)\n pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+"\\n")\nasyncio.run(main())\n''')
        run('capacity',[str(ATLAS/'vllm/bin/python3'),str(helper),str(harness),str(MODEL),str(out/'capacity.json')],180)
        capacity=json.loads((out/'capacity.json').read_text());assert capacity['n_ok']==16 and capacity['n_err']==0
        assert capacity['prompt_tokens_per_req']==[1193] and capacity['completion_tokens_per_req']==[1]*16,'capacity work or token parity mismatch'
        free=free_memory();require_capacity(free,False);dump('capacity-after.json',{'free_mib':free,'required_mib':8*1024,'utc':utc(),'capacity_elapsed_s':capacity['wall_s']})
        remaining=deadline-time.monotonic()-100
        if remaining<120:raise TimeoutError('insufficient remaining window for ladder plus post-gate')
        run('ladder',[str(ATLAS/'vllm/bin/python3'),str(harness),'--url','http://127.0.0.1:8890','--model',str(MODEL),'--label','rental.qwen38.butter.native-lat01','--out',str(out/'ladder.json'),'--concs','1,16','--reps','3','--isl','1024','--osl','256','--warmup','1'],remaining)
        ladder=json.loads((out/'ladder.json').read_text());assert [r['concurrency'] for r in ladder['rungs']]==[1,16]
        for rung in ladder['rungs']:
            assert rung['errors_total']==0 and len(rung['reps'])==3
            for rep in rung['reps']:
                assert rep['n_ok']==rung['concurrency'] and rep['prompt_tokens_per_req']==[1193]
                for n in rep['completion_tokens_per_req']:require_tokens(1193,n,256)
        gate('post');summary['completed']=True;summary['actual_prompt_tokens']=1193;summary['actual_completion_tokens']=256
    except Exception as exc:summary['fatal_error']=repr(exc);print('STOP',repr(exc),flush=True)
    finally:
        for p in children:stop_owned(p)
        if server is not None:stop_owned(server)
        monitor_stop.set()
        if monitor is not None:monitor.join(timeout=12)
        p=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],capture_output=True,text=True,timeout=10)
        (out/'tenants-after.stdout').write_text(p.stdout);(out/'tenants-after.stderr').write_text(p.stderr)
        summary.update(gpu_released=p.returncode==0 and not p.stdout.strip(),gpu_query_exit=p.returncode,server_exit=None if server is None else server.poll(),finished_utc=utc(),elapsed_s=time.monotonic()-started)
        subprocess.run(['df','-h','/'],stdout=(out/'df-after.txt').open('w'),timeout=10)
        dump('summary.json',summary);print('GPU RELEASE',summary['gpu_released'],summary['finished_utc'],'Evidence',out,flush=True)

if __name__=='__main__':main()
