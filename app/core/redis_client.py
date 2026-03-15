import json
from datetime import datetime, timezone

from redis import Redis

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


def _link_cache_key(short_code: str) -> str:
    return f"link:{short_code}"


def cache_link(short_code: str, original_url: str, expires_at, is_active: bool) -> None:
    payload = {
        "original_url": original_url,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "is_active": is_active,
    }

    key = _link_cache_key(short_code)

    if expires_at:
        now = datetime.now(timezone.utc)
        ttl = int((expires_at - now).total_seconds())
        if ttl > 0:
            redis_client.set(key, json.dumps(payload), ex=ttl)
            return

    redis_client.set(key, json.dumps(payload))


def get_cached_link(short_code: str):
    raw = redis_client.get(_link_cache_key(short_code))
    if not raw:
        return None
    return json.loads(raw)


def invalidate_link_cache(short_code: str) -> None:
    redis_client.delete(_link_cache_key(short_code))