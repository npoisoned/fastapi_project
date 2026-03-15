import secrets
import string
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.redis_client import cache_link, get_cached_link, invalidate_link_cache
from app.models.link import Link


class LinkService:
    def _generate_code(self, length: int = 6) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _get_unique_code(self, db: Session) -> str:
        while True:
            code = self._generate_code()
            exists = db.query(Link).filter(Link.short_code == code).first()
            if not exists:
                return code

    def _serialize(self, link: Link, base_url: Optional[str] = None) -> dict:
        data = {
            "short_code": link.short_code,
            "original_url": link.original_url,
            "created_at": link.created_at,
            "updated_at": link.updated_at,
            "expires_at": link.expires_at,
            "click_count": link.click_count,
            "last_accessed_at": link.last_accessed_at,
            "is_active": link.is_active,
            "user_id": link.user_id,
            "created_by_authenticated": link.created_by_authenticated,
        }
        if base_url:
            data["short_url"] = f"{base_url}/{link.short_code}"
        return data

    def _is_expired(self, link: Link) -> bool:
        if link.expires_at is None:
            return False
        return datetime.now(timezone.utc) > link.expires_at

    def create_link(
        self,
        db: Session,
        original_url: str,
        base_url: str,
        custom_alias: Optional[str] = None,
        expires_at=None,
        user_id: Optional[int] = None,
        created_by_authenticated: bool = False,
    ):
        if custom_alias:
            exists = db.query(Link).filter(Link.short_code == custom_alias).first()
            if exists:
                raise ValueError("Alias already exists")
            short_code = custom_alias
        else:
            short_code = self._get_unique_code(db)

        now = datetime.now(timezone.utc)

        link = Link(
            short_code=short_code,
            original_url=str(original_url),
            custom_alias=bool(custom_alias),
            user_id=user_id,
            created_by_authenticated=created_by_authenticated,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            click_count=0,
            last_accessed_at=None,
            is_active=True,
        )

        db.add(link)
        db.commit()
        db.refresh(link)

        cache_link(
            short_code=link.short_code,
            original_url=link.original_url,
            expires_at=link.expires_at,
            is_active=link.is_active,
        )

        return self._serialize(link, base_url=base_url)

    def get_link_entity(self, db: Session, short_code: str):
        return db.query(Link).filter(Link.short_code == short_code).first()

    def get_link(self, db: Session, short_code: str):
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            return None

        if not link.is_active:
            return None

        if self._is_expired(link):
            link.is_active = False
            db.commit()
            invalidate_link_cache(short_code)
            return None

        return link

    def get_link_info(self, db: Session, short_code: str):
        link = self.get_link(db, short_code)
        if not link:
            return None
        return self._serialize(link)

    def redirect_link(self, db: Session, short_code: str):
        cached = get_cached_link(short_code)
        now = datetime.now(timezone.utc)

        if cached:
            if not cached.get("is_active", True):
                invalidate_link_cache(short_code)
                return None

            expires_at_raw = cached.get("expires_at")
            if expires_at_raw:
                expires_at = datetime.fromisoformat(expires_at_raw)
                if now > expires_at:
                    link = db.query(Link).filter(Link.short_code == short_code).first()
                    if link:
                        link.is_active = False
                        db.commit()
                    invalidate_link_cache(short_code)
                    return None

            updated_rows = (
                db.query(Link)
                .filter(Link.short_code == short_code, Link.is_active.is_(True))
                .update(
                    {
                        Link.click_count: Link.click_count + 1,
                        Link.last_accessed_at: now,
                    },
                    synchronize_session=False,
                )
            )
            db.commit()

            if updated_rows == 0:
                invalidate_link_cache(short_code)
                return None

            return {"original_url": cached["original_url"]}

        link = self.get_link(db, short_code)
        if not link:
            return None

        link.click_count += 1
        link.last_accessed_at = now
        db.commit()
        db.refresh(link)

        cache_link(
            short_code=link.short_code,
            original_url=link.original_url,
            expires_at=link.expires_at,
            is_active=link.is_active,
        )

        return {"original_url": link.original_url}

    def update_link(self, db: Session, short_code: str, new_url: str):
        link = self.get_link(db, short_code)
        if not link:
            return None

        link.original_url = str(new_url)
        link.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(link)

        invalidate_link_cache(short_code)
        cache_link(
            short_code=link.short_code,
            original_url=link.original_url,
            expires_at=link.expires_at,
            is_active=link.is_active,
        )

        return self._serialize(link)

    def delete_link(self, db: Session, short_code: str):
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            return False

        link.is_active = False
        link.updated_at = datetime.now(timezone.utc)
        db.commit()

        invalidate_link_cache(short_code)
        return True

    def get_stats(self, db: Session, short_code: str):
        link = self.get_link(db, short_code)
        if not link:
            return None
        return self._serialize(link)

    def search_by_original_url(self, db: Session, original_url: str):
        links = (
            db.query(Link)
            .filter(
                Link.original_url == str(original_url),
                Link.is_active.is_(True),
            )
            .all()
        )

        result = []
        for link in links:
            if not self._is_expired(link):
                result.append(self._serialize(link))
        return result


link_service = LinkService()