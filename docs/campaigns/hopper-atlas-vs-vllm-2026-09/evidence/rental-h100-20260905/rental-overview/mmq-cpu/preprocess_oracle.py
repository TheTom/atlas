from pathlib import Path
import hashlib,json,re,subprocess,sys
r=Path(sys.argv[1]); phase=sys.argv[2]
v=r/'kernels/gb10/qwen3.6-27b/nvfp4/q4k_vendor/common.cuh'
s=r/'kernels/gb10/qwen3.6-27b/nvfp4/nvfp4_mmq.cu'
vendor=v.read_text(); source=s.read_text()
defines='\n'.join(l for l in vendor.splitlines() if re.match(r'#define GGML_CUDA_CC_(BLACKWELL|RUBIN) ',l))
start=vendor.index('#if !defined(GGML_USE_HIP) && __CUDA_ARCH__ >= GGML_CUDA_CC_BLACKWELL &&')
end=vendor.index('\n',vendor.index('#endif',start))
predicate=vendor[start:end]
unit=defines+'\n'+predicate+'\n'+'\n'.join(l for l in source.splitlines() if not l.startswith('#include'))
rows=[]
for arch in (900,1000,1200,1210,1300):
 cmd=['/usr/bin/clang','-E','-P','-x','c++',f'-D__CUDA_ARCH__={arch}','-']
 p=subprocess.run(cmd,input=unit,text=True,capture_output=True)
 exports=re.findall(r'extern "C" __global__ void.*?(atlas_nvfp4_\w+)\(',p.stdout)
 expected=13 if arch in (1200,1210) else 0
 rows.append(dict(arch=arch,command=cmd,exit=p.returncode,exports=exports,count=len(exports),expected=expected,pass_=p.returncode==0 and len(exports)==expected,stderr=p.stderr))
result=dict(phase=phase,scope='Actual C preprocessor and unchanged vendor capability predicate; includes omitted, no CUDA compilation or GPU execution',source_sha256=hashlib.sha256(s.read_bytes()).hexdigest(),vendor_sha256=hashlib.sha256(v.read_bytes()).hexdigest(),vendor_predicate=predicate,rows=rows)
print(json.dumps(result,indent=2))
sys.exit(0 if all(x['pass_'] for x in rows) else 1)
