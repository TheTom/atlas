#!/usr/bin/env python3
"""Verify every regular rental result/proof file against its local export."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent
REMOTE_SCRIPT = r'''
import hashlib,json,stat
from pathlib import Path
records=[]
for name in ('results','download-proof'):
    root=Path('/workspace/atlas-rental')/name
    for p in sorted(root.rglob('*')):
        mode=p.lstat().st_mode
        if stat.S_ISDIR(mode): continue
        if not stat.S_ISREG(mode): raise RuntimeError('unexpected nonregular evidence: '+str(p))
        before=p.stat()
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        after=p.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise RuntimeError('evidence changed while hashing: '+str(p))
        records.append({'tree':name,'path':str(p.relative_to(root)),
                        'bytes':after.st_size,'sha256':digest})
print(json.dumps(records))
'''


def main():
    result = subprocess.run(
        ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-p', '51249',
         'root@93.91.156.94', 'python3', '-'], input=REMOTE_SCRIPT,
        capture_output=True, text=True, timeout=120, check=True)
    records = json.loads(result.stdout)
    failures = []
    for item in records:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise RuntimeError('invalid relative evidence path')
        local = BASE / {'results': 'remote-results', 'download-proof': 'download-proof'}[item['tree']] / relative
        if not local.is_file() or local.is_symlink():
            failures.append({'tree': item['tree'], 'path': item['path'], 'error': 'missing or nonregular'})
        elif local.stat().st_size != item['bytes'] or hashlib.sha256(local.read_bytes()).hexdigest() != item['sha256']:
            failures.append({'tree': item['tree'], 'path': item['path'], 'error': 'size or hash mismatch'})
    receipt = {'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'passed': bool(records) and not failures, 'files_checked': len(records),
               'bytes_checked': sum(item['bytes'] for item in records),
               'failures': failures, 'files': records,
               'scope': 'Every regular file currently in rental results/download-proof. Credentials, model weights and build trees are outside the export scope; local historical extras are retained.'}
    (BASE / 'final-export-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'files'}))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
