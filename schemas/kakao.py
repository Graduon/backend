from pydantic import BaseModel, Field
from typing import Optional


class KakaoLoginSuccessResponse(BaseModel):
    message: str = Field(..., examples=["카카오 로그인 성공"], description="성공 메시지")
    user: "KakaoUserInfo" = Field(..., description="카카오 사용자 정보")


class KakaoUserInfo(BaseModel):
    id: int = Field(..., examples=[1], description="데이터베이스 사용자 ID")
    kakao_id: str = Field(..., examples=["123456789"], description="카카오에서 제공하는 사용자 ID")
    nickname: Optional[str] = Field(None, examples=["홍길동"], description="사용자 닉네임")
    picture: Optional[str] = Field(None, examples=["http://k.kakaocdn.net/dn/profile.jpg"], description="프로필 사진 URL")


class KakaoLoginErrorResponse(BaseModel):
    detail: str = Field(..., examples=["카카오 로그인 실패: 인증 코드가 유효하지 않습니다"], description="오류 상세 메시지")