# ChessKE Atlas Frontend (Next.js)

High-impact recruiter-facing frontend for the ChessKE production API.

## Prerequisites

- Node.js 20+ (you have v22)
- Backend API running:

```bash
python -m chesske_platform.scripts.serve_api
```

## Run

```bash
cd frontend
npm install
npm run dev
```

Open: `http://localhost:3000`

## Routes

- `/` Atlas overview
- `/leaderboards` Full ranking surfaces
- `/player` Player route entry
- `/player/[username]` Deep player profile
- `/methodology` Data trust and collection model
- `/observability` Pipeline runs and error telemetry

## API Base URL

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_CHESSKE_API_BASE=http://127.0.0.1:8000
```

If omitted, the app defaults to `http://127.0.0.1:8000`.

## Quality checks

```bash
npm run lint
npm run build
```
