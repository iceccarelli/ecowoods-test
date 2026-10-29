#!/usr/bin/env python3
"""Black-box crawl and machine-surface audit of a live Ecowoods site.

Stdlib only. Idempotent: re-running overwrites reports/crawl_summary.json.
Does not submit forms, does not follow into /admin, does not store full HTML.

Usage:
  python scripts/full_site_audit.py --url https://ecowoods.ca
  python scripts/full_site_audit.py --url https://ecowoods.ca --dry-run
  python scripts/full_site_audit.py --url https://ecowoods.ca --max-urls 40
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eco_common import REPORTS, arg_value, dry_run_requested, fetch, header, utc_now, write_json  # noqa: E402

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
PRIORITY = [
    "/",
    "/pricing",
    "/estimate",
    "/framework",
    "/framework/assess",
    "/services",
    "/services/dust-free-sanding",
    "/services/hardwood-installation",
    "/services/floor-refinishing",
    "/services/floor-restoration",
    "/services/stair-refinishing",
    "/services/custom-inlays",
    "/hardwood-floor-refinishing-toronto",
    "/hardwood-flooring-toronto",
    "/hardwood-stairs-toronto",
    "/hardwood-floor-problems-toronto",
    "/guides/hardwood-flooring-cost-toronto",
    "/guides/dustless-hardwood-refinishing-toronto",
    "/guides/how-to-choose-hardwood-contractor-toronto",
    "/about",
    "/contact",
    "/team",
    "/reviews",
    "/authority",
    "/case-studies",
    "/technical-library",
    "/service-areas",
    "/service-areas/downtown-toronto",
    "/realtors",
    "/commercial",
    "/floor-studio",
    "/quote-check",
    "/press",
]
MACHINE = [
    "/robots.txt",
    "/sitemap.xml",
    "/llms.txt",
    "/llms-full.txt",
    "/ai.txt",
    "/feed.xml",
    "/api/health",
    "/api/knowledge",
    "/api/market",
]
MD_TWINS = [
    "/",
    "/pricing",
    "/framework",
    "/estimate",
    "/services/dust-free-sanding",
    "/guides/hardwood-flooring-cost-toronto",
    "/about",
    "/authority",
    "/reviews",
    "/floor-studio",
]


def parse_sitemap(xml_bytes: bytes) -> list[str]:
    # Some sitemaps ship a BOM or a leading comment.
    text = xml_bytes.decode("utf-8", "replace")
    root = ET.fromstring(text)
    locs = []
    for el in root.iter():
        if el.tag.endswith("loc") and el.text:
            locs.append(el.text.strip())
    return locs


def parse_robots(text: str) -> list[dict]:
    groups: list[dict] = []
    current = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()
        if key == "user-agent":
            if current is None or current["rules"]:
                current = {"agents": [val], "rules": []}
                groups.append(current)
            else:
                current["agents"].append(val)
        elif key in {"allow", "disallow"} and current is not None:
            current["rules"].append({"type": key, "path": val})
        elif key == "sitemap" and current is not None:
            current.setdefault("sitemaps", []).append(val)
    return groups


def rule_decision(group: dict, path: str) -> dict:
    """RFC 9309-ish: longest matching path wins. Also record first-match."""
    matches = []
    first = None
    for rule in group.get("rules", []):
        rule_path = rule["path"]
        if rule_path == "":
            hit = True
        else:
            hit = path.startswith(rule_path)
        if not hit:
            continue
        if first is None:
            first = rule
        matches.append(rule)
    if not matches:
        return {"longest": "allow-by-default", "first": "allow-by-default", "matched": []}
    longest = max(matches, key=lambda r: len(r["path"]))
    return {
        "longest": longest["type"],
        "longest_path": longest["path"],
        "first": first["type"] if first else None,
        "first_path": first["path"] if first else None,
        "matched": matches,
    }


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def analyze_html(url: str, body: bytes) -> dict:
    html = body.decode("utf-8", "replace")
    titles = re.findall(r"(?is)<title[^>]*>(.*?)</title>", html)
    h1s = re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", html)
    h1s = [re.sub(r"\s+", " ", strip_tags(h)).strip() for h in h1s]
    h1s = [h for h in h1s if h]
    desc = re.findall(r'(?is)<meta[^>]+name=["\']description["\'][^>]*>', html)
    desc_content = ""
    if desc:
        m = re.search(r'content=["\'](.*?)["\']', desc[0], re.I)
        desc_content = m.group(1) if m else ""
    canons = re.findall(r'(?is)<link[^>]+rel=["\']canonical["\'][^>]*>', html)
    canon = ""
    if canons:
        m = re.search(r'href=["\'](.*?)["\']', canons[0], re.I)
        canon = m.group(1) if m else ""
    schemas = re.findall(r'(?is)<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html)
    types = []
    for block in schemas:
        types.extend(re.findall(r'"@type"\s*:\s*"([^"]+)"', block))
        types.extend(re.findall(r'"@type"\s*:\s*\[([^\]]+)\]', block))
    flat_types = []
    for t in types:
        if t.startswith('"') or "," in t:
            flat_types.extend(re.findall(r'"([^"]+)"', t))
        else:
            flat_types.append(t)
    viewport = bool(re.search(r'name=["\']viewport["\']', html, re.I))
    md_alt = bool(re.search(r'type=["\']text/markdown["\']', html, re.I))
    text = strip_tags(html)
    return {
        "url": url,
        "title": re.sub(r"\s+", " ", titles[0]).strip() if titles else "",
        "title_len": len(re.sub(r"\s+", " ", titles[0]).strip()) if titles else 0,
        "meta_description_len": len(desc_content),
        "canonical": canon,
        "h1": h1s[:4],
        "h1_count": len(h1s),
        "schema_types": sorted(set(flat_types)),
        "json_ld_blocks": len(schemas),
        "viewport": viewport,
        "markdown_alternate": md_alt,
        "approx_visible_chars": len(text),
        "has_tel": "tel:" in html,
        "has_mailto": "mailto:" in html.lower(),
        "has_whatsapp": bool(re.search(r"wa\.me|whatsapp", html, re.I)),
        "form_count": len(re.findall(r"(?is)<form[\s>]", html)),
        "html_bytes_read": len(body),
    }


def crawl_one(url: str) -> dict:
    res = fetch(url, method="HEAD", limit=0, timeout=15)
    if res["status"] in {0, 400, 403, 405, 501} or (res["status"] == 200 and not header(res, "content-type") and res["error"]):
        res = fetch(url, method="GET", limit=256, timeout=15)
    elif res["status"] == 0:
        res = fetch(url, method="GET", limit=256, timeout=15)
    # Vercel often answers HEAD with 200. If HEAD failed, GET already happened.
    if res["status"] in {403, 405}:
        res = fetch(url, method="GET", limit=256, timeout=15)
    cl = header(res, "content-length")
    return {
        "url": url,
        "status": res["status"],
        "ok": res["status"] == 200,
        "ttfb_ms": res["ttfb_ms"],
        "content_type": header(res, "content-type").split(";")[0],
        "content_length": int(cl) if cl.isdigit() else None,
        "x_robots": header(res, "x-robots-tag"),
        "cache": header(res, "x-vercel-cache") or header(res, "cf-cache-status"),
        "error": res["error"],
    }


def security_snapshot(headers: dict) -> dict:
    wanted = [
        "strict-transport-security",
        "content-security-policy",
        "content-security-policy-report-only",
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "cross-origin-opener-policy",
        "permissions-policy",
        "x-robots-tag",
    ]
    out = {}
    for key in wanted:
        val = headers.get(key, "")
        out[key] = val[:240]
    csp = headers.get("content-security-policy", "")
    out["csp_has_unsafe_inline_script"] = "script-src" in csp and "'unsafe-inline'" in csp
    return out


def main(argv: list[str]) -> int:
    base = (arg_value(argv, "--url", "https://ecowoods.ca") or "https://ecowoods.ca").rstrip("/")
    max_urls = int(arg_value(argv, "--max-urls", "0") or "0")
    dry = dry_run_requested(argv)
    plan = {
        "url": base,
        "priority_pages": len(PRIORITY),
        "machine_files": MACHINE,
        "markdown_twins": MD_TWINS,
        "sitemap_crawl": True,
        "form_posts": 0,
        "dry_run": dry,
    }
    print(json_dumps_line(plan))
    if dry:
        print("dry-run: no network. exiting 0")
        return 0

    REPORTS.mkdir(parents=True, exist_ok=True)
    machine = {}
    for path in MACHINE:
        limit = 900_000 if path in {"/llms-full.txt", "/api/knowledge", "/sitemap.xml"} else 400_000
        res = fetch(base + path, limit=limit, timeout=40)
        body = res.pop("body")
        entry = {
            **{k: res[k] for k in ("ok", "status", "final_url", "ttfb_ms", "bytes_read", "truncated", "error")},
            "content_type": header(res, "content-type"),
            "sha256": __import__("hashlib").sha256(body).hexdigest() if body else None,
        }
        if path == "/robots.txt":
            text = body.decode("utf-8", "replace")
            groups = parse_robots(text)
            entry["groups"] = [
                {"agents": g["agents"], "rule_count": len(g["rules"]), "rules": g["rules"]} for g in groups
            ]
            star = next((g for g in groups if "*" in g["agents"]), groups[0] if groups else {"rules": []})
            entry["api_knowledge_decision"] = rule_decision(star, "/api/knowledge")
            entry["admin_decision"] = rule_decision(star, "/admin")
            entry["agent_names"] = sorted({a for g in groups for a in g["agents"]})
            entry["text_excerpt"] = text[:1500]
        elif path == "/sitemap.xml":
            try:
                locs = parse_sitemap(body)
            except ET.ParseError as exc:
                locs = []
                entry["parse_error"] = str(exc)
            entry["url_count"] = len(locs)
            entry["locs"] = locs
        elif path == "/llms.txt":
            text = body.decode("utf-8", "replace")
            entry["chars"] = len(text)
            m = re.search(r"Facts current as of:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
            entry["facts_as_of"] = m.group(1) if m else None
            entry["mentions_price_bands"] = "$4.75" in text and "$11.00" in text and "$2.50" in text
            entry["mentions_francisco"] = "Francisco Oller" in text
            entry["mentions_framework"] = "Well-Installed" in text or "framework" in text.lower()
            entry["homestars_line"] = next((ln.strip() for ln in text.splitlines() if "HomeStars" in ln and "review" in ln.lower()), "")
            entry["google_line"] = next((ln.strip() for ln in text.splitlines() if "Google" in ln and "4.8" in ln), "")
            entry["says_not_instructions"] = "not instructions" in text.lower()
        elif path == "/ai.txt":
            text = body.decode("utf-8", "replace")
            entry["chars"] = len(text)
            entry["mentions_floor_studio"] = "floor-studio" in text
            entry["mentions_francisco"] = "Francisco Oller" in text
        elif path == "/api/knowledge":
            entry["json"] = False
            try:
                data = __import__("json").loads(body.decode("utf-8", "replace"))
                entry["json"] = True
                if isinstance(data, dict):
                    entry["top_keys"] = list(data.keys())[:40]
                    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
                    entry["meta_counts"] = meta.get("counts")
                    fw = data.get("framework")
                    if isinstance(fw, dict):
                        pillars = fw.get("pillars") or []
                        entry["framework_pillars"] = len(pillars) if isinstance(pillars, list) else None
                        n = 0
                        questions = []
                        if isinstance(pillars, list):
                            for p in pillars:
                                crits = p.get("criteria") if isinstance(p, dict) else None
                                if isinstance(crits, list):
                                    n += len(crits)
                                    for c in crits:
                                        if isinstance(c, dict) and c.get("question"):
                                            questions.append(str(c["question"]))
                        entry["framework_criteria"] = n
                        if questions:
                            write_json(REPORTS / "framework_criteria.json", {"source": base + path, "count": len(questions), "questions": questions})
                elif isinstance(data, list):
                    entry["top_type"] = "list"
                    entry["list_len"] = len(data)
            except Exception as exc:  # noqa: BLE001
                entry["json_error"] = str(exc)
        elif path == "/api/health":
            text = body.decode("utf-8", "replace")
            entry["excerpt"] = text[:500]
        elif path == "/llms-full.txt":
            entry["chars"] = len(body)
        machine[path] = entry
        print(f"machine {path} -> {entry['status']} {entry['bytes_read']}B")

    locs = machine.get("/sitemap.xml", {}).get("locs") or []
    if max_urls:
        locs = locs[:max_urls]
    rows = []
    if locs:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futs = {pool.submit(crawl_one, u): u for u in locs}
            for fut in as_completed(futs):
                row = fut.result()
                rows.append(row)
                if len(rows) % 40 == 0:
                    print(f"crawled {len(rows)}/{len(locs)}")
    rows.sort(key=lambda r: r["url"])

    pages = []
    for path in PRIORITY:
        res = fetch(base + path, limit=700_000, timeout=30)
        body = res.pop("body")
        analysis = analyze_html(base + path, body) if res["status"] == 200 and b"<html" in body[:500].lower() or (res["status"] == 200 and b"<" in body[:200]) else {"url": base + path, "skipped": True}
        if res["status"] == 200 and isinstance(body, (bytes, bytearray)) and body.strip().startswith(b"<"):
            analysis = analyze_html(base + path, body)
        cl = header(res, "content-length")
        pages.append({
            "path": path,
            "status": res["status"],
            "ttfb_ms": res["ttfb_ms"],
            "bytes_read": res["bytes_read"],
            "content_length": int(cl) if str(cl).isdigit() else res["bytes_read"],
            "truncated": res["truncated"],
            "error": res["error"],
            "security": security_snapshot(res["headers"]) if path == "/" else None,
            "analysis": analysis,
        })
        print(f"page {path} -> {res['status']} {res['bytes_read']}B h1={analysis.get('h1_count')}")

    twins = []
    for path in MD_TWINS:
        target = base + ("/index.md" if path == "/" else path + ".md")
        res = fetch(target, limit=1500, timeout=20)
        twins.append({"page": path, "md_url": target, "status": res["status"], "content_type": header(res, "content-type"), "error": res["error"]})
        print(f"md {target} -> {res['status']}")

    ok = sum(1 for r in rows if r["status"] == 200)
    statuses = Counter(str(r["status"]) for r in rows)
    ttfbs = sorted(r["ttfb_ms"] for r in rows if r["status"] == 200)
    def pct(p):
        if not ttfbs:
            return None
        i = min(len(ttfbs) - 1, int(round((p / 100) * (len(ttfbs) - 1))))
        return ttfbs[i]
    prefixes = Counter()
    for r in rows:
        parts = urlparse(r["url"]).path.strip("/").split("/")
        prefixes[parts[0] if parts and parts[0] else "/"] += 1
    failures = [r for r in rows if r["status"] != 200]

    home = next((p for p in pages if p["path"] == "/"), {})
    summary = {
        "audited_at": utc_now(),
        "origin": base,
        "sitemap_urls": len(rows),
        "status_counts": dict(statuses),
        "status_200_rate": round(ok / len(rows), 4) if rows else 0,
        "ttfb_ms": {"p50": pct(50), "p90": pct(90), "max": ttfbs[-1] if ttfbs else None},
        "prefix_counts": dict(prefixes),
        "service_area_urls": sum(1 for r in rows if "/service-areas/" in r["url"]),
        "failures": failures[:80],
        "priority_pages": [
            {
                "path": p["path"],
                "status": p["status"],
                "bytes": p["content_length"],
                "ttfb_ms": p["ttfb_ms"],
                "title": (p.get("analysis") or {}).get("title"),
                "h1_count": (p.get("analysis") or {}).get("h1_count"),
                "canonical": (p.get("analysis") or {}).get("canonical"),
                "schema_types": (p.get("analysis") or {}).get("schema_types"),
                "viewport": (p.get("analysis") or {}).get("viewport"),
                "markdown_alternate": (p.get("analysis") or {}).get("markdown_alternate"),
                "form_count": (p.get("analysis") or {}).get("form_count"),
                "has_tel": (p.get("analysis") or {}).get("has_tel"),
                "has_whatsapp": (p.get("analysis") or {}).get("has_whatsapp"),
            }
            for p in pages
        ],
        "markdown_twins": twins,
        "homepage_security": home.get("security"),
        "homepage_bytes": home.get("content_length"),
        "machine_status": {k: {"status": v.get("status"), "bytes_read": v.get("bytes_read"), "error": v.get("error")} for k, v in machine.items()},
    }
    # Drop bulky loc list from the stored machine file (kept in summary via crawl rows).
    machine_store = {}
    for k, v in machine.items():
        v = dict(v)
        if k == "/sitemap.xml":
            v["sample_locs"] = (v.get("locs") or [])[:25]
            v.pop("locs", None)
        machine_store[k] = v
    write_json(REPORTS / "machine_surfaces.json", {"audited_at": utc_now(), "origin": base, "files": machine_store})
    write_json(REPORTS / "crawl_summary.json", summary)
    write_json(REPORTS / "crawl_urls.json", {"audited_at": utc_now(), "rows": rows})
    # signals for the scorecard
    llms = machine.get("/llms.txt", {})
    know = machine.get("/api/knowledge", {})
    robots = machine.get("/robots.txt", {})
    priority_ok = [p for p in pages if p["status"] == 200]
    schema_union = sorted({t for p in pages for t in ((p.get("analysis") or {}).get("schema_types") or [])})
    signals = {
        "audited_at": utc_now(),
        "origin": base,
        "sitemap_urls": len(rows),
        "status_200_rate": summary["status_200_rate"],
        "non_200": len(failures),
        "ttfb_p50": summary["ttfb_ms"]["p50"],
        "service_area_urls": summary["service_area_urls"],
        "homepage_bytes": home.get("content_length") or 0,
        "estimate_bytes": next((p["content_length"] for p in pages if p["path"] == "/estimate"), 0),
        "pricing_bytes": next((p["content_length"] for p in pages if p["path"] == "/pricing"), 0),
        "heavy_priority_pages": [
            {"path": p["path"], "bytes": p["content_length"]}
            for p in pages
            if (p["content_length"] or 0) > 250_000
        ],
        "priority_200_rate": round(len(priority_ok) / len(pages), 4) if pages else 0,
        "priority_with_title": sum(1 for p in priority_ok if (p.get("analysis") or {}).get("title")),
        "priority_with_h1": sum(1 for p in priority_ok if (p.get("analysis") or {}).get("h1_count")),
        "priority_with_viewport": sum(1 for p in priority_ok if (p.get("analysis") or {}).get("viewport")),
        "priority_count": len(pages),
        "priority_200": len(priority_ok),
        "schema_types": schema_union,
        "markdown_twin_404": [t for t in twins if t["status"] != 200],
        "markdown_alternate_home": (home.get("analysis") or {}).get("markdown_alternate"),
        "facts_as_of": llms.get("facts_as_of"),
        "llms_status": llms.get("status"),
        "llms_full_status": machine.get("/llms-full.txt", {}).get("status"),
        "llms_full_bytes": machine.get("/llms-full.txt", {}).get("bytes_read"),
        "ai_txt_status": machine.get("/ai.txt", {}).get("status"),
        "knowledge_status": know.get("status"),
        "knowledge_bytes": know.get("bytes_read"),
        "knowledge_criteria": know.get("framework_criteria"),
        "knowledge_pillars": know.get("framework_pillars"),
        "health_status": machine.get("/api/health", {}).get("status"),
        "market_status": machine.get("/api/market", {}).get("status"),
        "robots_agents": robots.get("agent_names"),
        "api_knowledge_robots": robots.get("api_knowledge_decision"),
        "price_bands_in_llms": llms.get("mentions_price_bands"),
        "francisco_in_llms": llms.get("mentions_francisco"),
        "llms_not_instructions": llms.get("says_not_instructions"),
        "google_review_line": llms.get("google_line"),
        "homestars_line": llms.get("homestars_line"),
        "security": home.get("security"),
        "estimate_forms": (next((p for p in pages if p["path"] == "/estimate"), {}).get("analysis") or {}).get("form_count"),
        "estimate_tel": (next((p for p in pages if p["path"] == "/estimate"), {}).get("analysis") or {}).get("has_tel"),
        "whatsapp_on_priority": any((p.get("analysis") or {}).get("has_whatsapp") for p in pages),
        "tel_on_home": (home.get("analysis") or {}).get("has_tel"),
        "floor_studio_status": next((p["status"] for p in pages if p["path"] == "/floor-studio"), 0),
        "quote_check_status": next((p["status"] for p in pages if p["path"] == "/quote-check"), 0),
        "framework_status": next((p["status"] for p in pages if p["path"] == "/framework"), 0),
        "assess_status": next((p["status"] for p in pages if p["path"] == "/framework/assess"), 0),
        "reviews_status": next((p["status"] for p in pages if p["path"] == "/reviews"), 0),
        "cost_guide_status": next((p["status"] for p in pages if p["path"] == "/guides/hardwood-flooring-cost-toronto"), 0),
    }
    write_json(REPORTS / "signals_site.json", signals)
    print(f"wrote {REPORTS/'crawl_summary.json'} urls={len(rows)} 200_rate={summary['status_200_rate']}")
    return 0 if summary["status_200_rate"] >= 0.95 or not rows else 1


def json_dumps_line(obj) -> str:
    import json
    return json.dumps(obj)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
