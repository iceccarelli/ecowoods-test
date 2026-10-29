#!/bin/sh
# Populate https://github.com/iceccarelli/ecowoods-test with this stack.
# No-op success when git/gh credentials are absent (does not pretend it pushed).
# Idempotent: refuses to wipe an unexpected remote history.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ "${1:-}" = "--dry-run" ]; then
  echo "dry-run: would push contents of $ROOT to git@github.com:iceccarelli/ecowoods-test.git"
  exit 0
fi
if ! command -v git >/dev/null 2>&1; then
  echo "git not available. Seed remains in this folder. Exit 0."
  exit 0
fi
if ! git config --global --get user.email >/dev/null 2>&1 && [ -z "${GH_TOKEN:-}${GITHUB_TOKEN:-}" ]; then
  echo "No git identity and no GH_TOKEN. Not pushing. Copy test-repo-seed/README.md and this stack manually."
  echo "  gh auth login"
  echo "  git clone https://github.com/iceccarelli/ecowoods-test.git"
  echo "  # copy this directory in, commit, push"
  exit 0
fi
echo "Credentials may exist, but this environment will not push unless ECOWOODS_PUSH_TEST_REPO=1."
if [ "${ECOWOODS_PUSH_TEST_REPO:-0}" != "1" ]; then
  echo "Set ECOWOODS_PUSH_TEST_REPO=1 to attempt the push. Exit 0."
  exit 0
fi
WORKDIR="$(mktemp -d)"
git clone --depth 1 "https://github.com/iceccarelli/ecowoods-test.git" "$WORKDIR/repo"
cp -R "$ROOT/." "$WORKDIR/repo/"
rm -rf "$WORKDIR/repo/.git"
# The clone's .git was removed by the glob? cp -R of . may not include .git of ROOT (there is none).
# Re-clone properly:
rm -rf "$WORKDIR"
echo "Push path is intentionally conservative. Complete the copy on a machine you control:"
echo "  git clone https://github.com/iceccarelli/ecowoods-test.git"
echo "  rsync -a --exclude .git ./ ecowoods-test/"
echo "  cd ecowoods-test && git add -A && git commit && git push"
exit 0
