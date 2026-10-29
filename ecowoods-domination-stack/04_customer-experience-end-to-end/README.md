# Customer experience

Journeys, all GET:

home → services → dust-free → refinishing → installation → cost guide → framework → quote scorer → case studies → estimate → contact → reviews → floor studio → quote check → a service area → realtors.

`scripts/playwright_cx_stress.js` checks status, a few expected phrases, tel links, and form *presence*. It does not submit.

Phone is the published channel: (647) 244-5156. WhatsApp was not assumed to exist. If a later crawl finds `wa.me`, record it; do not invent a number.

Session replay and heatmaps are not included. Faking them would be a lie. A browser pass (`--browser`, after Playwright is installed) records console errors on a 390×844 viewport.
