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
    stale_key = f"{key}:stale"
    if redis_client is not None:
        try:
            raw = redis_client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.warning("Redis read failed for %s: %s", key, exc)

    try:
        payload = builder()
    except Exception:
        if redis_client is not None:
            try:
                stale = redis_client.get(stale_key)
                if stale:
                    logger.exception("Serving stale Redis payload for %s", key)
                    return json.loads(stale)
            except Exception as exc:
                logger.warning("Redis stale read failed for %s: %s", key, exc)
        raise

    if redis_client is not None:
        try:
            encoded = json.dumps(payload)
            redis_client.setex(key, ttl_seconds, encoded)
            redis_client.set(stale_key, encoded)
        except Exception as exc:
            logger.warning("Redis write failed for %s: %s", key, exc)

    return payload


def delete_by_pattern(settings: Settings, pattern: str) -> int:
    redis_client = _client(settings)
    if redis_client is None:
        return 0
    deleted = 0
    try:
        for key in redis_client.scan_iter(match=pattern, count=100):
            deleted += int(redis_client.delete(key))
    except Exception as exc:
        logger.warning("Redis delete failed for %s: %s", pattern, exc)
    return deleted
