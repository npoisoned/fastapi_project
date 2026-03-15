from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services.cleanup_service import cleanup_service

scheduler = BackgroundScheduler()


def remove_expired_links_job():
    db = SessionLocal()
    try:
        deleted_count = cleanup_service.cleanup_expired_links(db)
        if deleted_count:
            print(f"[scheduler] deleted {deleted_count} expired links")
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            remove_expired_links_job,
            trigger="interval",
            minutes=1,
            id="remove_expired_links_job",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)