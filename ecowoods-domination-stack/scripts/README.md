# Scripts

All accept `--dry-run`.

| Script | Role |
|---|---|
| full_site_audit.py | Sitemap crawl, priority HTML, machine files |
| backend_repo_audit.py | GitHub metadata, no clone |
| ai_recommendation_tester.py | 200+ query retrieval test; optional live model |
| playwright_cx_stress.js | Journey HTTP probe; optional real browser |
| scorecard.py | 0–100 dimensions |
| generate_improvement_patches.sh | Calls scorecard.py |
| run_protocol.sh | Full sequence |
| seed_test_repo.sh | Refuses to push without an explicit env flag |
