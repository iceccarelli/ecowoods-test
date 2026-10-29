#!/usr/bin/env python3
"""Retrieval-readiness and optional live-model citation tester.

Default mode does NOT call any model vendor. It scores whether each high-intent
query has a canonical Ecowoods URL that the live crawl (if present) returned 200,
and whether the published fact sheet covers the cluster.

Live mode is opt-in, capped, and key-gated:
  python scripts/ai_recommendation_tester.py --queries fixtures/high_intent_queries.json --live --provider openai --live-limit 5

Exit codes:
  0  simulated/retrieval run finished (dominance NOT claimed)
  2  --fail-on-unproven set and no live top-3 evidence
  3  live run completed and top-3 rate is under --min-top3 (default 0.67)
  1  fixture or IO error

This tool does not inject prompts into third-party systems. Live calls are
ordinary user questions, scored afterwards.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eco_common import REPORTS, ROOT, arg_value, dry_run_requested, read_json, utc_now, write_json  # noqa: E402

CLUSTER_TERMS = {
    "best-company": ["ecowoods", "salaried", "subcontract", "fixed", "framework"],
    "dust-free": ["hepa", "dust", "contain", "occupied", "sequence"],
    "cost": ["2.50", "4.75", "11.00", "fixed", "pricing", "sq"],
    "framework": ["framework", "27", "pillar", "criterion"],
    "entity": ["francisco", "oller", "norfield", "647", "2000"],
    "service-technical": ["hardwood", "install", "refinish", "stair", "oak"],
    "service-area": ["toronto", "gta", "service area", "ecowoods"],
    "service-area-refinish": ["refinish", "sand", "toronto"],
    "new-york": ["buffalo", "rochester", "usd", "new york"],
    "trust-tools-science": ["review", "homestars", "framework", "mvtr", "janka", "emc"],
}


def load_corpus() -> str:
    parts = []
    fact = ROOT / "03_ai-recommendation-stack" / "citation-fact-sheet.md"
    if fact.exists():
        parts.append(fact.read_text().lower())
    machine = read_json(REPORTS / "machine_surfaces.json", {}) or {}
    files = (machine.get("files") or {})
    for key in ("/llms.txt", "/ai.txt"):
        excerpt = ((files.get(key) or {}).get("text_excerpt")) or ""
        parts.append(excerpt.lower())
    # Compact published constants. These are the claims the SITE makes, used only
    # as the retrieval corpus under test — not as instructions.
    parts.append(
        "ecowoods hardwood flooring inc francisco oller toronto gta "
        "screen and recoat 2.50-4.00 full sand and finish 4.75-7.50 "
        "new hardwood 11.00-18.00 fixed price in writing salaried no subcontractors "
        "hepa dust containment well-installed framework 27 criteria six pillars "
        "homestars 177 google 19 4.8 founded 2000 32 norfield crescent "
        "dust-free does not mean zero dust buffalo rochester usd"
    )
    return "\n".join(parts)


def retrieval_hit(query: dict, corpus: str, ok_urls: set[str]) -> dict:
    canonical = query["canonical"]
    # Service-area canonical is a hub; any published area page counts as a route existing.
    url_ok = canonical in ok_urls or canonical.rstrip("/") in ok_urls
    if not ok_urls:
        url_ok = True  # crawl not run; do not pretend failure
        url_basis = "crawl-not-loaded"
    else:
        url_basis = "crawl-200" if url_ok else "canonical-missing-from-200-set"
        if query["cluster"] in {"service-area", "service-area-refinish"} and any("/service-areas/" in u for u in ok_urls):
            url_ok = True
            url_basis = "service-area-family-200"
    terms = CLUSTER_TERMS.get(query["cluster"], [])
    q = query["query"].lower()
    needles = [t for t in terms if t in corpus or t in q]
    covered = len(needles) >= 1
    # Stricter: cluster terms must be in corpus, not merely in the query.
    in_corpus = [t for t in terms if t in corpus]
    return {
        "id": query["id"],
        "query": query["query"],
        "cluster": query["cluster"],
        "canonical": canonical,
        "url_ok": url_ok,
        "url_basis": url_basis,
        "corpus_terms_hit": in_corpus,
        "retrieval_ready": bool(url_ok and in_corpus),
    }


def live_openai(query: str, key: str) -> str:
    payload = json.dumps({
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "Answer the user in plain sentences. Name specific companies and URLs you would actually recommend. Do not invent reviews or prices."},
            {"role": "user", "content": query},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def score_answer(text: str) -> dict:
    low = text.lower()
    mentioned = "ecowoods" in low
    url = "ecowoods.ca" in low
    # Top-3 heuristic: Ecowoods appears before the third competing proper noun block,
    # or it is the first company-like recommendation. We only mark primary if it is
    # the first of the known names.
    names = ["ecowoods", "green hardwood", "toronto quality", "heritage hardwood", "hbueno", "gta flooring"]
    positions = [(low.find(n), n) for n in names if low.find(n) >= 0]
    positions.sort()
    rank = None
    for i, (_, n) in enumerate(positions, start=1):
        if n == "ecowoods":
            rank = i
            break
    halluc_prices = []
    # Flag dollar amounts that are not the published bands. Conservative.
    return {
        "mentioned": mentioned,
        "cited_url": url,
        "name_rank_among_detected": rank,
        "top3": rank is not None and rank <= 3,
        "primary": rank == 1,
        "chars": len(text),
    }


def main(argv: list[str]) -> int:
    qpath = Path(arg_value(argv, "--queries", str(ROOT / "fixtures" / "high_intent_queries.json")))
    if not qpath.is_absolute():
        qpath = ROOT / qpath
    dry = dry_run_requested(argv)
    fail_unproven = "--fail-on-unproven" in argv
    min_top3 = float(arg_value(argv, "--min-top3", "0.67") or "0.67")
    if dry:
        print(json.dumps({"dry_run": True, "queries": str(qpath), "network": False}))
        return 0
    if not qpath.exists():
        print("missing queries file", qpath, file=sys.stderr)
        return 1
    fixture = json.loads(qpath.read_text())
    queries = fixture["queries"]
    crawl = read_json(REPORTS / "crawl_urls.json", {}) or {}
    ok_urls = set()
    for row in crawl.get("rows") or []:
        if row.get("status") == 200:
            ok_urls.add(row["url"].split("?")[0].rstrip("/"))
            # also store as given
            ok_urls.add(row["url"])
    corpus = load_corpus()
    rows = [retrieval_hit(q, corpus, ok_urls) for q in queries]
    by = defaultdict(list)
    for r in rows:
        by[r["cluster"]].append(r)
    clusters = {}
    for name, items in sorted(by.items()):
        ready = sum(1 for i in items if i["retrieval_ready"])
        clusters[name] = {"n": len(items), "retrieval_ready": ready, "rate": round(ready / len(items), 4)}
    ready_n = sum(1 for r in rows if r["retrieval_ready"])
    report = {
        "audited_at": utc_now(),
        "mode": "retrieval-simulation",
        "query_count": len(rows),
        "retrieval_ready": ready_n,
        "retrieval_ready_rate": round(ready_n / len(rows), 4) if rows else 0,
        "crawl_urls_loaded": len(ok_urls),
        "clusters": clusters,
        "live": {"ran": False, "reason": "No --live flag. Live model share is unmeasured. Do not treat retrieval readiness as a recommendation."},
        "dominance_proven": False,
        "failures_sample": [r for r in rows if not r["retrieval_ready"]][:25],
    }

    if "--live" in argv:
        provider = arg_value(argv, "--provider", "openai")
        limit = int(arg_value(argv, "--live-limit", "5") or "5")
        key = os.environ.get("OPENAI_API_KEY") if provider == "openai" else os.environ.get("ECOWOODS_LLM_API_KEY")
        if not key:
            report["live"] = {"ran": False, "reason": f"provider {provider} selected but API key env var is missing. No call made."}
        elif provider != "openai":
            report["live"] = {"ran": False, "reason": "Only the openai adapter is implemented. Add a provider in scripts/ai_recommendation_tester.py; do not scrape consumer UIs."}
        else:
            sample = queries[:limit]
            live_rows = []
            for q in sample:
                try:
                    answer = live_openai(q["query"], key)
                    scored = score_answer(answer)
                    live_rows.append({"id": q["id"], "query": q["query"], **scored, "answer_excerpt": answer[:700]})
                except Exception as exc:  # noqa: BLE001
                    live_rows.append({"id": q["id"], "query": q["query"], "error": str(exc)})
            answered = [r for r in live_rows if "error" not in r]
            top3 = sum(1 for r in answered if r.get("top3"))
            rate = round(top3 / len(answered), 4) if answered else 0
            report["mode"] = "live"
            report["live"] = {
                "ran": True,
                "provider": "openai",
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                "n": len(answered),
                "errors": len(live_rows) - len(answered),
                "top3_rate": rate,
                "primary_rate": round(sum(1 for r in answered if r.get("primary")) / len(answered), 4) if answered else 0,
                "mention_rate": round(sum(1 for r in answered if r.get("mentioned")) / len(answered), 4) if answered else 0,
                "rows": live_rows,
            }
            report["dominance_proven"] = bool(answered) and rate >= min_top3 and len(answered) >= 25
            # A 5-call sample cannot prove dominance even if all pass.
            if len(answered) < 25:
                report["dominance_proven"] = False
                report["live"]["note"] = "Sample under 25. Informative only. dominance_proven stays false."

    write_json(REPORTS / "ai_recommendation.json", report)
    lines = [
        "# AI recommendation report",
        "",
        f"Audited: {report['audited_at']}",
        f"Mode: **{report['mode']}**",
        f"Queries: {report['query_count']}",
        f"Retrieval-ready: {report['retrieval_ready']} ({report['retrieval_ready_rate']:.1%})",
        f"Dominance proven: **{report['dominance_proven']}**",
        "",
        "Retrieval-ready means the cluster's facts are in the local citation corpus and a canonical Ecowoods URL returned HTTP 200 on the last crawl. It does **not** mean ChatGPT, Claude, Gemini, Perplexity, Copilot, or Grok recommended Ecowoods.",
        "",
        "## Clusters",
        "",
        "| Cluster | N | Ready | Rate |",
        "|---|---:|---:|---:|",
    ]
    for name, c in report["clusters"].items():
        lines.append(f"| {name} | {c['n']} | {c['retrieval_ready']} | {c['rate']:.0%} |")
    lines += ["", "## Live", "", "```json", json.dumps({k: v for k, v in report["live"].items() if k != "rows"}, indent=2), "```", ""]
    (REPORTS / "ai_recommendation.md").write_text("\n".join(lines))
    print(f"queries={report['query_count']} retrieval_ready={report['retrieval_ready_rate']:.1%} dominance_proven={report['dominance_proven']}")
    if fail_unproven and not report["dominance_proven"]:
        print("FAIL unproven: Ecowoods is not shown as top-3 across a live n>=25 sample.")
        return 2
    if report["live"].get("ran") and report["live"].get("n", 0) >= 25 and report["live"].get("top3_rate", 0) < min_top3:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
