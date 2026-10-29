#!/bin/sh
# Full sequence from 00_README_EXECUTION_ORDER.md. Continues after a non-zero
# audit exit so the scorecard still renders. Pass --dry-run to touch nothing remote.
set -eu
cd "$(dirname "$0")/.."
if [ "${1:-}" = "--dry-run" ]; then
  python3 scripts/full_site_audit.py --url https://ecowoods.ca --dry-run
  python3 scripts/backend_repo_audit.py --dry-run
  python3 scripts/ai_recommendation_tester.py --queries fixtures/high_intent_queries.json --dry-run
  node scripts/playwright_cx_stress.js --dry-run
  sh scripts/generate_improvement_patches.sh --dry-run
  sh scripts/seed_test_repo.sh --dry-run
  exit 0
fi
python3 scripts/full_site_audit.py --url https://ecowoods.ca || true
python3 scripts/backend_repo_audit.py || true
python3 scripts/ai_recommendation_tester.py --queries fixtures/high_intent_queries.json || true
node scripts/playwright_cx_stress.js || true
sh scripts/generate_improvement_patches.sh
echo "----- reports/master_scorecard.md -----"
cat reports/master_scorecard.md
