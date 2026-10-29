# Monitoring

`weekly.yml` is a GitHub Actions sketch. It runs the external audit. It does not deploy the site.

Cadence:

- Every Monday: crawl, retrieval test, CX HTTP probe, scorecard artifact.
- Every Monday once keys exist: `--live --live-limit 25` on a frozen id list, stored next to the previous JSON. Diff mention rate.
- Every deploy of ecowoods-app: the existing `verify-freshness.mjs` and `verify-entity.mjs`. Fail the deploy if llms facts are older than 21 days.

Leading indicators, in this order: Google review count (dated), live primary-citation rate, non-brand organic clicks, estimate requests, close rate.
