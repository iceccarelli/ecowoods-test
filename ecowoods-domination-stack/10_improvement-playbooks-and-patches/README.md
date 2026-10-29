# Playbooks

`PRIORITIZED_FIXES.md` is rewritten by `scripts/generate_improvement_patches.sh` from the latest scorecard. Do not hand-edit it; edit `scripts/scorecard.py` if the ranking rules are wrong.

Patches against the product repo are described there as reversible actions. This folder does not contain a diff that rewrites production copy, because that copy is generated from constants in ecowoods-app and a blind diff would drift.
