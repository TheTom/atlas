#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Task-owned boot orchestration; never retries or changes a serve plan."""
import argparse, datetime, json, os, pathlib, signal, subprocess, sys, time
from control_remote_job import permitted, snapshot


def failed_boot(plan, started, status, detail):
    return {'schema':1,'engine':plan['engine'],'url':plan['url'],'model':plan['model'],
            'start_epoch':started,'timeout_s':plan['timeout_s'],'status':status,'passed':False,
            'time_to_ready_s':None,'first_token_s':None,'total_s':round(time.time()-started,3),
            'measurement_source':'launcher_process_exit_observation','detail':detail,
            'http_exchanges':None,'schema_gaps':['Readiness was cancelled after a terminal container exit; its in-memory HTTP polls are unavailable. This is an observed failed boot, not a timed readiness success.']}


def selftest():
    plan={'engine':'vllm','url':'http://fixture','model':'fixture','timeout_s':1800}
    d=failed_boot(plan,time.time()-3,'engine_exited','container exited 1')
    assert d['passed'] is False and d['time_to_ready_s'] is None
    assert d['first_token_s'] is None and d['status']=='engine_exited'
    assert 3 <= d['total_s'] < 5
    assert d['measurement_source']=='launcher_process_exit_observation'
    print('SELFTEST OK: observed process failure retains null timing and failed verdict')


def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
def capture(argv):return subprocess.run(argv,text=True,capture_output=True)
def inspect(name):
    p=capture(['docker','inspect',name]);return json.loads(p.stdout)[0] if p.returncode==0 else None


def guard(plan):
    root=pathlib.Path(plan['root']);name=plan['engine']
    with (root/(name+'-runtime.resources.jsonl')).open('w') as f:
        while True:
            d=snapshot();f.write(json.dumps(d)+'\n');f.flush()
            if not permitted(845513351168,d['used'],d['available']):
                stopped=capture(['docker','stop','--time','5',plan['container']])
                write(root/(name+'-storage-stop.json'),{'sample':d,'stop_exit':stopped.returncode,'stdout':stopped.stdout,'stderr':stopped.stderr})
                return
            state=inspect(plan['container'])
            if not state or not state['State']['Running']:return
            time.sleep(.5)


def boot(plan):
    root=pathlib.Path(plan['root']);engine=plan['engine'];(root/'results').mkdir(exist_ok=True)
    evidence={}
    for name,argv in [('gpu',['nvidia-smi']),('compute_processes',['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader']),('utilization',['nvidia-smi','--query-gpu=utilization.gpu','--format=csv,noheader,nounits']),('containers',['docker','ps','--format','{{.ID}} {{.Names}}']),('df',['df','-h','/'])]:
        p=capture(argv);evidence[name]={'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    write(root/(engine+'-prelaunch.json'),evidence)
    assert all(d['exit_code']==0 for d in evidence.values()),'preflight command failed'
    assert not evidence['compute_processes']['stdout'].strip(),'GPU compute process present: stop'
    assert all(int(n)==0 for n in evidence['utilization']['stdout'].split()),'GPU is no longer idle: stop'
    assert not evidence['containers']['stdout'].strip(),'running container present: stop for occupancy review'
    s=snapshot();assert permitted(845513351168,s['used'],s['available']),'storage preflight failed'
    started=time.time();launch=capture(plan['docker_argv'])
    write(root/(engine+'-launch.json'),{'plan':plan,'start_epoch':started,'utc':datetime.datetime.fromtimestamp(started,datetime.timezone.utc).isoformat(),'exit_code':launch.returncode,'stdout':launch.stdout,'stderr':launch.stderr})
    if launch.returncode:
        write(root/(engine+'-boot.json'),failed_boot(plan,started,'launch_failed',launch.stderr));return 1
    state=inspect(plan['container']);write(root/(engine+'-container-start.json'),state)
    with (root/(engine+'-guard.log')).open('w') as log:
        watchdog=subprocess.Popen([sys.executable,__file__,'--plan',args.plan,'--guard'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    write(root/(engine+'-guard-pid.json'),{'pid':watchdog.pid})
    argv=['bash',str(root/'time_to_ready.sh'),'--url',plan['url'],'--model',plan['model'],'--engine',engine,'--start-epoch',str(started),'--timeout-s',str(plan['timeout_s']),'--out',str(root/(engine+'-boot.json'))]
    write(root/(engine+'-readiness-command.json'),{'argv':argv})
    with (root/(engine+'-readiness.log')).open('w') as log:
        gate=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        while gate.poll() is None:
            state=inspect(plan['container'])
            if state is not None and not state['State']['Running']:
                os.killpg(gate.pid,signal.SIGTERM);gate.wait()
                if not (root/(engine+'-boot.json')).exists():
                    result=failed_boot(plan,started,'engine_exited',json.dumps(state['State']))
                    result['readiness_cancelled_on_terminal_container_exit']=True
                    write(root/(engine+'-boot.json'),result)
                break
            time.sleep(1)
    write(root/(engine+'-container-after-boot.json'),inspect(plan['container']))
    logs=capture(['docker','logs','--timestamps',plan['container']]);(root/(engine+'-server.log')).write_text(logs.stdout+logs.stderr)
    result=json.loads((root/(engine+'-boot.json')).read_text())
    write(root/(engine+'-boot.done.json'),{'passed':result['passed'],'status':result['status'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return 0 if result['passed'] else 1


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan');ap.add_argument('--guard',action='store_true');ap.add_argument('--selftest',action='store_true');args=ap.parse_args()
    if args.selftest:selftest();sys.exit()
    plan=json.loads(pathlib.Path(args.plan).read_text())
    if args.guard:guard(plan)
    else:sys.exit(boot(plan))
