import logging
import os
import subprocess
from typing import List


logging.basicConfig(
    filename="automation_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


BASE_STEPS: List[List[str]] = [
    ["python", "-u", "-m", "chesske_platform.scripts.run_pipeline"],
    ["python", "-u", "-m", "chesske_platform.scripts.export_public_csv"],
]

POSTGRES_VERIFY_CODE = """
from pathlib import Path

import pandas as pd
import psycopg

database_url = os.environ["DATABASE_URL"]
csv_path = Path("cleaned_master_chess_players.csv")
csv_rows = len(pd.read_csv(csv_path, low_memory=False).drop_duplicates(subset=["Username"], keep="last"))

with psycopg.connect(database_url) as conn, conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM users")
    db_users = int(cur.fetchone()[0])
    cur.execute("SELECT notes FROM pipeline_runs ORDER BY id DESC LIMIT 1")
    latest_note = cur.fetchone()[0]

print(f"Postgres verification: csv_rows={csv_rows} db_users={db_users} latest_run_note={latest_note}")
if db_users != csv_rows:
    raise SystemExit(f"Postgres user count mismatch: csv_rows={csv_rows} db_users={db_users}")
"""


def build_steps() -> List[List[str]]:
    steps = list(BASE_STEPS)
    if os.getenv("DATABASE_URL", "").strip():
        steps.extend(
            [
                [
                    "python",
                    "-u",
                    "-m",
                    "chesske_platform.scripts.bootstrap_postgres_from_csv",
                    "--reset",
                    "--csv",
                    "cleaned_master_chess_players.csv",
                ],
                ["python", "-u", "-c", "import os\n" + POSTGRES_VERIFY_CODE],
            ]
        )
    steps.extend(
        [
            ["python", "-u", "-m", "chesske_platform.scripts.warm_api_cache"],
            ["python", "-u", "africa_count.py"],
        ]
    )
    return steps


def run_step(cmd: List[str]) -> None:
    logging.info("Running step: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    logging.info("Step completed: %s", " ".join(cmd))


def main() -> None:
    try:
        for cmd in build_steps():
            run_step(cmd)
        logging.info("Production automation workflow completed successfully.")
    except subprocess.CalledProcessError as exc:
        logging.error("Automation failed on %s: %s", exc.cmd, exc)
        raise


if __name__ == "__main__":
    main()
