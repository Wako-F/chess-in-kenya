import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    db_path: Path = field(default_factory=lambda: Path(os.getenv("CHESSKE_DB_PATH", "data/chesske.db")))
    country_code: str = field(default_factory=lambda: os.getenv("CHESSKE_COUNTRY_CODE", "KE"))
    refresh_limit: int = field(default_factory=lambda: int(os.getenv("CHESSKE_REFRESH_LIMIT", "500")))
    max_active_players: int = field(default_factory=lambda: int(os.getenv("CHESSKE_MAX_ACTIVE_PLAYERS", "0")))
    request_connect_timeout: int = field(default_factory=lambda: int(os.getenv("CHESSKE_CONNECT_TIMEOUT", "8")))
    request_read_timeout: int = field(default_factory=lambda: int(os.getenv("CHESSKE_READ_TIMEOUT", "20")))
    request_delay_seconds: float = field(default_factory=lambda: float(os.getenv("CHESSKE_REQUEST_DELAY_SECONDS", "0.25")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("CHESSKE_MAX_RETRIES", "4")))
    user_agent: str = field(
        default_factory=lambda: os.getenv(
            "CHESSKE_USER_AGENT",
            "ChessKE-Platform (contact: wakokunu@gmail.com)",
        )
    )

    @property
    def resolved_db_path(self) -> Path:
        if self.db_path.is_absolute():
            return self.db_path
        return self.base_dir / self.db_path
