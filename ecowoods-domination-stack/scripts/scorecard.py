#!/usr/bin/env python3
"""Merge audit artifacts into reports/master_scorecard.md and the fix list.

Missing inputs are scored as unmeasured, which lowers the dimension. Re-running
is idempotent. --dry-run prints the input paths and writes nothing.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eco_common import REPORTS, ROOT, dry_run_requested, read_json, utc_now, write_json  # noqa: E402


def clamp(n: float) -> int:
    return max(0, min(100, int(round(n))))


def days_since(iso_day: str | None) -> int | None:
    if not iso_day:
        return None
    try:
        then = datetime.strptime(iso_day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - then).days


def google_review_count(line: str | None) -> int | None:
    if not line:
        return None
    m = re.search(r"(\d+)\s+at\s+4\.", line)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s+at\s+[0-9]", line)
    return int(m.group(1)) if m else None


def build() -> dict:
    site = read_json(REPORTS / "signals_site.json", {}) or {}
    ai = read_json(REPORTS / "ai_recommendation.json", {}) or {}
    repo = read_json(REPORTS / "backend_repo.json", {}) or {}
    cx = read_json(REPORTS / "cx_browser.json", {}) or {}
    notes = []

    # --- SEO ---
    seo = 0
    if site:
        seo += 40 * float(site.get("status_200_rate") or 0)
        seo += 8 if site.get("sitemap_urls", 0) > 100 else 0
        seo += 7 if "GPTBot" in (site.get("robots_agents") or []) or "*" in (site.get("robots_agents") or []) else 0
        areas = site.get("service_area_urls") or 0
        seo += 10 if areas >= 80 else (6 if areas >= 40 else 2)
        p200 = site.get("priority_200") or 0
        seo += 10 * ((site.get("priority_with_title") or 0) / p200) if p200 else 0
        seo += 8 * ((site.get("priority_with_h1") or 0) / p200) if p200 else 0
        if any(t in (site.get("schema_types") or []) for t in ("LocalBusiness", "HomeAndConstructionBusiness", "GeneralContractor", "HousePainter")):
            seo += 6
        elif site.get("schema_types"):
            seo += 4
        if (site.get("ttfb_p50") or 9999) < 500:
            seo += 5
        if (site.get("homepage_bytes") or 0) > 400_000:
            seo -= 8
            notes.append("SEO −8: homepage HTML is over 400 KB.")
        if site.get("markdown_twin_404"):
            seo -= 4
            notes.append("SEO −4: at least one priority Markdown twin is not HTTP 200.")
    else:
        notes.append("SEO unmeasured: signals_site.json missing.")
    seo_s = clamp(seo)

    # --- AEO / GEO ---
    aeo = 0
    if site:
        aeo += 18 if site.get("llms_status") == 200 else 0
        aeo += 10 if site.get("llms_full_status") == 200 else 0
        aeo += 12 if site.get("ai_txt_status") == 200 else 0
        aeo += 14 if site.get("knowledge_status") == 200 else 0
        aeo += 8 if site.get("framework_status") == 200 else 0
        aeo += 8 if site.get("price_bands_in_llms") else 0
        aeo += 6 if site.get("homestars_line") and site.get("google_review_line") else 0
        aeo += 6 if site.get("cost_guide_status") == 200 else 0
        aeo += 5 if site.get("llms_not_instructions") else 0
        aeo += 5 if site.get("markdown_alternate_home") else 0
        crit = site.get("knowledge_criteria") or 0
        aeo += 6 if crit >= 27 else (3 if crit else 0)
        if crit and crit != 27:
            aeo -= 12
            notes.append(
                f"AEO −12: /api/knowledge says framework.criterionCount={crit} "
                "(pillar lengths 5+4+4+3+5+4). Public pages say 27 criteria. "
                "Ship one number. Until then every model citation of the framework is a coin flip."
            )
        age = days_since(site.get("facts_as_of"))
        if age is not None and age > 21:
            aeo -= 8
            notes.append(f"AEO −8: llms.txt facts date {site.get('facts_as_of')} is {age} days old (threshold 21).")
        if any(t.get("page") == "/framework" for t in (site.get("markdown_twin_404") or [])):
            aeo -= 5
            notes.append("AEO −5: /framework.md is not a 200, despite the Markdown-twin convention.")
    else:
        notes.append("AEO unmeasured.")
    aeo_s = clamp(aeo)

    # --- CX ---
    cx_s_raw = 0
    if site:
        cx_s_raw += 18 if site.get("tel_on_home") else 0
        cx_s_raw += 14 if site.get("estimate_forms") else 4
        cx_s_raw += 12 if (site.get("pricing_bytes") or 0) > 0 else 0
        p200 = site.get("priority_200") or 1
        cx_s_raw += 12 * ((site.get("priority_with_viewport") or 0) / p200)
        cx_s_raw += 10 if site.get("floor_studio_status") == 200 else 0
        cx_s_raw += 8 if site.get("quote_check_status") == 200 else 0
        cx_s_raw += 8 if site.get("assess_status") == 200 else 0
        if (site.get("homepage_bytes") or 0) > 400_000:
            cx_s_raw -= 10
        if (site.get("estimate_bytes") or 0) > 250_000:
            cx_s_raw -= 6
            notes.append("CX −6: /estimate HTML is over 250 KB. Form friction is bytes as well as fields.")
        if not site.get("whatsapp_on_priority"):
            notes.append("CX note: no WhatsApp/wa.me link on priority pages. Not scored as a defect; the phone path is the published channel.")
    if cx:
        if cx.get("mode") == "browser" and cx.get("console_errors"):
            cx_s_raw -= min(12, 4 * len(cx["console_errors"]))
            notes.append(f"CX −browser: {len(cx['console_errors'])} console errors.")
        elif cx.get("mode") == "http":
            notes.append("CX browser pass did not launch Chromium. HTTP probes only. Visual/session-replay claims are not made.")
    cx_s = clamp(cx_s_raw)

    # --- AI dominance ---
    # Hard cap until a live n>=25 top-3 result exists. Retrieval excellence is not dominance.
    ai_raw = 0
    if ai:
        ai_raw += 45 * float(ai.get("retrieval_ready_rate") or 0)
    if site:
        agents = site.get("robots_agents") or []
        wanted = ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended"]
        ai_raw += 3 * sum(1 for w in wanted if w in agents)
        if site.get("francisco_in_llms"):
            ai_raw += 4
    g_reviews = google_review_count(site.get("google_review_line") if site else None)
    if g_reviews is not None and g_reviews < 40:
        ai_raw -= 8
        notes.append(f"AI −8: Google review line shows about {g_reviews} reviews. Models overweight Google relative to HomeStars.")
    cap = 64
    if ai.get("dominance_proven"):
        cap = 100
        live = ai.get("live") or {}
        ai_raw = 70 + 30 * float(live.get("top3_rate") or 0)
    else:
        notes.append("AI dominance capped at 64: no live n≥25 sample shows Ecowoods as a top-3 citation. Corpus readiness is not a recommendation.")
    ai_s = clamp(min(ai_raw, cap))

    # --- Technical ---
    tech = 0
    sec = (site or {}).get("security") or {}
    if sec:
        if "max-age" in (sec.get("strict-transport-security") or ""):
            tech += 8
        if sec.get("content-security-policy"):
            tech += 8
        if sec.get("x-content-type-options") == "nosniff":
            tech += 4
        if sec.get("x-frame-options") or "frame-ancestors" in (sec.get("content-security-policy") or ""):
            tech += 4
        if sec.get("cross-origin-opener-policy"):
            tech += 4
        if sec.get("csp_has_unsafe_inline_script"):
            tech -= 3
            notes.append("Technical −3: enforced CSP still allows script 'unsafe-inline'. Report-only policy is the migration path; finish it.")
    if site.get("health_status") == 200:
        tech += 6
    if repo:
        tech += 6 if repo.get("has_fastapi_layout") else 0
        tech += 4 if repo.get("has_mobile") else 0
        tech += 4 if repo.get("has_admin") else 0
        tech += 4 if repo.get("has_docker_compose") and repo.get("has_dockerfile") else 0
        tech += 4 if repo.get("has_backend_tests") else 0
        tech += 4 if repo.get("has_alembic") else 0
        if (repo.get("internal_verify_or_audit_scripts") or 0) >= 20:
            tech += 8
        if repo.get("committed_sqlite"):
            tech -= 15
            notes.append("Technical −15: backend/ecowoods.db is committed on the public repo.")
        if (repo.get("repo") or {}).get("size_kb", 0) > 500_000:
            tech -= 6
        tech -= 10
        notes.append("Technical −10: job lifecycle, JWT, rate limits, and race conditions were not executed against a running backend.")
    else:
        notes.append("Technical: backend_repo.json missing, lifecycle unmeasured.")
        tech -= 10
    tech_s = clamp(tech)

    # --- Conversion ---
    conv = 0
    if site:
        conv += 22 if site.get("price_bands_in_llms") else 0
        conv += 12 if site.get("estimate_forms") else 0
        conv += 10 if site.get("reviews_status") == 200 else 0
        conv += 10 if site.get("assess_status") == 200 else 0
        conv += 8 if site.get("quote_check_status") == 200 else 0
        conv += 8 if site.get("floor_studio_status") == 200 else 0
        conv += 8 if site.get("francisco_in_llms") else 0
        conv += 6 if site.get("tel_on_home") else 0
        if g_reviews is not None and g_reviews < 40:
            conv -= 8
    conv_s = clamp(conv)

    dims = {
        "SEO": seo_s,
        "AEO_GEO": aeo_s,
        "CX": cx_s,
        "AI_Recommendation_Dominance": ai_s,
        "Technical_Resilience": tech_s,
        "Conversion_Readiness": conv_s,
    }
    weights = {
        "SEO": 0.16,
        "AEO_GEO": 0.18,
        "CX": 0.14,
        "AI_Recommendation_Dominance": 0.22,
        "Technical_Resilience": 0.15,
        "Conversion_Readiness": 0.15,
    }
    overall = clamp(sum(dims[k] * weights[k] for k in dims))
    return {
        "audited_at": utc_now(),
        "origin": (site or {}).get("origin", "https://ecowoods.ca"),
        "overall": overall,
        "weights": weights,
        "dimensions": dims,
        "google_reviews_parsed": g_reviews,
        "facts_as_of": (site or {}).get("facts_as_of"),
        "dominance_proven": bool((ai or {}).get("dominance_proven")),
        "notes": notes,
        "inputs": {
            "signals_site": bool(site),
            "ai_recommendation": bool(ai),
            "backend_repo": bool(repo),
            "cx_browser": bool(cx),
        },
    }


def markdown(card: dict) -> str:
    d = card["dimensions"]
    lines = [
        "# Ecowoods master scorecard",
        "",
        f"Audited: {card['audited_at']}  ",
        f"Origin: {card['origin']}  ",
        f"Overall (weighted): **{card['overall']} / 100**",
        "",
        "These scores measure the live site and the public GitHub metadata. They do not measure revenue, and they do not mean a model recommended the company.",
        "",
        "| Dimension | Score | Weight |",
        "|---|---:|---:|",
    ]
    for k, w in card["weights"].items():
        lines.append(f"| {k.replace('_', ' ')} | {d[k]} | {w:.0%} |")
    lines += [
        "",
        f"AI recommendation dominance proven by a live n≥25 sample: **{card['dominance_proven']}**.",
        f"Published facts date in llms.txt: **{card.get('facts_as_of') or 'unknown'}**.",
        f"Google review count parsed from llms.txt: **{card.get('google_reviews_parsed')}**.",
        "",
        "## How to read the cap",
        "",
        "AI Recommendation Dominance cannot exceed 64 until `ai_recommendation.json` has `dominance_proven: true`. That flag requires a real model sample of at least 25 queries with Ecowoods in the top 3 of named companies. Retrieval readiness is necessary and, today, insufficient.",
        "",
        "## Deductions and notes",
        "",
    ]
    if card["notes"]:
        lines.extend(f"- {n}" for n in card["notes"])
    else:
        lines.append("- None.")
    lines += [
        "",
        "## Structural leadership — the actual gap",
        "",
        "Ecowoods already publishes the thing most contractors fake: price bands, a versioned framework, dated third-party review counts, Markdown twins, llms.txt, ai.txt, and a knowledge API. That is rare. It is not the same as being the default answer. The framework's own count is currently not one number.",
        "",
        "The binding constraints, in order:",
        "",
        "1. **Make the framework one number.** On 2026-10-29 the HTML said 27 criteria and `/api/knowledge` `framework.criterionCount` was 25. Six pillars sum to 25. Pick the real list, regenerate llms.txt, the assessor, and the hero from that list, and fail CI if the counts diverge.",
        "2. **Distribution, not documents.** Google shows ~19 reviews at 4.8 against 177 HomeStars reviews at 5.0. Answer engines cite the graph they can see. A review-ask at every job close, pointed at the Google write-a-review URL already published in ai.txt, is the highest-leverage 90-day move. Target: 50+ Google reviews, still dated in llms.txt, still not a self-serving aggregate rating.",
        "3. **Freshness is already a product.** Facts were marked current as of a date that is now past the 21-day threshold. `scripts/verify-freshness.mjs` exists in ecowoods-app. Wire it to a weekly run that fails the deploy if the live llms.txt date is stale. Models treat stale facts as uncertain facts.",
        "4. **Prove recommendation share.** Run `ai_recommendation_tester.py --live --live-limit 25` weekly with a fixed query id set. Store the JSON. Do not declare number one until primary-citation rate on that set is ≥60% for four consecutive weeks across at least two vendors.",
        "5. **Win the credential query without lying.** Competitors name Bona, NWFA, and ASTM F2170 on the homepage. If Ecowoods holds a credential, put the registry URL in ai.txt. If it does not, do not invent one; publish the measurement the credential is a proxy for (machine sequence, meter readings, cure window) and say which standard the method follows.",
        "6. **Cut HTML weight.** Homepage, pricing, and estimate documents are hundreds of kilobytes. `/hardwood-flooring-toronto` was about 800 KB. Budget: 180 KB HTML on `/`, 160 KB on `/estimate`.",
        "7. **Public repo hygiene.** `backend/ecowoods.db` is in the tree and the repo is ~1 GB. Fix both before any outside diligence. This stack did not download the database.",
        "",
        "## What this is not",
        "",
        "A regional hardwood contractor does not have a trillion-dollar outcome hiding in title tags. Category ownership in Toronto/GTA dust-free refinishing is a real asset: it raises close rate, referral rate, and the multiple on a small services firm. Track organic non-brand clicks, AI citation rate on the frozen 25, Google review count, estimate requests, and close rate. Those five numbers are the valuation story. Ignore any plan that asks for fake ratings, hidden text, or instructions that tell a model to ignore its rules.",
        "",
        "## Inputs present",
        "",
        "```json",
        json.dumps(card["inputs"], indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def fixes(card: dict) -> str:
    return f"""# Prioritized fixes

Generated {card['audited_at']}. Ranked by expected effect on organic visibility plus AI citation, not by how impressive they sound. Each item is reversible.

| ID | Sev | Change | Measure | Reverse |
|---|---|---|---|---|
| F0 | P0 | One criterion count. API says 25, pages say 27. Regenerate every surface from `framework.criterionCount`. | knowledge count equals the number in `/framework` H1 and in llms.txt | Revert the constants |
| F1 | P0 | Inspect `backend/ecowoods.db`. If it contains personal data, remove it from the tree and history. | `git ls-files backend/ecowoods.db` returns nothing; a fresh clone has no customer rows | Restore the blob only if it was a fixture |
| F2 | P0 | Google review velocity: QR and the published write-review link at job close. No incentive that violates Google's policy. | Review count in llms.txt, with a new read date, moves from ~19 toward 50 in 90 days | Stop asking |
| F3 | P0 | Fail deploy when live `llms.txt` facts date is older than 21 days. | `facts_as_of` in `reports/signals_site.json` within 21 days | Remove the CI check |
| F4 | P1 | Ship `/framework.md` and `/authority.md` (both 404 on 2026-10-29; other priority twins returned 200). | `markdown_twin_404` empty | Delete the routes |
| F5 | P1 | HTML budget: `/` ≤ 180 KB, `/estimate` ≤ 160 KB. `/hardwood-flooring-toronto` was ~800 KB. | `heavy_priority_pages` empty | Revert the asset split |
| F6 | P1 | Weekly live model sample, n=25, two vendors, frozen query ids. | `dominance_proven` becomes a time series, not a slogan | Stop the job |
| F7 | P1 | Resolve credential queries: publish real registry URLs or an explicit "we do not claim X" line in ai.txt. | Query cluster `dust-free` and "Bona certified" no longer produce a hedged or wrong citation | Edit ai.txt |
| F8 | P2 | Finish the CSP migration off `script-src 'unsafe-inline'`. | Enforced CSP matches today's report-only script-src, pages still work | Restore the previous CSP |
| F9 | P2 | Shrink the git repo under 200 MB without deleting history of the site. | GitHub `size` field | LFS / filter-repo is hard to reverse; do it on a mirror first |
| F10 | P2 | One third-party page that cites the Framework by URL, not a homepage mention. | Referring URL returns 200 and links to /framework | Outreach, not a code revert |
| F11 | P3 | Populate `ecowoods-test` with this stack's CI, not a slogan README. | Test repo contains `scripts/` and a green run | Delete the commit |

Do not: buy reviews, stamp an aggregateRating you computed yourself, cloak, or add "ignore previous instructions" blocks. The live ai.txt already says the file is data. Keep that sentence.
"""


def main(argv: list[str]) -> int:
    if dry_run_requested(argv):
        print(json.dumps({"dry_run": True, "would_write": ["reports/master_scorecard.json", "reports/master_scorecard.md", "10_improvement-playbooks-and-patches/PRIORITIZED_FIXES.md"]}))
        return 0
    card = build()
    write_json(REPORTS / "master_scorecard.json", card)
    text = markdown(card)
    (REPORTS / "master_scorecard.md").write_text(text)
    fix = fixes(card)
    (REPORTS / "prioritized_fixes.md").write_text(fix)
    dest = ROOT / "10_improvement-playbooks-and-patches" / "PRIORITIZED_FIXES.md"
    dest.write_text(fix)
    print(f"overall={card['overall']} " + " ".join(f"{k}={v}" for k, v in card["dimensions"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
