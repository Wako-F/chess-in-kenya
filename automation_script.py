import logging
import subprocess
from typing import List


logging.basicConfig(
    filename="automation_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


STEPS: List[List[str]] = [
    ["python", "-u", "-m", "chesske_platform.scripts.run_pipeline"],
    ["python", "-u", "-m", "chesske_platform.scripts.export_public_csv"],
    ["python", "-u", "africa_count.py"],
]


def run_step(cmd: List[str]) -> None:
    logging.info("Running step: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    logging.info("Step completed: %s", " ".join(cmd))


def main() -> None:
    try:
        for cmd in STEPS:
            run_step(cmd)
        logging.info("Production automation workflow completed successfully.")
    except subprocess.CalledProcessError as exc:
        logging.error("Automation failed on %s: %s", exc.cmd, exc)
        raise


if __name__ == "__main__":
    main()

