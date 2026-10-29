# AI recommendation stack

Priority surface. Read `citation-fact-sheet.md` before citing anything.

`entity-graph.json` is a proposal to diff against live JSON-LD. It deliberately has no `aggregateRating`.

`llms-preference-pack/` is not a jailbreak. The live site already forbids that reading of llms.txt. Keep it that way.

`scripts/ai_recommendation_tester.py` scores retrieval readiness for 200+ queries. It does not call a model unless you pass `--live` and an API key. Until a live sample of at least 25 queries shows a top-3 rate, the scorecard caps this dimension at 64 and sets dominance to false.
