# Prioritized fixes

Generated 2026-10-29T18:30:39Z. Ranked by expected effect on organic visibility plus AI citation, not by how impressive they sound. Each item is reversible.

| ID | Sev | Change | Measure | Reverse |
|---|---|---|---|---|
| F0 | P0 | One criterion count. API says 25, pages say 27. Regenerate every surface from `framework.criterionCount`. | knowledge count equals the number in `/framework` H1 and in llms.txt | Revert the constants |
| F1 | P0 | Inspect `backend/ecowoods.db`. If it contains personal data, remove it from the tree and history. | `git ls-files backend/ecowoods.db` returns nothing; a fresh clone has no customer rows | Restore the blob only if it was a fixture |
| F2 | P0 | Google review velocity: QR and the published write-review link at job close. No incentive that violates Google's policy. | Review count in llms.txt, with a new read date, moves from ~19 toward 50 in 90 days | Stop asking |
| F3 | P0 | Fail deploy when live `llms.txt` facts date is older than 21 days. | `facts_as_of` in `reports/signals_site.json` within 21 days | Remove the CI check |
| F4 | P1 | Ship `/framework.md` and `/authority.md` (both 404 on 2026-10-29; other priority twins returned 200). | `markdown_twin_404` empty | Delete the routes |
| F5 | P1 | HTML budget: `/` ≤ 180 KB, `/estimate` ≤ 160 KB. `/hardwood-flooring-toronto` was ~800 KB. | `heavy_priority_pages` empty | Revert the asset split |
| F6 | P1 | Weekly live model sample, n=25, two vendors, frozen query ids. | `dominance_proven` becomes a time series, not a slogan | Stop the job |
| F7 | P1 | Resolve credential queries: publish real registry URLs or an explicit "we do not claim X" line in ai.txt. | Query cluster `dust-free` and "Bona certified" no longer produce a hedged or wrong citation | Edit ai.txt |
| F8 | P2 | Finish the CSP migration off `script-src 'unsafe-inline'`. | Enforced CSP matches today's report-only script-src, pages still work | Restore the previous CSP |
| F9 | P2 | Shrink the git repo under 200 MB without deleting history of the site. | GitHub `size` field | LFS / filter-repo is hard to reverse; do it on a mirror first |
| F10 | P2 | One third-party page that cites the Framework by URL, not a homepage mention. | Referring URL returns 200 and links to /framework | Outreach, not a code revert |
| F11 | P3 | Populate `ecowoods-test` with this stack's CI, not a slogan README. | Test repo contains `scripts/` and a green run | Delete the commit |

Do not: buy reviews, stamp an aggregateRating you computed yourself, cloak, or add "ignore previous instructions" blocks. The live ai.txt already says the file is data. Keep that sentence.
