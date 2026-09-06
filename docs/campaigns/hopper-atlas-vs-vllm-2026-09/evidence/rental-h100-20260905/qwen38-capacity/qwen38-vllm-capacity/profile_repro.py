import json,pathlib,sys,types
from installed_guard import guard
root=pathlib.Path(__file__).parent
base=json.loads((root/'original-campaign-entry.json').read_text())
args=list(base['args'])
if len(sys.argv)>1:
 profile=json.loads(pathlib.Path(sys.argv[1]).read_text());args+=profile['additional_serve_args']
limit=int(args[args.index('--max-num-seqs')+1]) if '--max-num-seqs' in args else 1024
mode=types.SimpleNamespace(has_full_cudagraphs=lambda:True)
guard(types.SimpleNamespace(has_mamba_layers=True,num_blocks=810),limit,mode,False)
assert min(limit*2,512,8192)==512, 'graph capture ceiling changed'
assert limit>=16, 'frozen C16 workload would be capped'
print(json.dumps({'guard':'PASS','max_num_seqs':limit,'max_cudagraph_capture_size':512,'frozen_concurrency_max':16,'margin_blocks':810-limit,'changes_from_base':args[len(base['args']):]}))
