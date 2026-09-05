#!/usr/bin/env python3
"""Turn two ladder JSONs into the campaign's Pareto table.

Input is two files written by `bench/ladder38/harness_w55_conc_ladder.py` --
one per engine. Output is a markdown table and a JSON twin: per concurrency,
tok/s, TTFT p50/p99, TPOT p50, the Atlas/vLLM ratio, and WIN, TIE or LOSS.

★ The fairness oracle is the reason this exists rather than a spreadsheet.
Before it compares anything it refuses two files whose workload axes disagree:
isl, osl, temperature, seed, chat_template_kwargs. That failure is otherwise
SILENT -- two legs run days apart with one flag changed produce a table that
looks exactly like a valid one, and the only trace is a number that seems
surprising. `bench/ladder38/published.json` carries a whole `harness_shas`
block arguing after the fact that two legs really were equivalent; refusing up
front is cheaper than arguing later.

Usage:
  compare.py --atlas ATLAS.json --vllm VLLM.json [--out-md F] [--out-json F]
  compare.py --selftest
"""

import argparse
import copy
import json
import pathlib
import statistics
import sys

# The workload axes that must agree for two runs to be comparable at all.
#
# Every one of these changes what was measured, not how well it went. Anything
# NOT in this list -- label, url, model, driver sha, timestamps -- may differ:
# the two legs are two engines, so they are supposed to differ there.
PARITY_KEYS = ("isl", "osl", "temperature", "seed", "chat_template_kwargs")


class Mismatch(Exception):
    """The two files do not describe the same workload."""


def load(path):
    d = json.loads(pathlib.Path(path).read_text())
    if "rungs" not in d:
        raise Mismatch(f"{path}: no 'rungs' -- not a harness_w55_conc_ladder.py output")
    return d


def assert_comparable(a, b, a_name="atlas", b_name="vllm"):
    """Refuse the comparison unless every parity axis matches.

    A MISSING key is a mismatch too, not a pass. An older harness that did not
    record `chat_template_kwargs` cannot be shown to have disabled thinking,
    and "we probably did" is exactly the claim this campaign cannot make.
    """
    problems = []
    for key in PARITY_KEYS:
        if key not in a or key not in b:
            problems.append(
                f"{key}: {a_name}={a.get(key, '<absent>')!r} {b_name}={b.get(key, '<absent>')!r} "
                "(absent is not a match -- the run cannot show it used this value)"
            )
        elif a[key] != b[key]:
            problems.append(f"{key}: {a_name}={a[key]!r} vs {b_name}={b[key]!r}")
    if problems:
        raise Mismatch(
            "refusing to compare two runs that did not measure the same workload:\n  - "
            + "\n  - ".join(problems)
        )


def rung_stats(rung):
    """One rung's headline numbers, aggregated over its timed reps.

    tok/s comes from the harness's own mean over the rep series. The latency
    percentiles are per-rep, so they are averaged across reps -- a median of
    medians would hide a rep that was uniformly slow, which on a shared box is
    the reading that matters.
    """
    reps = rung.get("reps") or []

    def mean_of(key):
        vals = [r[key] for r in reps if r.get(key) is not None]
        return statistics.fmean(vals) if vals else None

    return {
        "concurrency": rung["concurrency"],
        "tok_s": rung.get("tok_s_mean"),
        "ttft_p50_ms": mean_of("ttft_p50_ms"),
        "ttft_p99_ms": mean_of("ttft_p99_ms"),
        "tpot_p50_ms": mean_of("tpot_p50_ms"),
        "errors": rung.get("errors_total", 0),
    }


def compare(atlas, vllm):
    assert_comparable(atlas, vllm)
    atlas_by_c = {r["concurrency"]: rung_stats(r) for r in atlas["rungs"]}
    vllm_by_c = {r["concurrency"]: rung_stats(r) for r in vllm["rungs"]}
    rows = []
    for concurrency in sorted(atlas_by_c.keys() | vllm_by_c.keys()):
        a = atlas_by_c.get(concurrency)
        b = vllm_by_c.get(concurrency)
        if a is None or b is None:
            # Reported, not dropped: a rung one engine ran and the other did
            # not is a hole in the campaign, and a table that silently omits it
            # reads as complete.
            rows.append({**{f"atlas_{k}": v for k, v in (a or {}).items()},
                         **{f"vllm_{k}": v for k, v in (b or {}).items()},
                         "concurrency": concurrency, "verdict": "NO-PAIR"})
            continue
        ratio = (a["tok_s"] / b["tok_s"]) if (a["tok_s"] and b["tok_s"]) else None
        rows.append({
            "concurrency": a["concurrency"],
            "atlas_tok_s": a["tok_s"], "vllm_tok_s": b["tok_s"],
            "atlas_ttft_p50_ms": a["ttft_p50_ms"], "vllm_ttft_p50_ms": b["ttft_p50_ms"],
            "atlas_ttft_p99_ms": a["ttft_p99_ms"], "vllm_ttft_p99_ms": b["ttft_p99_ms"],
            "atlas_tpot_p50_ms": a["tpot_p50_ms"], "vllm_tpot_p50_ms": b["tpot_p50_ms"],
            "atlas_errors": a["errors"], "vllm_errors": b["errors"],
            "ratio": ratio,
            # Throughput decides the label because that is what the campaign's
            # scoreboard is scored on; the latency columns sit beside it so a
            # win bought by a TTFT regression is visible in the same row rather
            # than in a footnote.
            "verdict": ("TIE" if ratio == 1.0 else
                        "WIN" if ratio is not None and ratio > 1.0 else "LOSS"),
        })
    return {
        "schema": 1,
        "workload": {k: atlas[k] for k in PARITY_KEYS if k in atlas},
        "atlas_label": atlas.get("label"), "vllm_label": vllm.get("label"),
        "atlas_model": atlas.get("model"), "vllm_model": vllm.get("model"),
        "rows": rows,
        "rungs_won": sum(1 for r in rows if r["verdict"] == "WIN"),
        "rungs_compared": sum(1 for r in rows if r["verdict"] in ("WIN", "TIE", "LOSS")),
    }


def to_markdown(result):
    w = result["workload"]
    num = lambda v, p=2: "--" if v is None else f"{v:.{p}f}"
    lines = [
        f"### ISL {w.get('isl')} / OSL {w.get('osl')} "
        f"(temp {w.get('temperature')}, seed {w.get('seed')})",
        "",
        "| C | Atlas tok/s | vLLM tok/s | ratio | Atlas TTFT p50/p99 ms | vLLM TTFT p50/p99 ms "
        "| Atlas TPOT p50 ms | vLLM TPOT p50 ms | rung |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in result["rows"]:
        if r["verdict"] == "NO-PAIR":
            lines.append(f"| {r['concurrency']} | {num(r.get('atlas_tok_s'))} "
                         f"| {num(r.get('vllm_tok_s'))} | -- | -- "
                         "| -- | -- | -- | **NO-PAIR** |")
            continue
        lines.append(
            f"| {r['concurrency']} | {num(r['atlas_tok_s'])} | {num(r['vllm_tok_s'])} "
            f"| {num(r['ratio'])}x "
            f"| {num(r['atlas_ttft_p50_ms'], 0)} / {num(r['atlas_ttft_p99_ms'], 0)} "
            f"| {num(r['vllm_ttft_p50_ms'], 0)} / {num(r['vllm_ttft_p99_ms'], 0)} "
            f"| {num(r['atlas_tpot_p50_ms'])} | {num(r['vllm_tpot_p50_ms'])} "
            f"| **{r['verdict']}** |"
        )
    lines += ["", f"{result['rungs_won']}/{result['rungs_compared']} rungs won.", ""]
    return "\n".join(lines)


def selftest():
    """Validate the instrument against three known cases.

    The matched pair must produce the arithmetic the fixtures were built to
    give (Atlas 2x at C=1, 0.5x at C=16 -- one WIN and one LOSS, so a table
    that reported everything as a win would be caught). The mismatched pair
    must be REFUSED: `fixtures/vllm_tiny_mismatched.json` differs from the
    Atlas fixture in exactly one axis, `osl`, which is the shape of the mistake
    that actually happens -- a re-run with one flag edited. And the third case
    is a file with no `chat_template_kwargs` at all, which must also be refused
    rather than assumed equivalent.
    """
    here = pathlib.Path(__file__).parent / "fixtures"
    atlas = load(here / "atlas_tiny.json")
    result = compare(atlas, load(here / "vllm_tiny.json"))
    print(to_markdown(result))
    assert result["rows"][0]["ratio"] == 2.0, result["rows"][0]
    assert result["rows"][0]["verdict"] == "WIN", result["rows"][0]
    assert result["rows"][1]["ratio"] == 0.5, result["rows"][1]
    assert result["rows"][1]["verdict"] == "LOSS", result["rows"][1]
    assert result["rungs_won"] == 1 and result["rungs_compared"] == 2, result
    assert result["rows"][0]["atlas_ttft_p50_ms"] == 100.0, result["rows"][0]

    for bad, expect in (("vllm_tiny_mismatched.json", "osl"),
                        ("vllm_tiny_no_thinking_key.json", "chat_template_kwargs")):
        try:
            compare(atlas, load(here / bad))
        except Mismatch as e:
            assert expect in str(e), f"{bad}: refusal did not name {expect}: {e}"
            print(f"REFUSED {bad}: {str(e).splitlines()[-1].strip()}")
        else:
            raise AssertionError(f"{bad} must be refused, not compared")
    # Arithmetic identity and rung-set union are independent of GPU timings.
    failures = []
    tied = compare(atlas, copy.deepcopy(atlas))
    if not (all(r["ratio"] == 1.0 and r["verdict"] == "TIE" for r in tied["rows"])
            and tied["rungs_compared"] == 2 and tied["rungs_won"] == 0):
        failures.append("identity oracle: A/A ratio 1.0 must be TIE and count as compared")
    for name, a, b in (("atlas-only", atlas, {**atlas, "rungs": atlas["rungs"][:1]}),
                       ("vllm-only", {**atlas, "rungs": atlas["rungs"][:1]}, atlas)):
        unpaired = compare(a, b)
        rows = {r["concurrency"]: r for r in unpaired["rows"]}
        if 16 not in rows or rows[16]["verdict"] != "NO-PAIR":
            failures.append(f"rung-union oracle: {name} C=16 must remain NO-PAIR")
        elif name == "vllm-only" and "200.00" not in to_markdown(unpaired):
            failures.append("rung-union oracle: vllm-only throughput must render in its column")
    for failure in failures:
        print("FAIL:", failure)
    assert not failures, "; ".join(failures)
    print("SELFTEST OK: arithmetic, parity refusal, A/A identity and symmetric rung union")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--atlas")
    ap.add_argument("--vllm")
    ap.add_argument("--out-md")
    ap.add_argument("--out-json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0
    if not a.atlas or not a.vllm:
        ap.error("--atlas and --vllm are required (or pass --selftest)")

    try:
        result = compare(load(a.atlas), load(a.vllm))
    except Mismatch as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    md = to_markdown(result)
    print(md)
    if a.out_md:
        pathlib.Path(a.out_md).write_text(md + "\n")
    if a.out_json:
        pathlib.Path(a.out_json).write_text(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
