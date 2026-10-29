# Backend and ops

`scripts/backend_repo_audit.py` reads the public GitHub API. It does not clone.

Observed layout of iceccarelli/ecowoods-app:

- `apps/web` — the site (Next.js, deployed on Vercel; confirmed by response headers)
- `apps/admin` — admin dashboard
- `apps/mobile` — React Native / Expo
- `backend/` — FastAPI, Alembic, tests, Dockerfile, and a committed `ecowoods.db`
- `scripts/verify-*.mjs` — a large internal AEO and content suite
- `docker-compose.yml`, `services/render-api`

Not validated, on purpose, without credentials: JWT flows, rate limits, race conditions, Postgres, the estimate→invoice lifecycle, load.

P0: a human inspects `backend/ecowoods.db` for personal data before the next public push.

The internal suite is a strength. Self-grading is not a measurement of whether ChatGPT cites the site. Keep both.
