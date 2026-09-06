import json,pathlib,sys,types
from installed_guard import guard
root=pathlib.Path(__file__).parent
blocks=int(sys.argv[1]); limit=int(sys.argv[2])
kv=types.SimpleNamespace(has_mamba_layers=True,num_blocks=blocks)
mode=types.SimpleNamespace(has_full_cudagraphs=lambda:True)
guard(kv,limit,mode,False)
print(json.dumps({"guard":"PASS","max_num_seqs":limit,"mamba_blocks":blocks,"gpu_work":False}))
