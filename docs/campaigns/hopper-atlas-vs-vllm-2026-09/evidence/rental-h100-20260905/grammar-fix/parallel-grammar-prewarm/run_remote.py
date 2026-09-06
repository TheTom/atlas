import json,pathlib,subprocess,time,sys
root=pathlib.Path(__file__).parent
label,cmd=sys.argv[1:]
remote='cd /home/pidtom/atlas-grammar-prewarm-20260905 && export PATH="$HOME/.cargo/bin:/usr/local/cuda/bin:$PATH" && CUDA_VISIBLE_DEVICES="" ATLAS_SKIP_BUILD=1 CUDARC_CUDA_VERSION=13000 CARGO_TARGET_DIR=/home/pidtom/atlas-hopper-gate-full/target '+cmd
argv=['ssh','-o','BatchMode=yes','pidtom@192.168.50.125',remote]
(root/(label+'.command.json')).write_text(json.dumps({'argv':argv},indent=2)+'\n')
start=time.monotonic()
with (root/(label+'.stdout')).open('w') as out,(root/(label+'.stderr')).open('w') as err:
 r=subprocess.run(argv,stdout=out,stderr=err)
(root/(label+'.exit-code.txt')).write_text(str(r.returncode)+'\n')
(root/(label+'.timing.json')).write_text(json.dumps({'wall_seconds':time.monotonic()-start},indent=2)+'\n')
print(label,'exit',r.returncode)
print((root/(label+'.stdout')).read_text()[-5000:]);print((root/(label+'.stderr')).read_text()[-2500:])
