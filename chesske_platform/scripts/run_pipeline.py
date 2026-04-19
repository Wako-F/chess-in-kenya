from datetime import datetime

from chesske_platform.chesske.config import Settings
from chesske_platform.chesske.pipeline import run_ingestion_pipeline
from chesske_platform.chesske.quality import compute_quality_report


def main() -> None:
    settings = Settings()
    result = run_ingestion_pipeline(settings)
    report = compute_quality_report(settings)
    with open("last_update.txt", "w", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with open("refresh.flag", "w", encoding="utf-8") as f:
        f.write(f"Refreshed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("Pipeline run summary:", result)
    print("Quality report:", report)


if __name__ == "__main__":
    main()
