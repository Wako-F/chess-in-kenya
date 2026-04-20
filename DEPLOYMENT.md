# Deployment Checklist (GitHub + Vercel)

This repo now has two deployable surfaces:

- `frontend/` (Next.js app) -> deploy on Vercel
- `chesske_platform/` API (FastAPI) -> deploy on a Python host (Render/Railway/Fly/VM)

Vercel should host **frontend only**.

## 1) Pre-push sanity checks

From repo root:

```bash
python -m py_compile chesske_platform/chesske/api.py
```

From `frontend/`:

```bash
npm run lint
npm run build
```

## 2) Push to GitHub

Suggested flow:

```bash
git add .
git status
git commit -m "Production platform + analytics frontend + repo cleanup"
git push
```

## 3) Deploy backend API (required before frontend is useful)

Deploy `chesske_platform/chesske/api.py` app with your Python host.

Required backend env vars:

- `DATABASE_URL` (PostgreSQL connection URL; preferred for production)
- `CHESSKE_DB_PATH` (SQLite fallback when `DATABASE_URL` is not set)
- `CHESSKE_CORS_ORIGINS` (comma-separated)
  - local dev: `http://localhost:3000,http://127.0.0.1:3000`
  - add your Vercel domain after deploy, for example:
    `https://chesske-atlas.vercel.app`

Optional:

- `CHESSKE_REFRESH_LIMIT`
- `CHESSKE_MAX_ACTIVE_PLAYERS`
- timeout/retry knobs in `chesske_platform/chesske/config.py`
- `CHESSKE_AUTO_BOOTSTRAP` (`1` by default)
- `CHESSKE_BOOTSTRAP_CSV` (optional override path for bootstrap csv)
- `CHESSKE_BOOTSTRAP_LIMIT` (`0` = full csv; set a smaller number on free tier for faster warmup)

### Free tier note (no persistent disk)

If using Render free tier, keep `CHESSKE_DB_PATH` inside writable ephemeral storage, for example:

- `CHESSKE_DB_PATH=data/chesske.db`

On free tier, the DB resets on restarts/redeploys. The API now auto-bootstraps from CSV when empty.

### Postgres cutover (Aiven + Render)

When `DATABASE_URL` is set, the backend now uses PostgreSQL automatically.

Recommended Render env for Postgres mode:

- `DATABASE_URL=postgres://...`
- `CHESSKE_AUTO_BOOTSTRAP=0`
- keep `CHESSKE_CORS_ORIGINS` with your Vercel domains

Optional: keep `CHESSKE_DB_PATH` for local fallback only.

## 4) Deploy frontend on Vercel

In Vercel project settings:

1. Import GitHub repo
2. Set **Root Directory** to `frontend`
3. Framework preset: Next.js
4. Add env var:
   - `NEXT_PUBLIC_CHESSKE_API_BASE=https://<your-api-host>`
5. Deploy

## 5) Post-deploy validation

Frontend pages:

- `/`
- `/leaderboards`
- `/player`
- `/methodology`
- `/observability`

On landing page, confirm **Analytics Engine Status** shows green endpoint checks.

If any endpoint is red:

- check backend CORS (`CHESSKE_CORS_ORIGINS`)
- check API base URL env in Vercel
- check backend logs for endpoint errors
