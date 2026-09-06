import subprocess, time, json
from pathlib import Path
p = Path(__file__).parent
env = "cd /workspace/atlas-rental/src/native-bf16-head-batch-gemv && env CUDA_VISIBLE_DEVICES= ATLAS_SKIP_BUILD=1 CUDARC_CUDA_VERSION=13000 CARGO_TARGET_DIR=/workspace/atlas-rental/target-cpu-checks CARGO_BUILD_JOBS=4 ATLAS_TARGET_HW=hopper ATLAS_TARGET_MODEL=qwen3.8-27b ATLAS_TARGET_QUANT=nvfp4 /root/.cargo/bin/cargo +1.93.1 "
for name, args in [("full-model", "test --locked -p spark-model"), ("clippy", "clippy --locked -p spark-model --tests"), ("rustdoc", "doc --locked --workspace --no-deps"), ("doctests", "test --locked --workspace --doc")]:
    subprocess.run(["python3", "/Users/tom/Documents/New project/atlas-campaign-evidence/verify_destination.py"], check=True)
    cmd = env + args
    t = time.time()
    with (p / (name + ".log")).open("w") as out:
        r = subprocess.run(["ssh", "-p", "51249", "root@93.91.156.94", cmd], stdout=out, stderr=subprocess.STDOUT)
    receipt = {"command": cmd, "exit": r.returncode, "wall_s": time.time() - t}
    (p / (name + ".json")).write_text(json.dumps(receipt, indent=2) + "\n")
    print(name, json.dumps(receipt), flush=True)
    print("\n".join(line for line in (p / (name + ".log")).read_text().splitlines() if "test result:" in line), flush=True)
    if r.returncode: raise SystemExit(r.returncode)
