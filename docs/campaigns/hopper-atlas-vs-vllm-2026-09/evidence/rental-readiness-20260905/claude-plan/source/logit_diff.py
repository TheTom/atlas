#!/usr/bin/env python3
"""logit_diff.py - the "runs but wrong" oracle: does Atlas emit the SAME tokens as vLLM?

A benchmark that runs, is fast, and is silently wrong is the worst outcome of a rental
day. This compares two OpenAI-compatible servers position-by-position on a fixed prompt
set at temperature 0, so a numerics bug shows up as "first divergence at index 12"
instead of as a vibes-based reading of two paragraphs.

Usage:
  logit_diff.py --a http://127.0.0.1:8888 --b http://127.0.0.1:8000 \
                --model-a <id> --model-b <id> [--max-tokens 64] [--top-k 5] \
                [--think on|off] [--raw] [--min-agree N|full] [--out report.json]
  logit_diff.py --selftest

What it measures, per prompt, per position i:
  (a) argmax equality      - at temperature 0 the emitted token IS the argmax
  (b) top-K Jaccard        - |A_topK n B_topK| / |A_topK u B_topK| over token strings
  (c) |logprob delta|      - of the token A chose, looked up in B's top-K (None if absent)

--raw additionally hits /v1/completions with the plain prompt text, which takes the chat
template out of the picture. A divergence that appears on /v1/chat/completions but NOT on
/v1/completions is a template bug, not a kernel bug. That distinction is worth the extra
four requests.

Exit codes:
  0  every prompt agreed for at least --min-agree leading positions (default: all of them)
  1  at least one prompt diverged earlier than that
  2  oracle unavailable - a server returned logprobs: null, or was unreachable. This is
     NEVER reported as agreement; a missing oracle is not a passing oracle.

Stdlib only (urllib/json/argparse/http.server). Python 3.12+.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# The campaign's coherency-gate prompts. Do not edit casually: divergence indices from
# different runs are only comparable when the prompt bytes are identical.
PROMPTS = [
    {"name": "arith_17x23",
     "text": "What is 17 * 23? Reply with the number, then explain briefly.",
     "expect": "391"},
    {"name": "capital_japan",
     "text": "Name the capital city of Japan, then describe it in a few sentences.",
     "expect": "Tokyo"},
    {"name": "spell_backwards",
     "text": "Spell the word 'refrigerator' backwards, then explain how you did it.",
     "expect": "rotaregirfer"},
    {"name": "five_primes",
     "text": "List exactly five prime numbers greater than 100, comma separated.",
     "expect": None},
]


class OracleUnavailable(Exception):
    """Raised when a server cannot answer the question at all (null logprobs, HTTP error,
    connection refused). Deliberately distinct from 'the answers differ'."""


# --------------------------------------------------------------------------- transport

def post_json(base, path, body, timeout=300, api_key=None):
    """POST a JSON body. Returns (status:int|None, raw_text:str, error:str|None)."""
    url = base.rstrip("/") + path
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace"), None
    except Exception as exc:  # URLError, socket.timeout, ...
        return None, "", "%s: %s" % (type(exc).__name__, exc)


def build_chat_body(model, prompt, max_tokens, top_k, think):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": 42,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "logprobs": True,
        "top_logprobs": top_k,
        "stream": False,
    }
    if not think:
        # Reasoning traces are nondeterministic length; they wreck position alignment.
        body["chat_template_kwargs"] = {"enable_thinking": False}
    return body


def build_completions_body(model, prompt, max_tokens, top_k):
    # No chat template, no system prompt, no thinking toggle: the raw path.
    return {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": 42,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "logprobs": top_k,
        "stream": False,
    }


# --------------------------------------------------------------------------- normalize

def normalize_tokens(obj):
    """Pull a uniform [{token, logprob, top:[(tok, lp), ...]}] stream out of either the
    chat shape (logprobs.content[]) or the legacy completions shape (logprobs.tokens[]).
    Raises OracleUnavailable when the server declined to give us logprobs at all."""
    if not isinstance(obj, dict):
        raise OracleUnavailable("response was not a JSON object")
    if "error" in obj and "choices" not in obj:
        raise OracleUnavailable("server returned an error object: %s" % json.dumps(obj)[:300])
    choices = obj.get("choices")
    if not choices:
        raise OracleUnavailable("response has no choices[]")
    lp = choices[0].get("logprobs")
    if lp is None:
        raise OracleUnavailable("logprobs is null")
    out = []
    content = lp.get("content") if isinstance(lp, dict) else None
    if content:
        for entry in content:
            top = [(t.get("token"), float(t.get("logprob")))
                   for t in (entry.get("top_logprobs") or [])]
            out.append({"token": entry.get("token"),
                        "logprob": float(entry.get("logprob")),
                        "top": top})
        return out
    if isinstance(lp, dict) and lp.get("tokens") is not None:
        toks = lp.get("tokens") or []
        tlps = lp.get("token_logprobs") or []
        tops = lp.get("top_logprobs") or []
        for i, tok in enumerate(toks):
            val = tlps[i] if i < len(tlps) and tlps[i] is not None else float("-inf")
            raw = tops[i] if i < len(tops) else None
            pairs = []
            if isinstance(raw, dict):            # {"tok": -0.1, ...}
                pairs = [(k, float(v)) for k, v in raw.items()]
            elif isinstance(raw, list):          # [{"token":..,"logprob":..}, ...]
                pairs = [(d.get("token"), float(d.get("logprob"))) for d in raw]
            out.append({"token": tok, "logprob": float(val), "top": pairs})
        return out
    raise OracleUnavailable("logprobs object present but carries neither .content nor .tokens")


# --------------------------------------------------------------------------- comparison

def compare(a_toks, b_toks):
    """Position-by-position diff of two normalized streams."""
    n = min(len(a_toks), len(b_toks))
    first_div = None
    matches = 0
    jaccards = []
    positions = []
    for i in range(n):
        ta, tb = a_toks[i], b_toks[i]
        same = ta["token"] == tb["token"]
        if same:
            matches += 1
        elif first_div is None:
            first_div = i
        sa = {t for t, _ in ta["top"]} or {ta["token"]}
        sb = {t for t, _ in tb["top"]} or {tb["token"]}
        union = sa | sb
        jac = (len(sa & sb) / len(union)) if union else 1.0
        jaccards.append(jac)
        bmap = dict(tb["top"])
        delta = abs(ta["logprob"] - bmap[ta["token"]]) if ta["token"] in bmap else None
        positions.append({"i": i, "a_token": ta["token"], "b_token": tb["token"],
                          "argmax_match": same, "jaccard": round(jac, 4),
                          "a_logprob": ta["logprob"], "b_logprob": tb["logprob"],
                          "abs_logprob_delta_of_a_choice": (None if delta is None else round(delta, 6)),
                          "a_choice_in_b_topk": ta["token"] in bmap})
    length_mismatch = len(a_toks) != len(b_toks)
    if first_div is None and length_mismatch:
        # One side stopped early. That is a divergence at the shorter length, not a pass.
        first_div = n
    return {
        "n_compared": n,
        "len_a": len(a_toks),
        "len_b": len(b_toks),
        "length_mismatch": length_mismatch,
        "first_divergence": first_div,
        "argmax_agreement": (matches / n) if n else 0.0,
        "mean_jaccard": (sum(jaccards) / len(jaccards)) if jaccards else 0.0,
        "agree_prefix": first_div if first_div is not None else n,
        "positions": positions,
    }


def decode_window(toks, div, after=8):
    """The decoded string up to the divergence plus `after` tokens, for eyeballing."""
    end = len(toks) if div is None else min(len(toks), div + after)
    return "".join(t["token"] or "" for t in toks[:end])


# --------------------------------------------------------------------------- the run

def fetch_side(base, model, prompt, args, endpoint, exchanges, side, label):
    """One request. Appends the raw request/response to `exchanges` no matter what."""
    if endpoint == "chat":
        path, body = "/v1/chat/completions", build_chat_body(
            model, prompt, args.max_tokens, args.top_k, args.think == "on")
    else:
        path, body = "/v1/completions", build_completions_body(
            model, prompt, args.max_tokens, args.top_k)
    t0 = time.time()
    status, raw, err = post_json(base, path, body, timeout=args.timeout, api_key=args.api_key)
    rec = {"prompt": label, "side": side, "endpoint": endpoint,
           "url": base.rstrip("/") + path, "request": body, "http_status": status,
           "transport_error": err, "elapsed_s": round(time.time() - t0, 3)}
    try:
        rec["response"] = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        rec["response_text"] = raw[:20000]
        rec["response"] = None
    exchanges.append(rec)
    if err is not None:
        raise OracleUnavailable("server %s unreachable at %s (%s)" % (side, base, err))
    if status != 200:
        raise OracleUnavailable("server %s returned HTTP %s from %s" % (side, status, path))
    if rec.get("response") is None:
        raise OracleUnavailable("server %s returned non-JSON from %s" % (side, path))
    return normalize_tokens(rec["response"])


def run_oracle(args, out=sys.stdout):
    """Returns (exit_code, report_dict). Pure enough that --selftest drives it in-process."""
    exchanges = []
    report = {
        "config": {"a": args.a, "b": args.b, "model_a": args.model_a, "model_b": args.model_b,
                   "max_tokens": args.max_tokens, "top_k": args.top_k, "think": args.think,
                   "raw": args.raw, "min_agree": args.min_agree,
                   "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        "prompts": [], "exchanges": exchanges, "summary": {},
    }
    endpoints = ["chat"] + (["completions"] if args.raw else [])
    unavailable = None
    failures = 0

    for spec in PROMPTS:
        entry = {"name": spec["name"], "prompt": spec["text"],
                 "expect_substring": spec["expect"], "endpoints": {}}
        report["prompts"].append(entry)
        for endpoint in endpoints:
            print("== %s [%s]" % (spec["name"], endpoint), file=out)
            print("   prompt: %s" % spec["text"], file=out)
            try:
                a_toks = fetch_side(args.a, args.model_a, spec["text"], args,
                                    endpoint, exchanges, "A", spec["name"])
                b_toks = fetch_side(args.b, args.model_b, spec["text"], args,
                                    endpoint, exchanges, "B", spec["name"])
            except OracleUnavailable as exc:
                side = "A" if "server A" in str(exc) or unavailable is None else "B"
                msg = str(exc)
                if msg == "logprobs is null":
                    # Which side? The last exchange we appended is the culprit.
                    side = exchanges[-1]["side"]
                    msg = "server %s does not return logprobs; oracle unavailable" % side
                print("   ORACLE UNAVAILABLE: %s" % msg, file=out)
                entry["endpoints"][endpoint] = {"oracle_unavailable": msg}
                unavailable = unavailable or msg
                continue

            res = compare(a_toks, b_toks)
            res["a_tokens"] = [t["token"] for t in a_toks]
            res["b_tokens"] = [t["token"] for t in b_toks]
            div = res["first_divergence"]
            passed = (res["agree_prefix"] >= args.n_min_agree(res["n_compared"]))
            res["pass"] = passed
            entry["endpoints"][endpoint] = res
            if not passed:
                failures += 1

            print("   first divergence : %s" % ("none" if div is None else div), file=out)
            print("   argmax agreement : %.4f  (%d/%d positions, len A=%d B=%d)"
                  % (res["argmax_agreement"],
                     round(res["argmax_agreement"] * res["n_compared"]),
                     res["n_compared"], res["len_a"], res["len_b"]), file=out)
            print("   mean top-%d Jaccard: %.4f" % (args.top_k, res["mean_jaccard"]), file=out)
            if res["length_mismatch"]:
                print("   NOTE: response lengths differ (%d vs %d) - one side stopped early"
                      % (res["len_a"], res["len_b"]), file=out)
            deltas = [p["abs_logprob_delta_of_a_choice"] for p in res["positions"]
                      if p["abs_logprob_delta_of_a_choice"] is not None]
            absent = sum(1 for p in res["positions"] if not p["a_choice_in_b_topk"])
            if deltas:
                print("   |logprob delta| of A's choice in B's top-%d: max %.4f mean %.4f "
                      "(%d/%d positions where A's choice was absent from B's top-K)"
                      % (args.top_k, max(deltas), sum(deltas) / len(deltas),
                         absent, res["n_compared"]), file=out)
            print("   A: %r" % decode_window(a_toks, div), file=out)
            print("   B: %r" % decode_window(b_toks, div), file=out)
            if spec["expect"]:
                ta = "".join(t["token"] or "" for t in a_toks)
                tb = "".join(t["token"] or "" for t in b_toks)
                print("   coherency (%r present): A=%s B=%s"
                      % (spec["expect"], spec["expect"] in ta, spec["expect"] in tb), file=out)
            print("   verdict: %s" % ("PASS" if passed else "FAIL"), file=out)
            print("", file=out)

    divs, agrees = [], []
    for entry in report["prompts"]:
        res = entry["endpoints"].get("chat") or {}
        if "oracle_unavailable" in res or not res:
            divs.append("n/a")
            agrees.append("n/a")
        else:
            divs.append("none" if res["first_divergence"] is None else str(res["first_divergence"]))
            agrees.append("%.3f" % res["argmax_agreement"])

    if unavailable:
        code = 2
        verdict = "ORACLE UNAVAILABLE"
    elif failures:
        code = 1
        verdict = "DIVERGED"
    else:
        code = 0
        verdict = "AGREED"

    summary = ("LOGIT_DIFF: %d prompts, first divergence at [%s], argmax agreement [%s]"
               % (len(PROMPTS), ", ".join(divs), ", ".join(agrees)))
    report["summary"] = {"line": summary, "verdict": verdict, "exit_code": code,
                         "failing_comparisons": failures,
                         "oracle_unavailable": unavailable}
    print(summary, file=out)
    print("LOGIT_DIFF: %s (exit %d)" % (verdict, code), file=out)
    if unavailable:
        print("LOGIT_DIFF: %s" % unavailable, file=out)
    return code, report


# --------------------------------------------------------------------------- selftest

class _CannedHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):  # keep the selftest output clean
        pass

    def do_POST(self):  # noqa: N802 (http.server API)
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        payload = json.dumps(self.server.responder()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _start_canned(responder):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _CannedHandler)
    srv.responder = responder
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_address[1]


_BASE_TOKENS = ["391", ".", " Seven", "teen", " times", " twenty", "-", "three",
                " is", " three", " hundred", " ninety", "-", "one", ",", " by",
                " the", " distributive", " law", "."]


def _canned(tokens, top_k=5, with_logprobs=True):
    text = "".join(tokens)
    if not with_logprobs:
        return {"id": "canned", "object": "chat.completion",
                "choices": [{"index": 0, "finish_reason": "stop", "logprobs": None,
                             "message": {"role": "assistant", "content": text}}]}
    content = []
    for tok in tokens:
        top = [{"token": tok, "logprob": -0.01}]
        for k in range(1, top_k):
            top.append({"token": "alt%d" % k, "logprob": -1.0 * k - 0.5})
        content.append({"token": tok, "logprob": -0.01, "top_logprobs": top})
    return {"id": "canned", "object": "chat.completion",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "logprobs": {"content": content},
                         "message": {"role": "assistant", "content": text}}]}


def _selftest_args(url_a, url_b):
    ns = argparse.Namespace(a=url_a, b=url_b, model_a="canned-a", model_b="canned-b",
                            max_tokens=64, top_k=5, think="off", raw=False,
                            min_agree="full", timeout=20, api_key=None, out=None)
    ns.n_min_agree = _mk_min_agree(ns.min_agree)
    return ns


def _mk_min_agree(spec):
    if spec == "full":
        return lambda n: n
    val = int(spec)
    return lambda n: min(val, n)


def selftest():
    """Red first: prove the tool reports a planted bug, THEN prove the clean case passes."""
    print("logit_diff --selftest: two in-process http.server instances, canned OpenAI "
          "payloads, no GPU and no network.\n")
    ok = True

    # ---- RED 1: streams that diverge at position 7 must be reported as 7 and must FAIL.
    print("=" * 78)
    print("RED 1/3  planted bug: B's token at position 7 differs -> expect "
          "first_divergence=7 and exit 1")
    print("=" * 78)
    bad = list(_BASE_TOKENS)
    bad[7] = "four"                                   # "three" -> "four": 17*23 becomes wrong
    srv_a, url_a = _start_canned(lambda: _canned(_BASE_TOKENS))
    srv_b, url_b = _start_canned(lambda: _canned(bad))
    code, rep = run_oracle(_selftest_args(url_a, url_b))
    srv_a.shutdown(); srv_b.shutdown()
    got = rep["prompts"][0]["endpoints"]["chat"]["first_divergence"]
    good = (code == 1 and got == 7)
    ok &= good
    print(">>> RED 1/3 %s: exit=%d (want 1), first_divergence=%s (want 7)\n"
          % ("PASS" if good else "FAIL", code, got))

    # ---- RED 2: a server with logprobs: null must be called out, never scored as agreement.
    print("=" * 78)
    print("RED 2/3  planted bug: server A returns logprobs: null -> expect exit 2, "
          "NOT a silent pass")
    print("=" * 78)
    srv_a, url_a = _start_canned(lambda: _canned(_BASE_TOKENS, with_logprobs=False))
    srv_b, url_b = _start_canned(lambda: _canned(_BASE_TOKENS))
    code, rep = run_oracle(_selftest_args(url_a, url_b))
    srv_a.shutdown(); srv_b.shutdown()
    msg = rep["summary"]["oracle_unavailable"] or ""
    good = (code == 2 and "server A does not return logprobs" in msg)
    ok &= good
    print(">>> RED 2/3 %s: exit=%d (want 2), message=%r\n"
          % ("PASS" if good else "FAIL", code, msg))

    # ---- RED 3: unreachable server must be exit 2, not exit 0.
    print("=" * 78)
    print("RED 3/3  planted bug: server B refuses connections -> expect exit 2")
    print("=" * 78)
    srv_a, url_a = _start_canned(lambda: _canned(_BASE_TOKENS))
    srv_dead, url_dead = _start_canned(lambda: _canned(_BASE_TOKENS))
    srv_dead.shutdown(); srv_dead.server_close()      # port is now closed
    code, rep = run_oracle(_selftest_args(url_a, url_dead))
    srv_a.shutdown()
    good = (code == 2)
    ok &= good
    print(">>> RED 3/3 %s: exit=%d (want 2)\n" % ("PASS" if good else "FAIL", code))

    # ---- GREEN: identical streams must pass cleanly.
    print("=" * 78)
    print("GREEN 4/4  clean case: identical streams on both servers -> expect no "
          "divergence and exit 0")
    print("=" * 78)
    srv_a, url_a = _start_canned(lambda: _canned(_BASE_TOKENS))
    srv_b, url_b = _start_canned(lambda: _canned(_BASE_TOKENS))
    code, rep = run_oracle(_selftest_args(url_a, url_b))
    srv_a.shutdown(); srv_b.shutdown()
    res = rep["prompts"][0]["endpoints"]["chat"]
    good = (code == 0 and res["first_divergence"] is None
            and res["argmax_agreement"] == 1.0 and res["mean_jaccard"] == 1.0)
    ok &= good
    print(">>> GREEN 4/4 %s: exit=%d (want 0), first_divergence=%s (want None), "
          "agreement=%.3f, jaccard=%.3f\n"
          % ("PASS" if good else "FAIL", code, res["first_divergence"],
             res["argmax_agreement"], res["mean_jaccard"]))

    print("SELFTEST: %s" % ("ALL 4 CASES BEHAVED AS EXPECTED" if ok else "SOMETHING IS WRONG"))
    return 0 if ok else 1


# --------------------------------------------------------------------------- cli

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()

    ap = argparse.ArgumentParser(
        prog="logit_diff.py",
        description="Position-by-position logprob diff between two OpenAI-compatible servers.")
    ap.add_argument("--a", required=True, help="base URL of server A (Atlas, e.g. http://127.0.0.1:8888)")
    ap.add_argument("--b", required=True, help="base URL of server B (vLLM, e.g. http://127.0.0.1:8000)")
    ap.add_argument("--model-a", required=True)
    ap.add_argument("--model-b", required=True)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--top-k", type=int, default=5, help="top_logprobs K")
    ap.add_argument("--think", choices=["on", "off"], default="off",
                    help="off (default) sends chat_template_kwargs={enable_thinking:false}")
    ap.add_argument("--raw", action="store_true",
                    help="also compare /v1/completions (no chat template)")
    ap.add_argument("--min-agree", default="full",
                    help="'full' (default) or an integer: minimum leading positions that "
                         "must agree for a prompt to pass")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--api-key", default=None, help="sent as Authorization: Bearer <key>")
    ap.add_argument("--out", default=None, help="write the full report (every raw "
                                                "request/response) to this JSON file")
    ap.add_argument("--selftest", action="store_true", help="run offline canned-server tests")
    args = ap.parse_args(argv)
    try:
        args.n_min_agree = _mk_min_agree(args.min_agree)
    except ValueError:
        ap.error("--min-agree must be 'full' or an integer")

    code, report = run_oracle(args)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        print("LOGIT_DIFF: wrote %d exchanges (raw requests + responses) to %s"
              % (len(report["exchanges"]), args.out))
    return code


if __name__ == "__main__":
    sys.exit(main())
