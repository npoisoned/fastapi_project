import app.tasks.scheduler as scheduler_module


class FakeDB:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeScheduler:
    def __init__(self, running=False):
        self.running = running
        self.add_job_called = False
        self.start_called = False
        self.shutdown_called = False

    def add_job(self, *args, **kwargs):
        self.add_job_called = True

    def start(self):
        self.start_called = True
        self.running = True

    def shutdown(self, wait=False):
        self.shutdown_called = True
        self.running = False


def test_remove_expired_links_job(monkeypatch):
    fake_db = FakeDB()

    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: fake_db)

    called = {"value": False}

    def fake_cleanup(db):
        called["value"] = True
        assert db is fake_db
        return 1

    monkeypatch.setattr(scheduler_module.cleanup_service, "cleanup_expired_links", fake_cleanup)

    scheduler_module.remove_expired_links_job()

    assert called["value"] is True
    assert fake_db.closed is True


def test_start_scheduler(monkeypatch):
    fake_scheduler = FakeScheduler(running=False)
    monkeypatch.setattr(scheduler_module, "scheduler", fake_scheduler)

    scheduler_module.start_scheduler()

    assert fake_scheduler.add_job_called is True
    assert fake_scheduler.start_called is True
    assert fake_scheduler.running is True


def test_stop_scheduler(monkeypatch):
    fake_scheduler = FakeScheduler(running=True)
    monkeypatch.setattr(scheduler_module, "scheduler", fake_scheduler)

    scheduler_module.stop_scheduler()

    assert fake_scheduler.shutdown_called is True
    assert fake_scheduler.running is False