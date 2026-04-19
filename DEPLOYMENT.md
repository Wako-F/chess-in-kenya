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

- `CHESSKE_DB_PATH` (for example `/data/chesske.db`)
- `CHESSKE_CORS_ORIGINS` (comma-separated)
  - local dev: `http://localhost:3000,http://127.0.0.1:3000`
  - add your Vercel domain after deploy, for example:
    `https://chesske-atlas.vercel.app`

Optional:

- `CHESSKE_REFRESH_LIMIT`
- `CHESSKE_MAX_ACTIVE_PLAYERS`
- timeout/retry knobs in `chesske_platform/chesske/config.py`

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

