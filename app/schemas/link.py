from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator

RESERVED_ALIASES = {
    "health",
    "docs",
    "redoc",
    "openapi.json",
    "auth",
    "links",
}


class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, value):
        if value is None:
            return value

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        if not (3 <= len(value) <= 32):
            raise ValueError("Alias must be between 3 and 32 characters")

        if not set(value).issubset(allowed):
            raise ValueError("Alias can contain only letters, digits, '_' and '-'")

        if value in RESERVED_ALIASES:
            raise ValueError("This alias is reserved")

        return value


class LinkUpdate(BaseModel):
    original_url: HttpUrl


class LinkResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: HttpUrl
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class LinkInfo(BaseModel):
    short_code: str
    original_url: HttpUrl
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    click_count: int
    last_accessed_at: Optional[datetime] = None
    is_active: bool


class LinkStats(BaseModel):
    short_code: str
    original_url: HttpUrl
    created_at: datetime
    click_count: int
    last_accessed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None