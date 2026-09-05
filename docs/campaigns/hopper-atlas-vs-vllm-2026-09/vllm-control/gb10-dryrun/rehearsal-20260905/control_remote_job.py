#!/usr/bin/env python3
"""Task-owned download runner with byte-level disk headroom checks."""
import argparse,datetime,json,os,pathlib,signal,subprocess,sys,time


def permitted(baseline_used, used, available):
    # Keep 5 GB emergency headroom below the user's 70 GB / 12 GB limits.
    return used - baseline_used <= 65_000_000_000 and available >= 17_000_000_000


def selftest():
    assert permitted(100,100,20_000_000_000)
    assert not permitted(100,65_000_000_101,30_000_000_000)
    assert not permitted(100,100,16_999_999_999)
    assert permitted(100,65_000_000_100,17_000_000_000)
    print('SELFTEST OK: known low-space and excess-new-usage cases rejected')


def snapshot():
    s=os.statvfs('/')
    return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'used':(s.f_blocks-s.f_bfree)*s.f_frsize,'available':s.f_bavail*s.f_frsize}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--selftest',action='store_true');ap.add_argument('--job');a=ap.parse_args()
    if a.selftest: selftest();return
    job=json.loads(pathlib.Path(a.job).read_text());root=pathlib.Path(job['root']);phase=job['phase']
    (root/(phase+'.before.df.txt')).write_text(subprocess.check_output(['df','-h','/'],text=True))
    initial=snapshot();result={'job':job,'before':initial};proc=None
    try:
        if not permitted(job['baseline_used'],initial['used'],initial['available']):
            raise RuntimeError('download preflight exceeds guarded storage allowance')
        env=os.environ.copy();env.update(job.get('environment',{}))
        with (root/(phase+'.log')).open('w') as log,(root/(phase+'.resources.jsonl')).open('w') as resources:
            proc=subprocess.Popen(job['argv'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            result['pid']=proc.pid
            (root/(phase+'.started.json')).write_text(json.dumps(result,indent=2)+'\n')
            while True:
                sample=snapshot();resources.write(json.dumps(sample)+'\n');resources.flush()
                if not permitted(job['baseline_used'],sample['used'],sample['available']):
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                    raise RuntimeError('storage guard stopped task-owned process before hard limits')
                code=proc.poll()
                if code is not None:result['exit_code']=code;break
                time.sleep(0.5)
    except Exception as exc:
        result['exit_code']=1;result['error']=f'{type(exc).__name__}: {exc}'
    finally:
        result['after']=snapshot()
        (root/(phase+'.after.df.txt')).write_text(subprocess.check_output(['df','-h','/'],text=True))
        (root/(phase+'.done.json')).write_text(json.dumps(result,indent=2)+'\n')
    sys.exit(result['exit_code'])

if __name__=='__main__':main()
