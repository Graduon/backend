from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional


def utc_now_factory(tz=timezone.utc):
    return datetime.now(tz)


class KakaoUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kakao_id: str = Field(index=True, unique=True, nullable=False)
    nickname: Optional[str] = Field(default=None)
    picture: Optional[str] = Field(default=None)
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now_factory)
    updated_at: datetime = Field(default_factory=utc_now_factory)