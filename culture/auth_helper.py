# culture/auth_helper.py
from fastapi import HTTPException, status, Request, Depends
from sqlmodel import Session
from typing import Tuple, Optional
import itsdangerous

from auth_utils import get_engine, get_serializer, cookie_load
from auth import get_user_by_email
from google_auth import get_google_user_by_google_id
from kakao_auth import get_kakao_user_by_kakao_id  
from naver_auth import get_naver_user_by_naver_id


def get_current_user_info(
    request: Request, 
    engine = Depends(get_engine), 
    serializer: itsdangerous.URLSafeSerializer = Depends(get_serializer)
) -> Tuple[str, str]:
    """
    현재 로그인한 사용자의 정보를 반환합니다.
    모든 사용자 유형(email, google, kakao, naver)을 지원합니다.
    
    Returns:
        Tuple[user_type, user_identifier]: 사용자 유형과 식별자
    """
    
    print("=== DEBUG: get_current_user_info 시작 ===")
    print(f"request 객체: {request}")
    print(f"engine 객체: {engine}")
    print(f"serializer 객체: {serializer}")
    print(f"모든 쿠키: {request.cookies}")
    
    with Session(engine) as session:
        print(f"세션 생성됨: {session}")
        
        # 1. 일반 email 사용자 체크
        auth_cookie = request.cookies.get("auth")
        print(f"auth 쿠키: {auth_cookie}")
        if auth_cookie:
            user_email = cookie_load(auth_cookie, serializer)
            print(f"cookie_load 결과 (email): {user_email}")
            if user_email:
                user = get_user_by_email(session, user_email)
                print(f"get_user_by_email 결과: {user}")
                if user:
                    print(f"user.is_active: {user.is_active}")
                if user and user.is_active:
                    print(f"반환: ('email', '{user_email}')")
                    return ("email", user_email)
        
        # 2. Google 사용자 체크
        google_cookie = request.cookies.get("auth-google")
        print(f"auth-google 쿠키: {google_cookie}")
        if google_cookie:
            google_id = cookie_load(google_cookie, serializer)
            print(f"cookie_load 결과 (google): {google_id}")
            if google_id:
                user = get_google_user_by_google_id(session, google_id)
                print(f"get_google_user_by_google_id 결과: {user}")
                if user:
                    print(f"user.is_active: {user.is_active}")
                if user and user.is_active:
                    print(f"반환: ('google', '{google_id}')")
                    return ("google", google_id)
        
        # 3. Kakao 사용자 체크
        kakao_cookie = request.cookies.get("auth-kakao")
        print(f"auth-kakao 쿠키: {kakao_cookie}")
        if kakao_cookie:
            kakao_id = cookie_load(kakao_cookie, serializer)
            print(f"cookie_load 결과 (kakao): {kakao_id}")
            if kakao_id:
                user = get_kakao_user_by_kakao_id(session, kakao_id)
                print(f"get_kakao_user_by_kakao_id 결과: {user}")
                if user:
                    print(f"user.is_active: {user.is_active}")
                if user and user.is_active:
                    print(f"반환: ('kakao', '{kakao_id}')")
                    return ("kakao", kakao_id)
        
        # 4. Naver 사용자 체크
        naver_cookie = request.cookies.get("auth-naver")
        print(f"auth-naver 쿠키: {naver_cookie}")
        if naver_cookie:
            naver_id = cookie_load(naver_cookie, serializer)
            print(f"cookie_load 결과 (naver): {naver_id}")
            if naver_id:
                user = get_naver_user_by_naver_id(session, naver_id)
                print(f"get_naver_user_by_naver_id 결과: {user}")
                if user:
                    print(f"user.is_active: {user.is_active}")
                if user and user.is_active:
                    print(f"반환: ('naver', '{naver_id}')")
                    return ("naver", naver_id)
    
    print("모든 인증 방식에서 실패 - HTTPException 발생")
    # 모든 인증 방식에서 실패한 경우
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="로그인이 필요합니다."
    )


def get_user_display_info(
    user_type: str, 
    user_identifier: str,
    engine = Depends(get_engine)
) -> Optional[dict]:
    """
    사용자의 표시용 정보를 반환합니다 (닉네임, 이메일 등).
    """
    print(f"=== DEBUG: get_user_display_info 시작 ===")
    print(f"user_type: {user_type}")
    print(f"user_identifier: {user_identifier}")
    print(f"engine: {engine}")
    
    with Session(engine) as session:
        print(f"세션 생성됨: {session}")
        
        if user_type == "email":
            print("email 사용자 처리 중...")
            user = get_user_by_email(session, user_identifier)
            print(f"get_user_by_email 결과: {user}")
            result = {"email": user.email, "name": user.email} if user else None
            print(f"반환 값: {result}")
            return result
            
        elif user_type == "google":
            print("google 사용자 처리 중...")
            user = get_google_user_by_google_id(session, user_identifier)
            print(f"get_google_user_by_google_id 결과: {user}")
            result = {"email": user.email, "name": user.name} if user else None
            print(f"반환 값: {result}")
            return result
            
        elif user_type == "kakao":
            print("kakao 사용자 처리 중...")
            user = get_kakao_user_by_kakao_id(session, user_identifier)
            print(f"get_kakao_user_by_kakao_id 결과: {user}")
            result = {"nickname": user.nickname, "name": user.nickname or "카카오 사용자"} if user else None
            print(f"반환 값: {result}")
            return result
            
        elif user_type == "naver":
            print("naver 사용자 처리 중...")
            user = get_naver_user_by_naver_id(session, user_identifier)
            print(f"get_naver_user_by_naver_id 결과: {user}")
            result = {"email": user.email, "name": user.name} if user else None
            print(f"반환 값: {result}")
            return result
    
    print("알 수 없는 user_type - None 반환")
    return None