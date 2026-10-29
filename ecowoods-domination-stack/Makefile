.PHONY: dry live scorecard chmod

chmod:
	chmod +x download-heavy-deps.sh scripts/*.sh

dry: chmod
	./download-heavy-deps.sh
	python3 scripts/full_site_audit.py --url https://ecowoods.ca --dry-run
	python3 scripts/backend_repo_audit.py --dry-run
	python3 scripts/ai_recommendation_tester.py --queries fixtures/high_intent_queries.json --dry-run
	node scripts/playwright_cx_stress.js --dry-run
	sh scripts/generate_improvement_patches.sh --dry-run
	sh scripts/seed_test_repo.sh --dry-run

live: chmod
	sh scripts/run_protocol.sh

scorecard:
	sh scripts/generate_improvement_patches.sh
	sed -n '1,40p' reports/master_scorecard.md
