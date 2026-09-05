#!/usr/bin/env python3
"""Bounded offline audit. Only copies in this evidence directory are executed."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SANDBOX = ROOT / "offline-sandbox"
MOCK_ROOT = SANDBOX / "root"
BIN = SANDBOX / "bin"
for p in (MOCK_ROOT / ".local/bin", MOCK_ROOT / "vllm-venv/bin", MOCK_ROOT / "venv/bin", BIN,
          MOCK_ROOT / "etc", MOCK_ROOT / "hf"):
    p.mkdir(parents=True, exist_ok=True)


def executable(path, text):
    path.write_text(text); path.chmod(0o700)


def copy_script(name):
    # Redirect only literal root paths into this sandbox. Branches and commands
    # retain their original logic; all network/install/GPU executables are stubs.
    source = (ROOT / "source" / name).read_text()
    adapted = source.replace("/root", shlex.quote(str(MOCK_ROOT)))
    adapted = adapted.replace("/etc/os-release", shlex.quote(str(MOCK_ROOT / "etc/os-release")))
    p = SANDBOX / name; p.write_text(adapted); return p


ENV = {"PATH": str(BIN) + ":/usr/bin:/bin", "HF_HOME": str(MOCK_ROOT / "hf"),
       "LC_ALL": "C", "AUDIT_MODE": "ok"}
(MOCK_ROOT / "env.sh").write_text("# Offline fixture, no credentials.\n")
(MOCK_ROOT / "etc/os-release").write_text("PRETTY_NAME='Offline Ubuntu Fixture'\n")
executable(MOCK_ROOT / ".local/bin/uv", "#!/bin/sh\necho 'FIXTURE package resolution failed' >&2\nexit 17\n")
executable(MOCK_ROOT / "vllm-venv/bin/python", "#!/bin/sh\necho 'FIXTURE import failed' >&2\nexit 19\n")
executable(MOCK_ROOT / "venv/bin/hf", "#!/bin/sh\necho 'UNEXPECTED_FAKE_HF_INVOCATION' >&2\nexit 87\n")
executable(BIN / "df", "#!/bin/sh\ncase \"$AUDIT_MODE\" in defer) printf 'Avail\\n10G\\n';; *) printf 'Avail\\n300G\\n';; esac\n")
executable(BIN / "nproc", "#!/bin/sh\necho 32\n")
executable(BIN / "free", "#!/bin/sh\necho 'Mem: 256 1 255'\n")
executable(BIN / "mount", "#!/bin/sh\necho 'overlay on / type overlay'\n")
executable(BIN / "dpkg-query", "#!/bin/sh\nexit 1\n")
executable(BIN / "nvidia-smi", """#!/bin/sh
case "$*" in
  '-L') printf 'GPU 0: H100 fixture\\nGPU 1: H100 fixture\\n';;
  *query-compute-apps*) if [ "$AUDIT_MODE" = busy-query-error ]; then echo 'FIXTURE cannot query processes' >&2; exit 43; fi;;
  *query-gpu=compute_cap*) printf '9.0\\n9.0\\n';;
  *query-gpu=driver_version*) printf '595.71\\n595.71\\n';;
  'topo -m') printf ' GPU0 GPU1\\nGPU0 X NV18\\nGPU1 NV18 X\\n';;
  *) printf '0, H100 fixture, 9.0, 81920 MiB, 595.71\\n1, H100 fixture, 9.0, 81920 MiB, 595.71\\n';;
esac
""")
# Execute the original embedded network-check Python code while replacing its
# sole transport function. This makes both success and failure fully offline.
network_harness = SANDBOX / "network_harness.py"
network_harness.write_text("""import os,sys,urllib.request,urllib.error
class Response:
    def read(self, size): return b'{}'
def fake_urlopen(*args, **kwargs):
    if os.environ.get('AUDIT_MODE') == 'network-error':
        raise urllib.error.URLError('FIXTURE offline')
    return Response()
urllib.request.urlopen = fake_urlopen
exec(compile(sys.stdin.read(), '<original-preflight-network-code>', 'exec'))
""")
executable(BIN / "python3", "#!/bin/sh\nexec " + shlex.quote(sys.executable) + " " + shlex.quote(str(network_harness)) + "\n")
results = []


def shell_case(case, name, mode, args=()):
    command = ["bash", str(copy_script(name)), *args]
    r = subprocess.run(command, cwd=SANDBOX, env={**ENV, "AUDIT_MODE": mode},
                       capture_output=True, text=True, timeout=10)
    record = {"case": case, "original": str(ROOT / "source" / name),
              "adaptation": "Literal /root and /etc/os-release paths only; external commands stubbed offline",
              "command": command, "exit_code": r.returncode,
              "stdout": r.stdout, "stderr": r.stderr}
    (ROOT / (case + ".json")).write_text(json.dumps(record, indent=2) + "\n")
    print(case, "exit", r.returncode); results.append(record)


shell_case("install-failure-exits-zero", "install_vllm.sh", "ok")
shell_case("deferred-queue-reports-done", "dl_queue.sh", "defer")
shell_case("network-failure-reports-go", "preflight_node.sh", "network-error", ("--want-gpus", "2"))
shell_case("process-query-failure-reports-idle", "preflight_node.sh", "busy-query-error", ("--want-gpus", "2"))

spec = importlib.util.spec_from_file_location("audited_logit_diff", ROOT / "source/logit_diff.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def oracle_case(case, a, b):
    # Exercise production request construction, normalization, comparison and
    # verdict aggregation while only replacing the HTTP boundary.
    module.post_json = lambda base, *args, **kwargs: (200, json.dumps(a if base == "fixture-a" else b), None)
    args = module._selftest_args("fixture-a", "fixture-b")
    output = io.StringIO()
    code, report = module.run_oracle(args, out=output)
    record = {"case": case, "oracle_exit": code, "report": report, "stdout": output.getvalue()}
    (ROOT / (case + ".json")).write_text(json.dumps(record, indent=2) + "\n")
    print(case, "exit", code); results.append({"case": case, "exit_code": code})


oracle_case("shorter-prefix-falsely-agrees", module._canned(["391"]), module._canned(["391", " extra"]))
empty = {"choices": [{"logprobs": {"tokens": [], "token_logprobs": [], "top_logprobs": []}, "text": "", "finish_reason": "length"}]}
oracle_case("empty-legacy-streams-falsely-agree", empty, empty)
oracle_case("same-wrong-answer-is-agreement-only", module._canned(["wrong"]), module._canned(["wrong"]))
(ROOT / "red-observations.json").write_text(json.dumps(results, indent=2) + "\n")
receipt = json.loads((ROOT / "source-receipt.json").read_text())
for entry in receipt["files"]:
    assert hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest() == entry["sha256"], entry["path"]
print("All six original inputs remain byte-identical")
