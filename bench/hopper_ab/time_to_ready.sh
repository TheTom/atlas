#!/usr/bin/env bash
# Measure how long an engine takes to become servable, and how long its first
# token takes once it is.
#
# The PRD makes a 30-minute boot cap a GATE, so this has to be a measurement
# rather than an impression. Two things it deliberately does not assume:
#
#  * The clock starts at --start-epoch, which the CALLER supplies from just
#    before it launches the serve process. A script that starts its own clock
#    measures its own startup and forgives whatever the launcher did first.
#  * Connection-refused is a LOADING state, not an error. Atlas answers
#    503 {"status":"loading"} on /health while weights load and then 200; vLLM
#    refuses the TCP connection outright until its server binds and then
#    answers 200. Treating refusal as failure would score vLLM as never booting.
#
# Readiness and usability are different claims, so both are reported: an engine
# can answer /health before its graphs are captured, and the one-token request
# afterwards is what says so.
#
# Usage:
#   time_to_ready.sh --url URL --model MODEL [--engine atlas|vllm]
#                    [--start-epoch SECS] [--timeout-s 1800] [--out FILE]
#   time_to_ready.sh --selftest
#
# Exits non-zero when the endpoint has not answered 200 within --timeout-s.
set -uo pipefail

URL=""
MODEL=""
ENGINE="unknown"
START_EPOCH=""
TIMEOUT_S=1800
OUT=""
SELFTEST=0

usage() { sed -n '2,26p' "$0"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --url) URL="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --engine) ENGINE="$2"; shift 2 ;;
    --start-epoch) START_EPOCH="$2"; shift 2 ;;
    --timeout-s) TIMEOUT_S="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --selftest) SELFTEST=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

# `date +%s.%N` is a GNU extension -- BSD date (macOS, where the selftest is
# run) prints a literal "N". python3 answers the same question everywhere, and
# this repo never invokes bare `python`.
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }

# Emit one JSON object. Built here rather than by string-concatenation so a
# model id containing a quote cannot produce a file that does not parse.
emit() { # $1 ready_s|null  $2 first_token_s|null  $3 polls  $4 codes  $5 status
  python3 - "$ENGINE" "$URL" "$MODEL" "$1" "$2" "$3" "$4" "$5" "$TIMEOUT_S" <<'PY'
import json, sys
eng, url, model, ready, first, polls, codes, status, timeout = sys.argv[1:10]
num = lambda v: None if v in ("", "null") else float(v)
print(json.dumps({
    "schema": 1,
    "engine": eng,
    "url": url,
    "model": model,
    "time_to_ready_s": num(ready),
    "first_token_s": num(first),
    "polls": int(polls),
    "http_codes_seen": [c for c in codes.split(",") if c],
    "timeout_s": float(timeout),
    "status": status,
}, indent=2))
PY
}

measure() {
  local t0 codes="" polls=0 code ready="" first="null"
  t0="${START_EPOCH:-$(now)}"
  while :; do
    # --max-time bounds a hung accept; -o /dev/null keeps the body out of the
    # code. A refused connection makes curl print nothing, hence the default.
    code="$(curl -s -o /dev/null -m 5 -w '%{http_code}' "$URL/health" 2>/dev/null)"
    # curl writes 000 when it never got a response line at all -- a refused
    # connection or a timed-out one. Recorded under its own name because on the
    # vLLM leg it IS the loading state and a reader must not mistake a normal
    # boot for a run of transport failures.
    [ -z "$code" ] || [ "$code" = "000" ] && code="conn-refused"
    polls=$((polls + 1))
    case ",$codes," in *",$code,"*) ;; *) codes="${codes:+$codes,}$code" ;; esac
    if [ "$code" = "200" ]; then
      ready="$(python3 -c "import sys;print(f'{float(sys.argv[1])-float(sys.argv[2]):.3f}')" "$(now)" "$t0")"
      break
    fi
    if [ "$(python3 -c "import sys;print(int(float(sys.argv[1])-float(sys.argv[2])>=float(sys.argv[3])))" "$(now)" "$t0" "$TIMEOUT_S")" = "1" ]; then
      emit null null "$polls" "$codes" "timeout"
      echo "NOT READY after ${TIMEOUT_S}s (${polls} polls, codes: ${codes})" >&2
      return 1
    fi
    sleep 1
  done

  # Ready is not the same as usable. One token, measured separately.
  if [ -n "$MODEL" ]; then
    local a b
    a="$(now)"
    if curl -s -o /dev/null -m 120 -X POST "$URL/v1/chat/completions" \
        -H 'Content-Type: application/json' \
        -d "$(python3 -c 'import json,sys; print(json.dumps({"model": sys.argv[1], "messages":[{"role":"user","content":"hi"}], "max_tokens":1, "temperature":0, "seed":42}))' "$MODEL")"; then
      b="$(now)"
      first="$(python3 -c "import sys;print(f'{float(sys.argv[1])-float(sys.argv[2]):.3f}')" "$b" "$a")"
    fi
  fi
  emit "$ready" "$first" "$polls" "$codes" "ready"
}

selftest() {
  # Validate the INSTRUMENT against a known case: a stub that reports loading
  # twice and then ready. The measured value must be >= 2 s (two 1 s polls at
  # minimum), the JSON must parse, and both non-200 shapes must appear in the
  # codes list -- otherwise the poll loop is silently treating a loading
  # response as readiness, which is the failure that would make every boot
  # number in the campaign too small.
  local dir port stub_pid out rc
  dir="$(mktemp -d)"
  port="$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')"
  cat > "$dir/stub.py" <<'PY'
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

STATE = {"health_hits": 0}

class H(BaseHTTPRequestHandler):
    def _send(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path != "/health":
            return self._send(404, {"error": "not found"})
        STATE["health_hits"] += 1
        # Atlas's shape: 503 loading, 503 loading, then 200 ready.
        if STATE["health_hits"] <= 2:
            return self._send(503, {"status": "loading"})
        self._send(200, {"status": "ready"})

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self._send(200, {"choices": [{"message": {"content": "x"},
                                      "finish_reason": "length"}]})

    def log_message(self, *a):
        pass

HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PY
  python3 "$dir/stub.py" "$port" & stub_pid=$!
  # Wait for the stub to bind before starting the clock, so the selftest
  # measures the poll loop rather than python's import time.
  python3 - "$port" <<'PY'
import socket, sys, time
deadline = time.time() + 10
while time.time() < deadline:
    try:
        socket.create_connection(("127.0.0.1", int(sys.argv[1])), 0.2).close()
        sys.exit(0)
    except OSError:
        time.sleep(0.05)
sys.exit("stub never bound")
PY
  URL="http://127.0.0.1:$port" MODEL="stub-model" ENGINE="selftest" TIMEOUT_S=30
  out="$(measure)"; rc=$?
  kill "$stub_pid" 2>/dev/null; wait "$stub_pid" 2>/dev/null
  rm -rf "$dir"
  [ $rc -eq 0 ] || { echo "SELFTEST FAIL: measure exited $rc" >&2; return 1; }
  echo "$out"
  python3 - <<PY || return 1
import json, sys
d = json.loads('''$out''')
assert d["status"] == "ready", d
assert d["time_to_ready_s"] >= 2.0, f"two loading polls must cost >= 2 s, got {d['time_to_ready_s']}"
assert d["polls"] >= 3, d
assert "503" in d["http_codes_seen"], f"loading state never observed: {d}"
assert "200" in d["http_codes_seen"], d
assert d["first_token_s"] is not None, d
print("SELFTEST OK: measured", d["time_to_ready_s"], "s over", d["polls"], "polls", d["http_codes_seen"])
PY
}

if [ "$SELFTEST" = "1" ]; then
  selftest
  exit $?
fi

[ -n "$URL" ] || { echo "--url is required" >&2; usage >&2; exit 2; }
URL="${URL%/}"

if [ -n "$OUT" ]; then
  measure | tee "$OUT"
  exit "${PIPESTATUS[0]}"
fi
measure
