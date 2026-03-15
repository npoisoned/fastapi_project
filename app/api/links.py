from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.link import LinkCreate, LinkUpdate
from app.services.cleanup_service import cleanup_service
from app.services.link_service import link_service

router = APIRouter(tags=["links"])


@router.post("/links/shorten")
def shorten_link(
    payload: LinkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    base_url = str(request.base_url).rstrip("/")

    try:
        created_link = link_service.create_link(
            db=db,
            original_url=str(payload.original_url),
            base_url=base_url,
            custom_alias=payload.custom_alias,
            expires_at=payload.expires_at,
            user_id=current_user.id if current_user else None,
            created_by_authenticated=bool(current_user),
        )
        return created_link
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/links/search")
def search_link(original_url: str, db: Session = Depends(get_db)):
    return link_service.search_by_original_url(db, original_url)


@router.get("/links/expired/history")
def get_expired_links_history(limit: int = 100, db: Session = Depends(get_db)):
    return cleanup_service.get_expired_links_history(db, limit)


@router.get("/links/{short_code}")
def get_link_info(short_code: str, db: Session = Depends(get_db)):
    link_data = link_service.get_link_info(db, short_code)
    if not link_data:
        raise HTTPException(status_code=404, detail="Link not found")
    return link_data


@router.put("/links/{short_code}")
def update_link(
    short_code: str,
    payload: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = link_service.get_link_entity(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if not link.created_by_authenticated or link.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can update only your own links",
        )

    updated = link_service.update_link(db, short_code, str(payload.original_url))
    if not updated:
        raise HTTPException(status_code=404, detail="Link not found")

    return updated


@router.delete("/links/{short_code}")
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = link_service.get_link_entity(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if not link.created_by_authenticated or link.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can delete only your own links",
        )

    deleted = link_service.delete_link(db, short_code)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")

    return {"message": "Link deleted successfully"}


@router.get("/links/{short_code}/stats")
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    stats = link_service.get_stats(db, short_code)
    if not stats:
        raise HTTPException(status_code=404, detail="Link not found")
    return stats


@router.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    link = link_service.redirect_link(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found or expired")

    return RedirectResponse(url=link["original_url"], status_code=307)