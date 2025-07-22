# 외부 라이브러리
from fastapi import APIRouter, Response, status, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from typing import Optional
# 직접 작성한 모듈
from models.google_user import GoogleUser
from schemas.google import GoogleLoginSuccessResponse, GoogleLoginErrorResponse
from env import DATABASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from auth_utils import get_serializer, cookie_generate, get_engine


router = APIRouter(tags=["Google OAuth2"], prefix="/auth/google")


def get_google_flow():
    """Google OAuth2 Flow 객체 생성"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow


def get_google_user_by_google_id(session: Session, google_id: str) -> Optional[GoogleUser]:
    """Google ID로 사용자 조회"""
    return session.exec(select(GoogleUser).where(GoogleUser.google_id == google_id)).first()


def get_google_user_by_email(session: Session, email: str) -> Optional[GoogleUser]:
    """이메일로 Google 사용자 조회"""
    return session.exec(select(GoogleUser).where(GoogleUser.email == email)).first()


def create_google_user(session: Session, google_id: str, email: str, name: str, picture: str = None) -> GoogleUser:
    """새 Google 사용자 생성"""
    user = GoogleUser(
        google_id=google_id,
        email=email,
        name=name,
        picture=picture
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/login",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Google OAuth2 로그인 시작",
    response_description="Google OAuth2 인증 페이지로 리다이렉트",
    responses={
        307: {"description": "Google 로그인 페이지로 리다이렉트"},
        500: {"description": "OAuth2 설정 오류"}
    })
async def google_login():
    """
    ## 개요
    Google 로그인 페이지로 사용자를 리다이렉트합니다.

    ## 상세

    Google OAuth2 로그인을 시작합니다.
    
    이 엔드포인트는 사용자를 Google 로그인 페이지로 리다이렉트합니다.
    사용자가 Google에서 로그인을 완료하면 `/auth/google/callback`으로 돌아옵니다.
    
    ## 프론트엔드 지침
    
    이 URL로 사용자를 리다이렉트하거나 새 창/탭에서 열어주세요.
    
    ```javascript
    // 현재 페이지에서 리다이렉트
    window.location.href = "https://localhost:8000/auth/google/login";
    
    // 또는 새 창에서 열기
    window.open("https://localhost:8000/auth/google/login", "_blank");
    ```
    
    ## 주의사항
    
    - HTTPS 환경인지 확인하세요.
    """
    try:
        flow = get_google_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return RedirectResponse(url=authorization_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth2 설정 오류: {str(e)}")


@router.get("/callback",
    status_code=status.HTTP_200_OK,
    summary="Google OAuth2 콜백 처리",
    response_model=GoogleLoginSuccessResponse,
    responses={
        200: {
            "description": "Google 로그인 성공 및 쿠키 발급",
            "model": GoogleLoginSuccessResponse
        },
        400: {
            "description": "Google 인증 실패 또는 필수 정보 부족",
            "model": GoogleLoginErrorResponse
        },
        500: {"description": "서버 내부 오류"}
    })
async def google_callback(request: Request, response: Response):
    """
    ## 개요
    Google에서 돌아온 사용자 정보로 로그인하거나 회원가입을 처리합니다.

    ## 상세
    Google OAuth2 콜백을 처리합니다.
    
    Google에서 돌아온 사용자 정보를 검증하고, 데이터베이스에서 사용자를 찾거나
    새로운 사용자를 생성한 후 인증 쿠키를 발급합니다.
    
    ## 동작 과정
    
    1. Google에서 받은 authorization code를 access token으로 교환
    2. ID token에서 사용자 정보(이메일, 이름, 프로필 사진) 추출
    3. 데이터베이스에서 Google ID로 기존 사용자 조회
    4. 기존 사용자가 없으면 새 사용자 자동 생성 (회원가입)
    5. `auth-google` 쿠키 발급 (사용자 ID가 서명되어 저장)
    
    ## 쿠키 정보
    
    - **이름**: `auth-google`
    - **값**: itsdangerous로 서명된 사용자 ID
    - **유효기간**: 1년
    - **속성**: HTTPOnly, Secure
    
    ## 프론트엔드 지침
    
    이 엔드포인트는 Google OAuth2 flow의 일부로 **자동** 호출됩니다.
    **직접 호출하는 API 아닙니다.**
    **직접 호출하는 API 아닙니다.**
    **직접 호출하는 API 아닙니다.**
    **직접 호출하는 API 아닙니다.**
    **직접 호출하는 API 아닙니다.**
    **직접 호출하는 API 아닙니다.**
    **직접 호출하는 API 아닙니다.**
    **직접 호출하는 API 아닙니다.**
    **직접 호출하는 API 아닙니다.**
    
    성공 시 반환되는 사용자 정보를 사용하여 로그인 완료 처리를 하세요.
    
    ## 오류 처리
    
    - **400**: Google에서 필수 정보를 받지 못했거나 인증 실패
    - **500**: 서버 내부 오류 (데이터베이스 연결 실패 등)
    """
    flow = get_google_flow()
    
    try:
        # Authorization code를 token으로 교환
        authorization_response = str(request.url)
        flow.fetch_token(authorization_response=authorization_response)
        
        # Google ID token에서 사용자 정보 추출
        credentials = flow.credentials
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        google_id = id_info.get('sub')
        email = id_info.get('email')
        name = id_info.get('name')
        picture = id_info.get('picture')
        
        if not google_id or not email or not name:
            raise HTTPException(
                status_code=400, 
                detail="Google에서 필수 정보(ID, 이메일, 이름)를 받을 수 없습니다. 다시 시도해주세요."
            )
        
        # 데이터베이스에서 사용자 확인 또는 생성
        engine = get_engine()
        with Session(engine) as session:
            user = get_google_user_by_google_id(session, google_id)
            
            if not user:
                # 새 사용자 생성 (자동 회원가입)
                user = create_google_user(session, google_id, email, name, picture)
            
            # auth-google 쿠키 생성 및 설정
            serializer = get_serializer()
            cookie_value = cookie_generate(str(user.id), serializer)
            
            response.set_cookie(
                key='auth-google',
                value=cookie_value,
                httponly=True,
                secure=True,
                max_age=365 * 24 * 60 * 60  # 1년
            )
            
            return GoogleLoginSuccessResponse(
                message="Google 로그인 성공",
                user={
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "picture": user.picture
                }
            )
    
    except HTTPException:
        # 이미 HTTPException인 경우 다시 발생
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Google 로그인 실패: {str(e)}"
        )