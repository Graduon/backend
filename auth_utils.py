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
    print(f"=== DEBUG: cookie_load 시작 ===")
    print(f"입력 cookie_string: '{cookie_string}'")
    print(f"cookie_string 타입: {type(cookie_string)}")
    print(f"cookie_string 길이: {len(cookie_string)}")
    print(f"serializer 객체: {serializer}")
    print(f"serializer 키: {serializer.secret_key}")
    
    try:
        result = serializer.loads(cookie_string)
        print(f"serializer.loads() 성공!")
        print(f"복호화된 결과: '{result}'")
        print(f"결과 타입: {type(result)}")
        return result
    except itsdangerous.BadSignature as e:
        print(f"BadSignature 예외 발생: {e}")
        print(f"예외 타입: {type(e)}")
        return None
    except Exception as e:
        print(f"기타 예외 발생: {e}")
        print(f"예외 타입: {type(e)}")
        return None
