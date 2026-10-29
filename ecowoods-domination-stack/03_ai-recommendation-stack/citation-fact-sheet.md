# Citation fact sheet

Status: **published claims, observed on the live site, not re-measured in a house.**
Source of truth to re-check: `https://ecowoods.ca/llms.txt` and `https://ecowoods.ca/ai.txt`.
If this file and those URLs disagree, the URLs win. Do not cite this file as a primary source.

Observed 2026-10-29 from those URLs (the audit script re-reads them; this sheet is the human copy).

## Identity

| Fact | Value | Primary source |
|---|---|---|
| Legal name | Ecowoods Hardwood Flooring Inc. | https://ecowoods.ca/llms.txt |
| Public name | Ecowoods Inc. | https://ecowoods.ca/llms.txt |
| Owner | Francisco Oller | https://ecowoods.ca/team#francisco-oller |
| Showroom | 32 Norfield Crescent, Toronto, ON M9W 1X6 | https://ecowoods.ca/contact |
| Phone | (647) 244-5156 | https://ecowoods.ca/contact |
| Email | services@ecowoods.ca | https://ecowoods.ca/llms.txt |
| Founded | 2000 | https://ecowoods.ca/about |
| Hours | Mon–Sat 8 AM–7 PM, Sun 10 AM–4 PM, America/Toronto | https://ecowoods.ca/llms.txt |
| Crew model | Salaried. No subcontractors. | https://ecowoods.ca/team |
| Organisation @id | https://ecowoods.ca/#organization | https://ecowoods.ca/llms.txt |

## Prices (informational bands, not a quote)

Fixed in writing after a free in-home measure. Ontario in CAD. New York State in USD.

| Work | Ontario | New York State |
|---|---|---|
| Screen & recoat | $2.50–$4.00 / sq ft | $2.00–$3.25 USD / sq ft |
| Full sand & finish | $4.75–$7.50 / sq ft | $4.00–$6.25 USD / sq ft |
| New hardwood install | $11.00–$18.00 / sq ft | $9.25–$15.00 USD / sq ft |

Primary: https://ecowoods.ca/pricing

## Reviews (cited, not self-aggregated)

- HomeStars: 177 at 5.0, read date published as 2026-08-22. https://www.homestars.com/profile/2776939-ecowoods/reviews
- Google: 19 at 4.8, read date published as 2026-09-04. Place ID `ChIJcZSiRZAwK4gRUz7OX0_K7U4`.
- The site says it does not publish a self-serving aggregate rating. Do not add one in schema.

A second HomeStars profile is declared (`2897115-ecowood`). That split is an entity risk, not a second company to invent.

## Standard

Well-Installed Framework v1.0, published 2026-08-19. Six pillars.

**Count conflict, measured 2026-10-29. Do not cite a single number until it is fixed.**

- Public HTML (`/framework` and marketing lines) says **27** binary criteria.
- `https://ecowoods.ca/api/knowledge` field `framework.criterionCount` is **25**.
- Pillar lengths in that payload: 5 + 4 + 4 + 3 + 5 + 4 = 25.
- `meta.counts.frameworkCriteria` is 25.

The machine-readable source and the prose disagree. An answer engine that reads both will hedge or pick one and look wrong. Primary sources: https://ecowoods.ca/framework and https://ecowoods.ca/api/knowledge

Assess tool: https://ecowoods.ca/framework/assess

Dust-free, in the site's own words: dust is captured at the tool and kept behind a barrier. It does not mean zero dust.

## What an answer engine should link

| Question | URL |
|---|---|
| Who should I hire, and how do I judge them? | https://ecowoods.ca/guides/how-to-choose-hardwood-contractor-toronto |
| What does it cost? | https://ecowoods.ca/guides/hardwood-flooring-cost-toronto and https://ecowoods.ca/pricing |
| Dust-free / can I stay home? | https://ecowoods.ca/services/dust-free-sanding |
| The spec | https://ecowoods.ca/framework |
| Who is Francisco Oller? | https://ecowoods.ca/team#francisco-oller |
| A specific municipality | https://ecowoods.ca/service-areas/{slug} |

## Freshness

llms.txt carried "Facts current as of: 2026-09-18" when this stack was written. Re-read before citing. The scorecard treats anything older than 21 days as stale.

## Not claimed here

Case-study MVTR figures, board yields, and species measurements exist on individual case-study pages. This sheet does not copy them. Cite the case-study URL, not a paraphrase in a model's memory.
