# 외부 라이브러리
from fastapi import APIRouter, Response, status, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from typing import Optional
import httpx
import secrets
import urllib.parse
# 직접 작성한 모듈
from models.naver_user import NaverUser
from schemas.naver import NaverLoginSuccessResponse, NaverLoginErrorResponse
from env import DATABASE_URL, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NAVER_REDIRECT_URI
from auth_utils import get_serializer, cookie_generate, get_engine


router = APIRouter(tags=["Naver OAuth2"], prefix="/auth/naver")


def get_naver_user_by_naver_id(session: Session, naver_id: str) -> Optional[NaverUser]:
    """네이버 ID로 사용자 조회"""
    return session.exec(select(NaverUser).where(NaverUser.naver_id == naver_id)).first()


def get_naver_user_by_email(session: Session, email: str) -> Optional[NaverUser]:
    """이메일로 네이버 사용자 조회"""
    return session.exec(select(NaverUser).where(NaverUser.email == email)).first()


def create_naver_user(session: Session, naver_id: str, email: str, name: str, picture: str = None) -> NaverUser:
    """새 네이버 사용자 생성"""
    user = NaverUser(
        naver_id=naver_id,
        email=email,
        name=name,
        picture=picture
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


async def get_access_token(authorization_code: str, state: str) -> dict:
    """네이버 OAuth2 authorization code를 access token으로 교환"""
    token_url = "https://nid.naver.com/oauth2.0/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": NAVER_CLIENT_ID,
        "client_secret": NAVER_CLIENT_SECRET,
        "code": authorization_code,
        "state": state
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        response.raise_for_status()
        return response.json()


async def get_user_info(access_token: str) -> dict:
    """네이버 access token으로 사용자 정보 조회"""
    user_info_url = "https://openapi.naver.com/v1/nid/me"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)
        response.raise_for_status()
        return response.json()


@router.get("/login",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="네이버 OAuth2 로그인 시작",
    response_description="네이버 OAuth2 인증 페이지로 리다이렉트",
    responses={
        307: {"description": "네이버 로그인 페이지로 리다이렉트"},
        500: {"description": "OAuth2 설정 오류"}
    })
async def naver_login():
    """
    ## 개요
    네이버 로그인 페이지로 사용자를 리다이렉트합니다.

    ## 상세

    네이버 OAuth2 로그인을 시작합니다.
    
    이 엔드포인트는 사용자를 네이버 로그인 페이지로 리다이렉트합니다.
    사용자가 네이버에서 로그인을 완료하면 `/auth/naver/callback`으로 돌아옵니다.
    
    ## 프론트엔드 지침
    
    이 URL로 사용자를 리다이렉트하거나 새 창/탭에서 열어주세요.
    
    ```javascript
    // 현재 페이지에서 리다이렉트
    window.location.href = "https://localhost:8000/auth/naver/login";
    
    // 또는 새 창에서 열기
    window.open("https://localhost:8000/auth/naver/login", "_blank");
    ```
    
    ## 주의사항
    
    - HTTPS 환경인지 확인하세요.
    """
    try:
        # CSRF 방지를 위한 state 값 생성
        state = secrets.token_urlsafe(32)
        
        # 네이버 로그인 URL 생성
        naver_auth_url = "https://nid.naver.com/oauth2.0/authorize"
        params = {
            "response_type": "code",
            "client_id": NAVER_CLIENT_ID,
            "redirect_uri": NAVER_REDIRECT_URI,
            "state": state
        }
        
        authorization_url = f"{naver_auth_url}?{urllib.parse.urlencode(params)}"
        return RedirectResponse(url=authorization_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth2 설정 오류: {str(e)}")


@router.get("/callback",
    status_code=status.HTTP_200_OK,
    summary="네이버 OAuth2 콜백 처리",
    response_model=NaverLoginSuccessResponse,
    responses={
        200: {
            "description": "네이버 로그인 성공 및 쿠키 발급",
            "model": NaverLoginSuccessResponse
        },
        400: {
            "description": "네이버 인증 실패 또는 필수 정보 부족",
            "model": NaverLoginErrorResponse
        },
        500: {"description": "서버 내부 오류"}
    })
async def naver_callback(request: Request, response: Response, code: str = None, state: str = None, error: str = None):
    """
    ## 개요
    네이버에서 돌아온 사용자 정보로 로그인하거나 회원가입을 처리합니다.

    ## 상세
    네이버 OAuth2 콜백을 처리합니다.
    
    네이버에서 돌아온 사용자 정보를 검증하고, 데이터베이스에서 사용자를 찾거나
    새로운 사용자를 생성한 후 인증 쿠키를 발급합니다.
    
    ## 동작 과정
    
    1. 네이버에서 받은 authorization code를 access token으로 교환
    2. Access token으로 사용자 정보(이메일, 이름, 프로필 사진 등) 조회
    3. 데이터베이스에서 네이버 ID로 기존 사용자 조회
    4. 기존 사용자가 없으면 새 사용자 자동 생성 (회원가입)
    5. `auth-naver` 쿠키 발급 (사용자 ID가 서명되어 저장)
    
    ## 쿠키 정보
    
    - **이름**: `auth-naver`
    - **값**: itsdangerous로 서명된 사용자 ID
    - **유효기간**: 1년
    - **속성**: HTTPOnly, Secure
    
    ## 프론트엔드 지침
    
    이 엔드포인트는 네이버 OAuth2 flow의 일부로 **자동** 호출됩니다.
    **직접 호출하는 API 아닙니다.**
    
    성공 시 반환되는 사용자 정보를 사용하여 로그인 완료 처리를 하세요.
    
    ## 오류 처리
    
    - **400**: 네이버에서 필수 정보를 받지 못했거나 인증 실패
    - **500**: 서버 내부 오류 (데이터베이스 연결 실패 등)
    """
    
    # 에러가 있는 경우 처리
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"네이버 로그인 실패: {error}"
        )
    
    # code나 state가 없는 경우
    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="네이버에서 필수 정보(code, state)를 받을 수 없습니다. 다시 시도해주세요."
        )
    
    try:
        # Authorization code를 access token으로 교환
        token_data = await get_access_token(code, state)
        
        if "access_token" not in token_data:
            raise HTTPException(
                status_code=400,
                detail="네이버에서 access token을 받을 수 없습니다."
            )
        
        access_token = token_data["access_token"]
        
        # Access token으로 사용자 정보 조회
        user_info_response = await get_user_info(access_token)
        
        if user_info_response.get("resultcode") != "00":
            raise HTTPException(
                status_code=400,
                detail=f"네이버 사용자 정보 조회 실패: {user_info_response.get('message', '알 수 없는 오류')}"
            )
        
        user_info = user_info_response.get("response", {})
        naver_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("profile_image")
        
        if not naver_id or not email or not name:
            raise HTTPException(
                status_code=400,
                detail="네이버에서 필수 정보(ID, 이메일, 이름)를 받을 수 없습니다. 다시 시도해주세요."
            )
        
        # 데이터베이스에서 사용자 확인 또는 생성
        engine = get_engine()
        with Session(engine) as session:
            user = get_naver_user_by_naver_id(session, naver_id)
            
            if not user:
                # 새 사용자 생성 (자동 회원가입)
                user = create_naver_user(session, naver_id, email, name, picture)
            
            # 다른 인증 방식의 쿠키들을 만료시킴
            response.set_cookie(key='auth', value='', expires=0, httponly=True, secure=True)
            response.set_cookie(key='auth-google', value='', expires=0, httponly=True, secure=True)
            response.set_cookie(key='auth-kakao', value='', expires=0, httponly=True, secure=True)
            
            # auth-naver 쿠키 생성 및 설정
            serializer = get_serializer()
            cookie_value = cookie_generate(str(user.naver_id), serializer)
            
            response.set_cookie(
                key='auth-naver',
                value=cookie_value,
                httponly=True,
                secure=True,
                max_age=365 * 24 * 60 * 60  # 1년
            )
            
            return NaverLoginSuccessResponse(
                message="네이버 로그인 성공",
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
            detail=f"네이버 로그인 실패: {str(e)}"
        )