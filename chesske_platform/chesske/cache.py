import json
import logging
from typing import Any, Callable, Optional, TypeVar

from .config import Settings


logger = logging.getLogger(__name__)
T = TypeVar("T")


def _client(settings: Settings) -> Optional[Any]:
    if not settings.redis_url:
        return None
    try:
        import redis

        return redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    except Exception as exc:
        logger.warning("Redis unavailable: %s", exc)
        return None


def cached_json(settings: Settings, key: str, ttl_seconds: int, builder: Callable[[], T]) -> T:
    redis_client = _client(settings)
    if redis_client is not None:
        try:
            raw = redis_client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.warning("Redis read failed for %s: %s", key, exc)

    payload = builder()

    if redis_client is not None:
        try:
            redis_client.setex(key, ttl_seconds, json.dumps(payload))
        except Exception as exc:
            logger.warning("Redis write failed for %s: %s", key, exc)

    return payload
