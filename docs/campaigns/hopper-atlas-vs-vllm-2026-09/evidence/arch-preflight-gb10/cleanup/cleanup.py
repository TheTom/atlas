# SPDX-License-Identifier: AGPL-3.0-only
import pathlib, subprocess, os, shutil, json, datetime
root=pathlib.Path('/home/pidtom/atlas-step-d-20260905-1249')
assert root.name=='atlas-step-d-20260905-1249' and root.parent==pathlib.Path('/home/pidtom') and not root.is_symlink()
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root/'repo',text=True).strip()
assert sha=='b2c17cfe30c33c53d28c4fbec35f6204b8cfb14b'
active=[]
for p in pathlib.Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   cwd=(p/'cwd').resolve(strict=True)
   if cwd==root or root in cwd.parents: active.append(p.name)
  except (OSError,RuntimeError): pass
assert not active, 'Owned workspace has active process cwd: '+repr(active)
for argv in [['nvidia-smi'],['pgrep','-a','-x','spark'],['docker','ps'],['df','-h','/'],['df','-B1','/'],['du','-sb',str(root)]]:
 p=subprocess.run(argv,capture_output=True,text=True); print(json.dumps({'phase':'before_cleanup','argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}),flush=True)
shutil.rmtree(root)
assert not root.exists()
for argv in [['df','-h','/'],['df','-B1','/'],['nvidia-smi'],['docker','ps']]:
 p=subprocess.run(argv,capture_output=True,text=True); print(json.dumps({'phase':'after_cleanup','argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}),flush=True)
print(json.dumps({'removed_owned_root':str(root),'exists_after':root.exists(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
