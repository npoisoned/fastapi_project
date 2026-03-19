from datetime import datetime, timedelta, timezone

from app.services.link_service import link_service
from app.models.link import Link


def test_create_link_success(db, monkeypatch):
    monkeypatch.setattr("app.services.link_service.cache_link", lambda *args, **kwargs: None)

    result = link_service.create_link(
        db=db,
        original_url="https://www.python.org",
        base_url="http://testserver",
        custom_alias="unit-link",
        expires_at=None,
        user_id=None,
        created_by_authenticated=False,
    )

    assert result["short_code"] == "unit-link"
    assert result["short_url"] == "http://testserver/unit-link"
    assert result["original_url"] == "https://www.python.org"
    assert result["is_active"] is True


def test_create_link_duplicate_alias(db, monkeypatch):
    monkeypatch.setattr("app.services.link_service.cache_link", lambda *args, **kwargs: None)

    link_service.create_link(
        db=db,
        original_url="https://www.python.org",
        base_url="http://testserver",
        custom_alias="duplicate-unit",
    )

    try:
        link_service.create_link(
            db=db,
            original_url="https://docs.python.org",
            base_url="http://testserver",
            custom_alias="duplicate-unit",
        )
        assert False
    except ValueError as e:
        assert str(e) == "Alias already exists"


def test_get_link_entity(db):
    link = Link(
        short_code="entity-link",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
    )
    db.add(link)
    db.commit()

    result = link_service.get_link_entity(db, "entity-link")

    assert result is not None
    assert result.short_code == "entity-link"


def test_get_link_returns_none_for_missing(db):
    result = link_service.get_link(db, "missing-link")
    assert result is None


def test_get_link_returns_none_for_inactive(db):
    link = Link(
        short_code="inactive-link",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=False,
        created_by_authenticated=False,
    )
    db.add(link)
    db.commit()

    result = link_service.get_link(db, "inactive-link")
    assert result is None


def test_get_link_marks_expired_as_inactive(db, monkeypatch):
    invalidated = {"called": False}

    def fake_invalidate(short_code):
        invalidated["called"] = True

    monkeypatch.setattr("app.services.link_service.invalidate_link_cache", fake_invalidate)

    expired_time = datetime.now(timezone.utc) - timedelta(minutes=1)

    link = Link(
        short_code="expired-link",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
        expires_at=expired_time,
    )
    db.add(link)
    db.commit()

    result = link_service.get_link(db, "expired-link")
    db.refresh(link)

    assert result is None
    assert link.is_active is False
    assert invalidated["called"] is True


def test_get_link_info(db):
    link = Link(
        short_code="info-unit-link",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
    )
    db.add(link)
    db.commit()

    result = link_service.get_link_info(db, "info-unit-link")

    assert result is not None
    assert result["short_code"] == "info-unit-link"


def test_redirect_link_without_cache(db, monkeypatch):
    monkeypatch.setattr("app.services.link_service.get_cached_link", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.services.link_service.cache_link", lambda *args, **kwargs: None)

    link = Link(
        short_code="redirect-unit",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
        click_count=0,
    )
    db.add(link)
    db.commit()

    result = link_service.redirect_link(db, "redirect-unit")
    db.refresh(link)

    assert result["original_url"] == "https://www.python.org"
    assert link.click_count == 1
    assert link.last_accessed_at is not None


def test_update_link(db, monkeypatch):
    monkeypatch.setattr("app.services.link_service.invalidate_link_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.services.link_service.cache_link", lambda *args, **kwargs: None)

    link = Link(
        short_code="update-unit",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
    )
    db.add(link)
    db.commit()

    result = link_service.update_link(db, "update-unit", "https://docs.python.org")
    db.refresh(link)

    assert result["original_url"] == "https://docs.python.org"
    assert link.original_url == "https://docs.python.org"


def test_update_link_returns_none_for_missing(db):
    result = link_service.update_link(db, "missing-update", "https://docs.python.org")
    assert result is None


def test_delete_link(db, monkeypatch):
    monkeypatch.setattr("app.services.link_service.invalidate_link_cache", lambda *args, **kwargs: None)

    link = Link(
        short_code="delete-unit",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
    )
    db.add(link)
    db.commit()

    result = link_service.delete_link(db, "delete-unit")
    db.refresh(link)

    assert result is True
    assert link.is_active is False


def test_delete_link_returns_false_for_missing(db):
    result = link_service.delete_link(db, "missing-delete")
    assert result is False


def test_get_stats(db):
    link = Link(
        short_code="stats-unit",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
        click_count=5,
    )
    db.add(link)
    db.commit()

    result = link_service.get_stats(db, "stats-unit")

    assert result is not None
    assert result["short_code"] == "stats-unit"
    assert result["click_count"] == 5


def test_search_by_original_url(db):
    link1 = Link(
        short_code="search1",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
    )
    link2 = Link(
        short_code="search2",
        original_url="https://www.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
    )
    link3 = Link(
        short_code="search3",
        original_url="https://docs.python.org",
        custom_alias=True,
        is_active=True,
        created_by_authenticated=False,
    )
    db.add_all([link1, link2, link3])
    db.commit()

    result = link_service.search_by_original_url(db, "https://www.python.org")

    assert len(result) == 2
    short_codes = {item["short_code"] for item in result}
    assert short_codes == {"search1", "search2"}