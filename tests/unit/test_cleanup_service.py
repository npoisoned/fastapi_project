from datetime import datetime, timedelta, timezone

from app.models.expired_link import ExpiredLinkHistory
from app.models.link import Link
from app.services.cleanup_service import cleanup_service


def test_cleanup_expired_links_moves_link_to_history_and_deletes_from_links(db, monkeypatch):
    invalidated = {"called": False, "short_code": None}

    def fake_invalidate(short_code):
        invalidated["called"] = True
        invalidated["short_code"] = short_code

    monkeypatch.setattr("app.services.cleanup_service.invalidate_link_cache", fake_invalidate)

    expired_link = Link(
        short_code="expired-cleanup-link",
        original_url="https://www.python.org",
        custom_alias=True,
        user_id=1,
        created_by_authenticated=True,
        click_count=7,
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
        last_accessed_at=datetime.now(timezone.utc) - timedelta(hours=1),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        is_active=True,
    )
    db.add(expired_link)
    db.commit()

    deleted_count = cleanup_service.cleanup_expired_links(db)

    assert deleted_count == 1

    link_in_main_table = db.query(Link).filter(Link.short_code == "expired-cleanup-link").first()
    assert link_in_main_table is None

    history_item = (
        db.query(ExpiredLinkHistory)
        .filter(ExpiredLinkHistory.short_code == "expired-cleanup-link")
        .first()
    )

    assert history_item is not None
    assert history_item.original_url == "https://www.python.org"
    assert history_item.user_id == 1
    assert history_item.click_count == 7
    assert history_item.reason == "expired"

    assert invalidated["called"] is True
    assert invalidated["short_code"] == "expired-cleanup-link"


def test_cleanup_expired_links_does_not_touch_active_links(db, monkeypatch):
    monkeypatch.setattr("app.services.cleanup_service.invalidate_link_cache", lambda *args, **kwargs: None)

    active_link = Link(
        short_code="active-link",
        original_url="https://www.python.org",
        custom_alias=True,
        user_id=1,
        created_by_authenticated=True,
        click_count=0,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        is_active=True,
    )
    db.add(active_link)
    db.commit()

    deleted_count = cleanup_service.cleanup_expired_links(db)

    assert deleted_count == 0

    link_in_main_table = db.query(Link).filter(Link.short_code == "active-link").first()
    assert link_in_main_table is not None

    history_item = (
        db.query(ExpiredLinkHistory)
        .filter(ExpiredLinkHistory.short_code == "active-link")
        .first()
    )
    assert history_item is None


def test_get_expired_links_history_returns_items(db):
    item1 = ExpiredLinkHistory(
        short_code="expired-1",
        original_url="https://example.com/1",
        user_id=1,
        created_at=datetime.now(timezone.utc) - timedelta(days=2),
        expired_at=datetime.now(timezone.utc) - timedelta(hours=2),
        click_count=3,
        last_accessed_at=datetime.now(timezone.utc) - timedelta(hours=3),
        reason="expired",
    )
    item2 = ExpiredLinkHistory(
        short_code="expired-2",
        original_url="https://example.com/2",
        user_id=2,
        created_at=datetime.now(timezone.utc) - timedelta(days=3),
        expired_at=datetime.now(timezone.utc) - timedelta(hours=1),
        click_count=5,
        last_accessed_at=datetime.now(timezone.utc) - timedelta(hours=2),
        reason="expired",
    )
    db.add_all([item1, item2])
    db.commit()

    result = cleanup_service.get_expired_links_history(db, limit=10)

    assert len(result) == 2
    assert result[0]["short_code"] == "expired-2"
    assert result[1]["short_code"] == "expired-1"
    assert result[0]["reason"] == "expired"