import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
import app.main as main_module
import app.services.link_service as link_service_module
import app.services.cleanup_service as cleanup_service_module

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db, monkeypatch):
    monkeypatch.setattr(main_module, "start_scheduler", lambda: None)
    monkeypatch.setattr(main_module, "stop_scheduler", lambda: None)

    monkeypatch.setattr(link_service_module, "cache_link", lambda *args, **kwargs: None)
    monkeypatch.setattr(link_service_module, "get_cached_link", lambda *args, **kwargs: None)
    monkeypatch.setattr(link_service_module, "invalidate_link_cache", lambda *args, **kwargs: None)
    monkeypatch.setattr(cleanup_service_module, "invalidate_link_cache", lambda *args, **kwargs: None)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    main_module.app.dependency_overrides[get_db] = override_get_db

    with TestClient(main_module.app) as test_client:
        yield test_client

    main_module.app.dependency_overrides.clear()