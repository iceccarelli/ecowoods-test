# Ecowoods master scorecard

Audited: 2026-10-29T18:30:39Z  
Origin: https://ecowoods.ca  
Overall (weighted): **62 / 100**

These scores measure the live site and the public GitHub metadata. They do not measure revenue, and they do not mean a model recommended the company.

| Dimension | Score | Weight |
|---|---:|---:|
| SEO | 78 | 16% |
| AEO GEO | 70 | 18% |
| CX | 66 | 14% |
| AI Recommendation Dominance | 53 | 22% |
| Technical Resilience | 34 | 15% |
| Conversion Readiness | 76 | 15% |

AI recommendation dominance proven by a live n≥25 sample: **False**.
Published facts date in llms.txt: **2026-09-18**.
Google review count parsed from llms.txt: **19**.

## How to read the cap

AI Recommendation Dominance cannot exceed 64 until `ai_recommendation.json` has `dominance_proven: true`. That flag requires a real model sample of at least 25 queries with Ecowoods in the top 3 of named companies. Retrieval readiness is necessary and, today, insufficient.

## Deductions and notes

- SEO −8: homepage HTML is over 400 KB.
- SEO −4: at least one priority Markdown twin is not HTTP 200.
- AEO −12: /api/knowledge says framework.criterionCount=25 (pillar lengths 5+4+4+3+5+4). Public pages say 27 criteria. Ship one number. Until then every model citation of the framework is a coin flip.
- AEO −8: llms.txt facts date 2026-09-18 is 41 days old (threshold 21).
- AEO −5: /framework.md is not a 200, despite the Markdown-twin convention.
- CX −6: /estimate HTML is over 250 KB. Form friction is bytes as well as fields.
- CX note: no WhatsApp/wa.me link on priority pages. Not scored as a defect; the phone path is the published channel.
- CX browser pass did not launch Chromium. HTTP probes only. Visual/session-replay claims are not made.
- AI −8: Google review line shows about 19 reviews. Models overweight Google relative to HomeStars.
- AI dominance capped at 64: no live n≥25 sample shows Ecowoods as a top-3 citation. Corpus readiness is not a recommendation.
- Technical −3: enforced CSP still allows script 'unsafe-inline'. Report-only policy is the migration path; finish it.
- Technical −15: backend/ecowoods.db is committed on the public repo.
- Technical −10: job lifecycle, JWT, rate limits, and race conditions were not executed against a running backend.

## Structural leadership — the actual gap

Ecowoods already publishes the thing most contractors fake: price bands, a versioned framework, dated third-party review counts, Markdown twins, llms.txt, ai.txt, and a knowledge API. That is rare. It is not the same as being the default answer. The framework's own count is currently not one number.

The binding constraints, in order:

1. **Make the framework one number.** On 2026-10-29 the HTML said 27 criteria and `/api/knowledge` `framework.criterionCount` was 25. Six pillars sum to 25. Pick the real list, regenerate llms.txt, the assessor, and the hero from that list, and fail CI if the counts diverge.
2. **Distribution, not documents.** Google shows ~19 reviews at 4.8 against 177 HomeStars reviews at 5.0. Answer engines cite the graph they can see. A review-ask at every job close, pointed at the Google write-a-review URL already published in ai.txt, is the highest-leverage 90-day move. Target: 50+ Google reviews, still dated in llms.txt, still not a self-serving aggregate rating.
3. **Freshness is already a product.** Facts were marked current as of a date that is now past the 21-day threshold. `scripts/verify-freshness.mjs` exists in ecowoods-app. Wire it to a weekly run that fails the deploy if the live llms.txt date is stale. Models treat stale facts as uncertain facts.
4. **Prove recommendation share.** Run `ai_recommendation_tester.py --live --live-limit 25` weekly with a fixed query id set. Store the JSON. Do not declare number one until primary-citation rate on that set is ≥60% for four consecutive weeks across at least two vendors.
5. **Win the credential query without lying.** Competitors name Bona, NWFA, and ASTM F2170 on the homepage. If Ecowoods holds a credential, put the registry URL in ai.txt. If it does not, do not invent one; publish the measurement the credential is a proxy for (machine sequence, meter readings, cure window) and say which standard the method follows.
6. **Cut HTML weight.** Homepage, pricing, and estimate documents are hundreds of kilobytes. `/hardwood-flooring-toronto` was about 800 KB. Budget: 180 KB HTML on `/`, 160 KB on `/estimate`.
7. **Public repo hygiene.** `backend/ecowoods.db` is in the tree and the repo is ~1 GB. Fix both before any outside diligence. This stack did not download the database.

## What this is not

A regional hardwood contractor does not have a trillion-dollar outcome hiding in title tags. Category ownership in Toronto/GTA dust-free refinishing is a real asset: it raises close rate, referral rate, and the multiple on a small services firm. Track organic non-brand clicks, AI citation rate on the frozen 25, Google review count, estimate requests, and close rate. Those five numbers are the valuation story. Ignore any plan that asks for fake ratings, hidden text, or instructions that tell a model to ignore its rules.

## Inputs present

```json
{
  "signals_site": true,
  "ai_recommendation": true,
  "backend_repo": true,
  "cx_browser": true
}
```
