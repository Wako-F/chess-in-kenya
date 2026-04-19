# Production Migration Notes

The production implementation now lives under [`chesske_platform/`](C:/Users/Datac/OneDrive/Desktop/chess-in-kenya/chesske_platform).

## What changed

- Added database-backed ingestion and API service.
- Added rolling discovery + refresh queue pipeline.
- Added data quality reporting endpoint.
- Added CSV export compatibility bridge for existing dashboard consumers.
- Updated `automation_script.py` to run production pipeline + export.

## First-time setup

```bash
pip install -r requirements.txt
python -m chesske_platform.scripts.bootstrap_from_master_csv --csv master_chess_players.csv --reset-db
```

## Daily run

```bash
python automation_script.py
```

## Run API

```bash
python -m chesske_platform.scripts.serve_api
```

## Run dashboard v2

```bash
streamlit run chesske_platform/streamlit_dashboard_v2.py
```

## Run recruiter-facing Next.js frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend routes:
- `/`
- `/leaderboards`
- `/player`
- `/player/[username]`
- `/methodology`
- `/observability`
