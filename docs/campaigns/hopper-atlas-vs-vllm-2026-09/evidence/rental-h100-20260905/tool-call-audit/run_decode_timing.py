import datetime, json, subprocess, sys, time
from pathlib import Path
root=Path('/workspace/atlas-rental')
out=root/'results/diagnostic.atlas.decodetiming01'
for i in range(120):
    if (out/'ready.utc').exists(): break
    if (out/'exit-code.txt').exists(): raise SystemExit('server exited before readiness')
    time.sleep(1)
else: raise SystemExit('readiness window exceeded')
rows=[]
try:
    for case in ['plain']+['tool']*4:
        n=len(rows)
        payload=root/'protocol-requests'/f'{case}-stream.json'
        target=out/f'timing-{n}-{case}'
        command=['python3',str(root/'src/atlas/bench/campaign/stream_probe.py'),'--url','http://127.0.0.1:8888/v1/chat/completions','--request-json',str(payload),'--out',str(target),'--timeout-s','60']
        with (out/f'timing-{n}-{case}.log').open('w') as log:
            done=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=70)
        r=json.loads((target/'report.json').read_text())
        ok=r['passed'] and done.returncode==0
        if case=='tool':
            calls=list(r['tool_calls'].values())
            ok=ok and len(calls)==1 and calls[0]['name']=='get_weather' and json.loads(calls[0]['arguments'])=={'city':'Reykjavik','days':3} and r['finish_reason']=='tool_calls'
        rows.append({'case':case,'exit_code':done.returncode,'valid':ok,'first_content_s':r['first_content_s'],'first_tool_s':r['first_tool_s'],'elapsed_s':r['elapsed_s'],'usage':r['usage']})
        print(json.dumps(rows[-1]),flush=True)
        if not ok: break
    (out/'decode-timing-summary.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'diagnostic only; timing environment enabled','rows':rows,'all_valid':all(r['valid'] for r in rows)},indent=2)+'\n')
finally:
    (out/'requests-complete').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
