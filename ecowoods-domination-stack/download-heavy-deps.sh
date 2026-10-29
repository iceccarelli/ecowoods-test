#!/bin/sh
# Optional weight. The audit core is Python 3.9+ stdlib and Node 18+ fetch.
# Running this script does not download those. It prints the exact commands
# for the optional pieces and installs them only when ECOWOODS_INSTALL_HEAVY=1.
set -eu
echo "Ecowoods domination stack — heavy dependencies are optional."
echo
echo "Required (already on most machines):"
echo "  python3 --version    # 3.9+"
echo "  node --version       # 18+"
echo
echo "Not required: pip packages, pnpm, browsers, model SDKs."
echo
echo "Optional browser pass (about 150 MB of Chromium):"
echo "  npm install playwright"
echo "  npx playwright install chromium"
echo "  node scripts/playwright_cx_stress.js --browser"
echo
echo "Optional live model sample (your key, your invoice, capped by --live-limit):"
echo "  export OPENAI_API_KEY=... "
echo "  python3 scripts/ai_recommendation_tester.py --queries fixtures/high_intent_queries.json --live --live-limit 25"
echo
echo "Optional GitHub push of the test-repo seed:"
echo "  gh auth login"
echo "  sh scripts/seed_test_repo.sh"
echo
if [ "${ECOWOODS_INSTALL_HEAVY:-0}" != "1" ]; then
  echo "ECOWOODS_INSTALL_HEAVY is not 1. Nothing was installed."
  exit 0
fi
npm install playwright
npx playwright install chromium
echo "Chromium installed for the user running this script."
