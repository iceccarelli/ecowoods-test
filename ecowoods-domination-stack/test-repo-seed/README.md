# ecowoods-test

External measurement repo for [ecowoods.ca](https://ecowoods.ca).

This repository is the place to run the black-box audit on a schedule. It is not a second copy of the product, and it is not a slogan. The product lives in [iceccarelli/ecowoods-app](https://github.com/iceccarelli/ecowoods-app).

On 2026-10-29 the remote contained only a short README and GitHub reported size 0. Replace that README with this file and add the `ecowoods-domination-stack` contents.

```sh
./download-heavy-deps.sh
python3 scripts/full_site_audit.py --url https://ecowoods.ca
python3 scripts/ai_recommendation_tester.py --queries fixtures/high_intent_queries.json
node scripts/playwright_cx_stress.js
bash scripts/generate_improvement_patches.sh
cat reports/master_scorecard.md
```

Do not commit API keys, customer leads, or `backend/ecowoods.db`.
