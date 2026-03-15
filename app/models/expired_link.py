from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.db.session import Base


class ExpiredLinkHistory(Base):
    __tablename__ = "expired_links_history"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(32), nullable=False, index=True)
    original_url = Column(Text, nullable=False)
    user_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    expired_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    click_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(String(50), nullable=False)