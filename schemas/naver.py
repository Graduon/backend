from pydantic import BaseModel, Field
from typing import Optional


class NaverLoginSuccessResponse(BaseModel):
    message: str = Field(..., examples=["네이버 로그인 성공"], description="성공 메시지")
    user: "NaverUserInfo" = Field(..., description="네이버 사용자 정보")


class NaverUserInfo(BaseModel):
    id: int = Field(..., examples=[1], description="데이터베이스 사용자 ID")
    email: str = Field(..., examples=["user@naver.com"], description="사용자 이메일")
    name: str = Field(..., examples=["홍길동"], description="사용자 이름")
    picture: Optional[str] = Field(None, examples=["https://ssl.pstatic.net/static/pwe/address/img_profile.png"], description="프로필 사진 URL")


class NaverLoginErrorResponse(BaseModel):
    detail: str = Field(..., examples=["네이버 로그인 실패: 인증 코드가 유효하지 않습니다"], description="오류 상세 메시지")