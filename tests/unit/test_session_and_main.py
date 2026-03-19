from app.db import session as session_module


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_get_db_closes_session(monkeypatch):
    fake_session = FakeSession()
    monkeypatch.setattr(session_module, "SessionLocal", lambda: fake_session)

    generator = session_module.get_db()
    yielded = next(generator)

    assert yielded is fake_session

    try:
        next(generator)
    except StopIteration:
        pass

    assert fake_session.closed is True


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Service is running"}


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}