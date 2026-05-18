# ChessKE VPS Operations

Production currently runs on the Contabo VPS at `38.242.228.254`.

## Runtime Layout

- App checkout: `/opt/chesske`
- Backend: FastAPI via `chesske-api.service`
- Frontend: Next.js via `chesske-frontend.service`
- Reverse proxy: Nginx, public `/` to frontend and `/api/*` to backend
- Database: local PostgreSQL, connection stored in `/opt/chesske/.env.production`
- Backups: `/opt/chesske/backups`

## Public URLs

- VPS direct site: `http://38.242.228.254/`
- VPS API health: `http://38.242.228.254/api/health`
- Vercel site: `https://chesskenya.vercel.app/`

Vercel rewrites `/api/*` to the VPS API, so the HTTPS Vercel site uses VPS-backed data.

## Deploying Code Changes

Do not hand-edit production files on the VPS except for emergency operations. Make code changes in Git, commit, push, then deploy the latest `main` on the VPS:

```bash
ssh -i ~/.ssh/chesske_contabo_codex2 codex@38.242.228.254
/opt/chesske/bin/deploy-latest.sh
```

The deploy script pulls `origin/main`, reinstalls dependencies as needed, builds the frontend, and restarts the backend and frontend services.

## Data Updates

GitHub Actions no longer runs the scheduled production data job. The VPS owns ingestion.

Check the data timer:

```bash
systemctl status chesske-pipeline.timer
systemctl list-timers --all | grep chesske
```

Run a manual data refresh:

```bash
sudo systemctl start chesske-pipeline.service
```

Check pipeline logs:

```bash
sudo journalctl -u chesske-pipeline.service -n 100 --no-pager
```

The frontend pages revalidate every 5 minutes, so new database data appears without a Vercel rebuild.

## Service Checks

```bash
sudo systemctl status chesske-api chesske-frontend nginx
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1/api/health
```

Follow logs:

```bash
sudo journalctl -u chesske-api -f
sudo journalctl -u chesske-frontend -f
```

## Backups

Backups run daily through `chesske-backup.timer` and are retained under `/opt/chesske/backups`.

```bash
systemctl status chesske-backup.timer
ls -lh /opt/chesske/backups
```

Run a manual backup:

```bash
sudo systemctl start chesske-backup.service
```

## Security Notes

- SSH uses key auth for `codex`.
- Password SSH and root SSH are disabled.
- UFW allows only SSH plus Nginx HTTP/HTTPS.
- fail2ban is enabled for SSH.

