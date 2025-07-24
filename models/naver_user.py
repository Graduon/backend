from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional


def utc_now_factory(tz=timezone.utc):
    return datetime.now(tz)


class NaverUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    naver_id: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    name: str = Field(nullable=False)
    picture: Optional[str] = Field(default=None)
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now_factory)
    updated_at: datetime = Field(default_factory=utc_now_factory)