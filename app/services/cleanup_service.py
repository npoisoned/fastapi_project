from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.redis_client import invalidate_link_cache
from app.models.expired_link import ExpiredLinkHistory
from app.models.link import Link


class CleanupService:
    def cleanup_expired_links(self, db: Session) -> int:
        now = datetime.now(timezone.utc)

        expired_links = (
            db.query(Link)
            .filter(
                Link.is_active.is_(True),
                Link.expires_at.is_not(None),
                Link.expires_at <= now,
            )
            .all()
        )

        deleted_count = 0

        for link in expired_links:
            history_item = ExpiredLinkHistory(
                short_code=link.short_code,
                original_url=link.original_url,
                user_id=link.user_id,
                created_at=link.created_at,
                expired_at=now,
                click_count=link.click_count,
                last_accessed_at=link.last_accessed_at,
                reason="expired",
            )

            db.add(history_item)
            invalidate_link_cache(link.short_code)
            db.delete(link)
            deleted_count += 1

        db.commit()
        return deleted_count

    def get_expired_links_history(self, db: Session, limit: int = 100):
        items = (
            db.query(ExpiredLinkHistory)
            .order_by(ExpiredLinkHistory.expired_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "short_code": item.short_code,
                "original_url": item.original_url,
                "user_id": item.user_id,
                "created_at": item.created_at,
                "expired_at": item.expired_at,
                "click_count": item.click_count,
                "last_accessed_at": item.last_accessed_at,
                "reason": item.reason,
            }
            for item in items
        ]


cleanup_service = CleanupService()