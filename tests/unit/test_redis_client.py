import json
from datetime import datetime, timedelta, timezone

import app.core.redis_client as redis_module


class FakeRedis:
    def __init__(self):
        self.storage = {}
        self.last_set = None
        self.last_delete = None

    def set(self, key, value, ex=None):
        self.storage[key] = value
        self.last_set = {"key": key, "value": value, "ex": ex}

    def get(self, key):
        return self.storage.get(key)

    def delete(self, key):
        self.last_delete = key
        self.storage.pop(key, None)


def test_link_cache_key():
    assert redis_module._link_cache_key("abc123") == "link:abc123"


def test_cache_link_with_ttl(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(redis_module, "redis_client", fake_redis)

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    redis_module.cache_link(
        short_code="ttl-link",
        original_url="https://example.com",
        expires_at=expires_at,
        is_active=True,
    )

    assert fake_redis.last_set["key"] == "link:ttl-link"
    assert fake_redis.last_set["ex"] is not None
    payload = json.loads(fake_redis.last_set["value"])
    assert payload["original_url"] == "https://example.com"
    assert payload["is_active"] is True


def test_cache_link_without_ttl(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(redis_module, "redis_client", fake_redis)

    redis_module.cache_link(
        short_code="no-ttl-link",
        original_url="https://example.com",
        expires_at=None,
        is_active=True,
    )

    assert fake_redis.last_set["key"] == "link:no-ttl-link"
    assert fake_redis.last_set["ex"] is None


def test_get_cached_link_hit(monkeypatch):
    fake_redis = FakeRedis()
    fake_redis.storage["link:cached-link"] = json.dumps(
        {
            "original_url": "https://example.com",
            "expires_at": None,
            "is_active": True,
        }
    )
    monkeypatch.setattr(redis_module, "redis_client", fake_redis)

    result = redis_module.get_cached_link("cached-link")

    assert result["original_url"] == "https://example.com"
    assert result["is_active"] is True


def test_get_cached_link_miss(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(redis_module, "redis_client", fake_redis)

    result = redis_module.get_cached_link("missing-link")

    assert result is None


def test_invalidate_link_cache(monkeypatch):
    fake_redis = FakeRedis()
    fake_redis.storage["link:dead-link"] = "value"
    monkeypatch.setattr(redis_module, "redis_client", fake_redis)

    redis_module.invalidate_link_cache("dead-link")

    assert fake_redis.last_delete == "link:dead-link"
    assert "link:dead-link" not in fake_redis.storage