#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Audit downloaded bytes against the campaign's pinned HF file ledger."""
import datetime,hashlib,json,pathlib,sys
root=pathlib.Path('/home/pidtom/atlas-vllm-control-20260905')
ledger=json.loads((root/'nano-expected-files.json').read_text())
repo=root/'hf/hub'/('models--'+ledger['hf_id'].replace('/','--'))
snapshot=repo/'snapshots'/ledger['revision']
result={'scope':'GB10 rehearsal only','hf_id':ledger['hf_id'],'revision':ledger['revision'],'snapshot_path':str(snapshot),'files':[]}
for expected in ledger['files']:
    path=snapshot/expected['rfilename'];size=path.stat().st_size
    sha=hashlib.sha256();git=hashlib.sha1();git.update(('blob '+str(size)+'\0').encode())
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):sha.update(chunk);git.update(chunk)
    lfs=expected.get('lfs');want=lfs['sha256'] if lfs else expected['blobId'];got=sha.hexdigest() if lfs else git.hexdigest()
    record={'path':expected['rfilename'],'size':size,'sha256':sha.hexdigest(),'expected_digest':want,'expected_digest_kind':'sha256' if lfs else 'git_blob_sha1','passed':size==expected['size'] and got==want}
    result['files'].append(record);print(json.dumps(record),flush=True)
result['passed']=all(f['passed'] for f in result['files'])
result['verified_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
result['total_file_bytes']=sum(f['size'] for f in result['files'])
if result['passed']:
    (repo/'refs').mkdir(exist_ok=True)
    (repo/'refs/main').write_text(ledger['revision'])
    result['offline_main_ref']=str(repo/'refs/main')
    result['offline_main_ref_sha256']=hashlib.sha256((repo/'refs/main').read_bytes()).hexdigest()
(root/'nano-verification.json').write_text(json.dumps(result,indent=2)+'\n')
sys.exit(0 if result['passed'] else 1)
