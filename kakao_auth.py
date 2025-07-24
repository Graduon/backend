# 외부 라이브러리
from fastapi import APIRouter, Response, status, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from typing import Optional
import httpx
import secrets
import urllib.parse
# 직접 작성한 모듈
from models.kakao_user import KakaoUser
from schemas.kakao import KakaoLoginSuccessResponse, KakaoLoginErrorResponse
from env import DATABASE_URL, KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET, KAKAO_REDIRECT_URI
from auth_utils import get_serializer, cookie_generate, get_engine


router = APIRouter(tags=["Kakao OAuth2"], prefix="/auth/kakao")


def get_kakao_user_by_kakao_id(session: Session, kakao_id: str) -> Optional[KakaoUser]:
    """카카오 ID로 사용자 조회"""
    return session.exec(select(KakaoUser).where(KakaoUser.kakao_id == kakao_id)).first()


def create_kakao_user(session: Session, kakao_id: str, nickname: str = None, picture: str = None) -> KakaoUser:
    """새 카카오 사용자 생성"""
    user = KakaoUser(
        kakao_id=kakao_id,
        nickname=nickname,
        picture=picture
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


async def get_access_token(authorization_code: str) -> dict:
    """카카오 OAuth2 authorization code를 access token으로 교환"""
    token_url = "https://kauth.kakao.com/oauth/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "client_secret": KAKAO_CLIENT_SECRET,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": authorization_code
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        response.raise_for_status()
        return response.json()


async def get_user_info(access_token: str) -> dict:
    """카카오 access token으로 사용자 정보 조회"""
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)
        response.raise_for_status()
        return response.json()


@router.get("/login",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="카카오 OAuth2 로그인 시작",
    response_description="카카오 OAuth2 인증 페이지로 리다이렉트",
    responses={
        307: {"description": "카카오 로그인 페이지로 리다이렉트"},
        500: {"description": "OAuth2 설정 오류"}
    })
async def kakao_login():
    """
    ## 개요
    카카오 로그인 페이지로 사용자를 리다이렉트합니다.

    ## 상세

    카카오 OAuth2 로그인을 시작합니다.
    
    이 엔드포인트는 사용자를 카카오 로그인 페이지로 리다이렉트합니다.
    사용자가 카카오에서 로그인을 완료하면 `/auth/kakao/callback`으로 돌아옵니다.
    
    ## 프론트엔드 지침
    
    이 URL로 사용자를 리다이렉트하거나 새 창/탭에서 열어주세요.
    
    ```javascript
    // 현재 페이지에서 리다이렉트
    window.location.href = "https://localhost:8000/auth/kakao/login";
    
    // 또는 새 창에서 열기
    window.open("https://localhost:8000/auth/kakao/login", "_blank");
    ```
    
    ## 주의사항
    
    - HTTPS 환경인지 확인하세요.
    - 카카오는 이메일 정보를 제공하지 않으므로 닉네임과 프로필 이미지만 수집됩니다.
    """
    try:
        # CSRF 방지를 위한 state 값 생성
        state = secrets.token_urlsafe(32)
        
        # 카카오 로그인 URL 생성
        kakao_auth_url = "https://kauth.kakao.com/oauth/authorize"
        params = {
            "response_type": "code",
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "state": state
        }
        
        authorization_url = f"{kakao_auth_url}?{urllib.parse.urlencode(params)}"
        return RedirectResponse(url=authorization_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth2 설정 오류: {str(e)}")


@router.get("/callback",
    status_code=status.HTTP_200_OK,
    summary="카카오 OAuth2 콜백 처리",
    response_model=KakaoLoginSuccessResponse,
    responses={
        200: {
            "description": "카카오 로그인 성공 및 쿠키 발급",
            "model": KakaoLoginSuccessResponse
        },
        400: {
            "description": "카카오 인증 실패 또는 필수 정보 부족",
            "model": KakaoLoginErrorResponse
        },
        500: {"description": "서버 내부 오류"}
    })
async def kakao_callback(request: Request, response: Response, code: str = None, state: str = None, error: str = None):
    """
    ## 개요
    카카오에서 돌아온 사용자 정보로 로그인하거나 회원가입을 처리합니다.

    ## 상세
    카카오 OAuth2 콜백을 처리합니다.
    
    카카오에서 돌아온 사용자 정보를 검증하고, 데이터베이스에서 사용자를 찾거나
    새로운 사용자를 생성한 후 인증 쿠키를 발급합니다.
    
    ## 동작 과정
    
    1. 카카오에서 받은 authorization code를 access token으로 교환
    2. Access token으로 사용자 정보(ID, 닉네임, 프로필 이미지) 조회
    3. 데이터베이스에서 카카오 ID로 기존 사용자 조회
    4. 기존 사용자가 없으면 새 사용자 자동 생성 (회원가입)
    5. `auth-kakao` 쿠키 발급 (사용자 ID가 서명되어 저장)
    
    ## 쿠키 정보
    
    - **이름**: `auth-kakao`
    - **값**: itsdangerous로 서명된 사용자 ID
    - **유효기간**: 1년
    - **속성**: HTTPOnly, Secure
    
    ## 프론트엔드 지침
    
    이 엔드포인트는 카카오 OAuth2 flow의 일부로 **자동** 호출됩니다.
    **직접 호출하는 API 아닙니다.**
    
    성공 시 반환되는 사용자 정보를 사용하여 로그인 완료 처리를 하세요.
    
    ## 특이사항
    
    - 카카오는 **이메일 정보를 제공하지 않습니다.**
    - 닉네임과 프로필 이미지만 제공됩니다.
    
    ## 오류 처리
    
    - **400**: 카카오에서 필수 정보를 받지 못했거나 인증 실패
    - **500**: 서버 내부 오류 (데이터베이스 연결 실패 등)
    """
    
    # 에러가 있는 경우 처리
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"카카오 로그인 실패: {error}"
        )
    
    # code가 없는 경우
    if not code:
        raise HTTPException(
            status_code=400,
            detail="카카오에서 필수 정보(code)를 받을 수 없습니다. 다시 시도해주세요."
        )
    
    try:
        # Authorization code를 access token으로 교환
        token_data = await get_access_token(code)
        
        if "access_token" not in token_data:
            raise HTTPException(
                status_code=400,
                detail="카카오에서 access token을 받을 수 없습니다."
            )
        
        access_token = token_data["access_token"]
        
        # Access token으로 사용자 정보 조회
        user_info_response = await get_user_info(access_token)
        
        # 카카오 사용자 정보 추출
        kakao_id = str(user_info_response.get("id"))  # 숫자를 문자열로 변환
        kakao_account = user_info_response.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        nickname = profile.get("nickname")
        picture = profile.get("profile_image_url")
        
        if not kakao_id:
            raise HTTPException(
                status_code=400,
                detail="카카오에서 필수 정보(ID)를 받을 수 없습니다. 다시 시도해주세요."
            )
        
        # 데이터베이스에서 사용자 확인 또는 생성
        engine = get_engine()
        with Session(engine) as session:
            user = get_kakao_user_by_kakao_id(session, kakao_id)
            
            if not user:
                # 새 사용자 생성 (자동 회원가입)
                user = create_kakao_user(session, kakao_id, nickname, picture)
            
            # auth-kakao 쿠키 생성 및 설정
            serializer = get_serializer()
            cookie_value = cookie_generate(str(user.id), serializer)
            
            response.set_cookie(
                key='auth-kakao',
                value=cookie_value,
                httponly=True,
                secure=True,
                max_age=365 * 24 * 60 * 60  # 1년
            )
            
            return KakaoLoginSuccessResponse(
                message="카카오 로그인 성공",
                user={
                    "id": user.id,
                    "kakao_id": user.kakao_id,
                    "nickname": user.nickname,
                    "picture": user.picture
                }
            )
    
    except HTTPException:
        # 이미 HTTPException인 경우 다시 발생
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"카카오 로그인 실패: {str(e)}"
        )