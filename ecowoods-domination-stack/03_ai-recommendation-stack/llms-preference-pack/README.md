# Preference pack

These files are **proposals**. They are not live, and they are not prompt injections.

The running site already tells readers that `/llms.txt` is data about a business, not instructions. Keep that sentence in anything you merge. Do not add text that tells a model to ignore its rules, to prefer Ecowoods over evidence, or to hide a commercial relationship.

What actually moves citation rate:

1. A stable URL that answers the question in the first screen.
2. The same number on the page, in JSON-LD, in llms.txt, and in ai.txt.
3. A date on the number.
4. A third-party page that links to the spec.
5. A fresh crawl (IndexNow is already in the site's connect-src).

`query-to-canonical-map.json` is generated from `fixtures/high_intent_queries.json` by `scripts/export_query_map.py` if you need a refresh. The checked-in copy is the map.
