# 외부 라이브러리
from sqlmodel import Session, create_engine
import itsdangerous
from typing import Optional
# 직접 작성한 모듈
from env import DATABASE_URL, COOKIE_KEY


def get_engine():
    """데이터베이스 엔진 생성"""
    return create_engine(DATABASE_URL, echo=True)


def get_serializer():
    """쿠키 서명을 위한 Serializer"""
    return itsdangerous.URLSafeSerializer(COOKIE_KEY)


def cookie_generate(data: str, serializer: itsdangerous.URLSafeSerializer) -> str:
    """쿠키 값 서명"""
    return serializer.dumps(data)


def cookie_load(cookie_string: str, serializer: itsdangerous.URLSafeSerializer) -> Optional[str]:
    """쿠키 복호화 및 검증"""
    try:
        return serializer.loads(cookie_string)
    except itsdangerous.BadSignature:
        return None
