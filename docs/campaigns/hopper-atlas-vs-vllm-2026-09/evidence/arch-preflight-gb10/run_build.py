# SPDX-License-Identifier: AGPL-3.0-only
"""Task-owned remote build recorder; never changes repository source."""
import datetime, json, os, pathlib, shutil, signal, subprocess, sys, time
ROOT = pathlib.Path('/home/pidtom/atlas-step-d-20260905-1249')
hw = sys.argv[1]
assert hw in ('hopper', 'b200', 'gb10')
d = ROOT / 'evidence' / hw
d.mkdir(parents=True, exist_ok=True)
def capture(name, argv):
    p = subprocess.run(argv, capture_output=True, text=True)
    (d / (name + '.stdout.txt')).write_text(p.stdout)
    (d / (name + '.stderr.txt')).write_text(p.stderr)
    (d / (name + '.json')).write_text(json.dumps({'argv': argv, 'exit_code': p.returncode}, indent=2)+'\n')
    return p
for name, argv in [('nvidia-smi',['nvidia-smi']),('spark-processes',['pgrep','-a','-x','spark']),('containers',['docker','ps']),('df-before',['df','-h','/']),('nvidia-smi-q',['nvidia-smi','-q'])]:
    p=capture(name,argv)
    if name=='spark-processes' and p.returncode != 1: raise SystemExit('BLOCKED: spark process/query error')
    if name!='spark-processes' and p.returncode: raise SystemExit('BLOCKED: preflight query error')
for name, argv in [('compute-apps',['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader']),('container-ids',['docker','ps','-q'])]:
    p=capture(name,argv)
    if p.returncode or p.stdout.strip(): raise SystemExit('BLOCKED: foreign occupancy or query error')
if shutil.disk_usage('/').free < 20_000_000_000: raise SystemExit('BLOCKED: insufficient build headroom')
env=os.environ.copy()
for k in ['ATLAS_SKIP_BUILD','ATLAS_CUDA_ARCH','CUTLASS_HOME','FLASHINFER_HOME','RUSTFLAGS','RUSTUP_TOOLCHAIN','CARGO_TARGET_DIR']:
    env.pop(k,None)
env.update(PATH='/home/pidtom/.cargo/bin:/usr/local/cuda/bin:'+env['PATH'], CARGO_HOME=str(ROOT/'cargo-home'), CARGO_TARGET_DIR=str(ROOT/('target-'+hw)), CUDA_HOME='/usr/local/cuda', CUDARC_CUDA_VERSION='13000', ATLAS_TARGET_HW=hw, ATLAS_TARGET_MODEL='nemotron-3-nano-30b-a3b', ATLAS_TARGET_QUANT='nvfp4', CARGO_BUILD_JOBS='4', CARGO_INCREMENTAL='0')
cmd=['/usr/bin/time','-v','-o',str(d/'build.time.txt'),'/home/pidtom/.cargo/bin/cargo','build','--locked','--release','-p','spark-server','--bin','spark','--no-default-features','--features','cuda,nccl']
meta={'argv':cmd,'cwd':str(ROOT/'repo'),'environment':{k:v for k,v in env.items() if k.startswith(('ATLAS_','CARGO_','CUDA','CUDARC')) or k=='PATH'},'source_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT/'repo',text=True).strip(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(d/'build.command.json').write_text(json.dumps(meta,indent=2)+'\n')
start=time.monotonic(); stop=None
with (d/'build.stdout.txt').open('w') as out, (d/'build.stderr.txt').open('w') as err, (d/'resources.jsonl').open('w') as resources:
    p=subprocess.Popen(cmd,cwd=ROOT/'repo',env=env,stdout=out,stderr=err,start_new_session=True)
    while p.poll() is None:
        free=shutil.disk_usage('/').free
        resources.write(json.dumps({'elapsed_s':time.monotonic()-start,'free_bytes':free})+'\n'); resources.flush()
        # 15 GB stop leaves 3 GB beyond the user's 12 GB floor.
        if free < 15_000_000_000 or time.monotonic()-start > 7200:
            stop='resource/time stopping rule'; os.killpg(p.pid,signal.SIGTERM)
            try: p.wait(timeout=20)
            except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL)
            break
        time.sleep(2)
    rc=p.wait()
meta.update(exit_code=rc,wall_seconds=time.monotonic()-start,stopping_reason=stop)
(d/'build.status.json').write_text(json.dumps(meta,indent=2)+'\n')
capture('df-after',['df','-h','/'])
capture('target-size',['du','-sb',str(ROOT/('target-'+hw))])
capture('nvcc-version',['/usr/local/cuda/bin/nvcc','--version'])
if rc==0:
    (ROOT/'binaries'/hw).mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/('target-'+hw)/'release/spark',ROOT/'binaries'/hw/'spark')
    capture('binary-sha256',['sha256sum',str(ROOT/'binaries'/hw/'spark')])
print(json.dumps(meta),flush=True)
sys.exit(rc)
