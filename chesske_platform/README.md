# ChessKE Production Platform

This is the production track for the project. It separates:
- Collection/refresh pipeline
- Durable database state
- Quality checks
- API for presentation
- Optional Streamlit v2 UI that consumes the API

## Architecture

- Ingestion source: Chess.com API active users endpoint for `KE`
- Storage: SQLite (`data/chesske.db`) with normalized tables
- API: FastAPI
- UI: Streamlit (`streamlit_dashboard_v2.py`) backed by API endpoints

## Tables

- `users`: canonical user state (`active`/`deleted`, discovery metadata)
- `user_stats_latest`: latest stats snapshot per user
- `country_active_snapshots`: daily list of active users by snapshot date
- `pipeline_runs`: run metadata and health
- `run_errors`: per-run errors for observability

## Quick Start

Run from repo root.

1) Bootstrap DB from current master CSV:

```bash
python chesske_platform/scripts/bootstrap_from_master_csv.py --csv master_chess_players.csv
```

2) Run rolling ingestion (active discovery + refresh queue):

```bash
python chesske_platform/scripts/run_pipeline.py
```

3) Export API-backed public CSV for backward compatibility:

```bash
python chesske_platform/scripts/export_public_csv.py
```

4) Start API:

```bash
python chesske_platform/scripts/serve_api.py
```

5) (Optional) Start dashboard v2:

```bash
streamlit run chesske_platform/streamlit_dashboard_v2.py
```

## Environment Variables

- `CHESSKE_DB_PATH` (default: `data/chesske.db`)
- `CHESSKE_COUNTRY_CODE` (default: `KE`)
- `CHESSKE_REFRESH_LIMIT` (default: `500`)
- `CHESSKE_MAX_ACTIVE_PLAYERS` (default: `0`, disabled)
- `CHESSKE_CONNECT_TIMEOUT` (default: `8`)
- `CHESSKE_READ_TIMEOUT` (default: `20`)
- `CHESSKE_REQUEST_DELAY_SECONDS` (default: `0.25`)
- `CHESSKE_MAX_RETRIES` (default: `4`)

## API Endpoints

- `GET /health`
- `GET /meta/quality`
- `GET /overview`
- `GET /leaderboards/{rapid|blitz|bullet|daily|puzzle|games}`
- `GET /players/{username}`
- `GET /trends/joins?months=48`
- `GET /trends/discovery?days=60`

