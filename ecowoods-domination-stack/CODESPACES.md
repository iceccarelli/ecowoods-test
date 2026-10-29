# Codespaces — first hour in ecowoods-test

Run this from the test repo root (`/workspaces/ecowoods-test`). The zip unpacks into one directory, `ecowoods-domination-stack/`. It does not touch `.git`.

```bash
cd /workspaces/ecowoods-test
curl -fL --retry 3 -o /tmp/ecowoods-domination-stack.zip "$ECOWOODS_STACK_URL"
echo "$ECOWOODS_STACK_SHA256  /tmp/ecowoods-domination-stack.zip" | sha256sum -c -
unzip -o /tmp/ecowoods-domination-stack.zip -d "$PWD"
cd ecowoods-domination-stack
chmod +x download-heavy-deps.sh scripts/*.sh
./download-heavy-deps.sh
make dry
```

`ECOWOODS_STACK_URL` and `ECOWOODS_STACK_SHA256` are printed where this zip was published. If `sha256sum -c` fails, do not run anything else. The file was changed in transit.

## What `make dry` proves

No network. Every entry point accepts `--dry-run` and exits 0. If this fails, the unzip is wrong. Fix that before auditing the live site.

## What `make live` does

Reads https://ecowoods.ca and the public GitHub API. GET and HEAD only. It does not submit the estimate form, does not clone the 1 GB app repo, and does not download `backend/ecowoods.db`.

```bash
make live
sed -n '1,80p' reports/master_scorecard.md
```

## Commit it into this repo

```bash
cd /workspaces/ecowoods-test
git add ecowoods-domination-stack
git status
git commit -m "Add external audit stack for ecowoods.ca"
git push origin main
```

Do not commit API keys. There is no `.env` in this stack.

## This does not edit ecowoods.ca

Fixes are listed in `10_improvement-playbooks-and-patches/PRIORITIZED_FIXES.md`. They are applied in `iceccarelli/ecowoods-app`, one reversible change at a time, starting with F0 (one framework criterion count). This repository measures. The app repository changes the site.
