#!/bin/sh
# Refresh the scorecard and the prioritized fix list from whatever reports exist.
# Idempotent. --dry-run writes nothing.
set -eu
cd "$(dirname "$0")/.."
exec python3 scripts/scorecard.py "$@"
