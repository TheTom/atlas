#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Execute the frozen ladder jobs once each, in the recorded order."""
import json,pathlib,subprocess,sys,datetime
root=pathlib.Path('/home/pidtom/atlas-vllm-control-20260905');engine=sys.argv[1]
names=['vllm-a-lat','vllm-a-agent','vllm-b-lat','vllm-b-agent'] if engine=='vllm' else ['atlas-ab-lat','atlas-ab-agent']
container=engine+'-control-nano-20260905';results=[]
for name in names:
    state=subprocess.check_output(['docker','inspect','--format','{{.State.Running}}',container],text=True).strip()
    if state!='true':
        results.append({'job':name,'status':'NOT_RUN','reason':'engine container exited'});continue
    command=[sys.executable,str(root/'control_remote_job.py'),'--job',str(root/('control-'+name+'.json'))]
    code=subprocess.call(command)
    results.append({'job':name,'status':'EXECUTED','exit_code':code,'argv':command})
(root/(engine+'-ladders.done.json')).write_text(json.dumps({'engine':engine,'scope':'GB10 rehearsal only; not Hopper data','jobs':results,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
