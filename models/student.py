from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from pydantic import model_validator


def utc_now_factory(tz=timezone.utc):
    return datetime.now(tz)


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True, unique=True, nullable=False)  # 학번
    name: str = Field(nullable=False)  # 이름
    
    # 4개 인증 모델 중 하나와 1:1 관계 (정확히 하나만 값을 가져야 함)
    user_email: Optional[str] = Field(default=None, foreign_key="user.email")
    google_user_id: Optional[int] = Field(default=None, foreign_key="googleuser.id")
    naver_user_id: Optional[int] = Field(default=None, foreign_key="naveruser.id")
    kakao_user_id: Optional[int] = Field(default=None, foreign_key="kakaouser.id")
    
    created_at: datetime = Field(default_factory=utc_now_factory)
    updated_at: datetime = Field(default_factory=utc_now_factory)
    
    @model_validator(mode='after')
    def validate_auth_fields(self):
        # 정확히 하나의 인증 타입만 설정되어야 함
        auth_fields = [self.user_email, self.google_user_id, self.naver_user_id, self.kakao_user_id]
        non_null_count = sum(1 for field in auth_fields if field is not None)
        if non_null_count != 1:
            raise ValueError("정확히 하나의 인증 타입과 연결되어야 합니다.")
        return self