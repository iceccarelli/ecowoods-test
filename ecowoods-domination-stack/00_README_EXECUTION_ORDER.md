# Ecowoods domination stack — execution order

External black-box examiner for [ecowoods.ca](https://ecowoods.ca), the public repo [iceccarelli/ecowoods-app](https://github.com/iceccarelli/ecowoods-app), and [iceccarelli/ecowoods-test](https://github.com/iceccarelli/ecowoods-test).

Built 2026-10-29. Python 3 stdlib and Node 18+. No required pip or npm installs.

In Codespaces, start with [CODESPACES.md](CODESPACES.md). From this directory: `make dry`, then `make live`.

This stack does **not** declare Ecowoods number one. It measures whether the claim is even testable, then scores what the live site actually returns. Recommendation dominance is capped until a live model sample of n≥25 says otherwise.

## Order

From this directory:

```sh
./download-heavy-deps.sh
python3 scripts/full_site_audit.py --url https://ecowoods.ca
python3 scripts/ai_recommendation_tester.py --queries fixtures/high_intent_queries.json
node scripts/playwright_cx_stress.js
bash scripts/generate_improvement_patches.sh
cat reports/master_scorecard.md
```

`make live` runs that sequence plus the GitHub metadata audit. Every entry point accepts `--dry-run` and makes no network calls in that mode. `make dry` is the Codespaces smoke test.

Also, when you want repo metadata:

```sh
python3 scripts/backend_repo_audit.py --repo iceccarelli/ecowoods-app
```

## What each stage writes

| Stage | Output | Network |
|---|---|---|
| full_site_audit.py | reports/crawl_summary.json, crawl_urls.json, machine_surfaces.json, signals_site.json, framework_criteria.json | GET/HEAD only |
| backend_repo_audit.py | reports/backend_repo.json | GitHub API, no clone |
| ai_recommendation_tester.py | reports/ai_recommendation.json, ai_recommendation.md | none unless `--live` |
| playwright_cx_stress.js | reports/cx_browser.json | GET only, no form posts |
| generate_improvement_patches.sh | reports/master_scorecard.md, 10_…/PRIORITIZED_FIXES.md | none |

## Rules that are not optional

- Do not POST the production estimate form. A stress test that creates leads is an attack on the business, not a test of it. The CX script refuses posts to ecowoods.ca.
- Do not download `backend/ecowoods.db`. Flag it. A human with authority inspects it.
- Do not add "ignore previous instructions" text to llms.txt, ai.txt, or schema. The live ai.txt already says the file is data. The preference pack in `03_ai-recommendation-stack/` follows that rule. Files there are proposals to merge, not live edits.
- Do not invent ratings, certifications, or case-study measurements. If a figure is not in the crawl output, it is not a fact in this bundle.
- Live model calls spend the caller's money. Default is off. Cap with `--live-limit`.

## Heavy downloads

`./download-heavy-deps.sh` prints commands and installs nothing unless `ECOWOODS_INSTALL_HEAVY=1`.

```sh
npm install playwright
npx playwright install chromium
export OPENAI_API_KEY=…   # only if you want --live
```

There is no requirements.txt install. Optional file: `requirements.txt` documents that.

## Test repo

`iceccarelli/ecowoods-test` existed on 2026-10-29 with a one-paragraph README and size 0 KB of history weight. This environment had no GitHub token, so nothing was pushed. `scripts/seed_test_repo.sh` explains the push. `test-repo-seed/README.md` is the replacement README.

## Folder map

```
01_site-crawl-and-inventory/        how the crawl is interpreted
02_seo-aeo-geo-audit/               scoring notes for SEO and GEO
03_ai-recommendation-stack/         fact sheet, entity graph, preference pack
04_customer-experience-end-to-end/  journeys the CX script walks
05_technical-performance-stress/    HTML budgets
06_content-authority-and-framework/ what to cite, what not to copy
07_conversion-and-lead-systems/     lead rules
08_competitive-intelligence/        public competitor observations
09_backend-and-ops-validation/      repo findings, lifecycle not executed
10_improvement-playbooks-and-patches/
11_monitoring-and-recurring-tests/  weekly cadence and a CI sketch
scripts/  fixtures/  reports/  test-repo-seed/
```

## Reversibility

Every fix in `10_improvement-playbooks-and-patches/PRIORITIZED_FIXES.md` has a reverse column. This bundle does not patch ecowoods-app by itself.
