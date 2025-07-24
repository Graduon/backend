from pydantic import BaseModel, Field
from typing import Optional


class GoogleLoginSuccessResponse(BaseModel):
    message: str = Field(..., examples=["Google 로그인 성공"], description="성공 메시지")
    user: "GoogleUserInfo" = Field(..., description="Google 사용자 정보")


class GoogleUserInfo(BaseModel):
    id: int = Field(..., examples=[1], description="데이터베이스 사용자 ID")
    email: str = Field(..., examples=["user@example.com"], description="사용자 이메일")
    name: str = Field(..., examples=["손재혁"], description="사용자 이름")
    picture: Optional[str] = Field(None, examples=["https://lh3.googleusercontent.com/a/example"], description="프로필 사진 URL")


class GoogleLoginErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Google 로그인 실패: 인증 코드가 유효하지 않습니다"], description="오류 상세 메시지")
