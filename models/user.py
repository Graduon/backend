from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
import uuid
import secrets
import string


def utc_now_factory(tz=timezone.utc):
    return datetime.now(tz)

def generate_verification_code(length: int = 6) -> str:
    """6자리 영문 대문자+숫자 코드 생성"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class User(SQLModel, table=True):
    email: str = Field(index=True, unique=True, nullable=False, primary_key=True)
    password_hash: str = Field(nullable=False)

    is_active: bool = Field(default=False)

    verification_key: Optional[str] = Field(default_factory=generate_verification_code)
    key_created_at: Optional[datetime] = Field(default_factory=utc_now_factory)
    email_verification_try: int = Field(default=0)
    last_verification_try: Optional[datetime] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=utc_now_factory)
    updated_at: datetime = Field(default_factory=utc_now_factory)


if __name__ == "__main__":
    DATABASE_URL = "sqlite:///../app.db"
    from sqlmodel import create_engine, Session

    import hashlib
    def hash_password(password: str) -> str:
        return hashlib.blake2b(password.encode()).hexdigest()

    engine = create_engine(DATABASE_URL, echo=True)
    dummy_users = [
        {"email": "alice@example.com", "password": "alice123"},
        {"email": "bob@example.com", "password": "bob456"},
        {"email": "charlie@example.com", "password": "charlie789"},
    ]

    with Session(engine) as session:
        for entry in dummy_users:
            email = entry["email"]
            password_hash = hash_password(entry["password"])

            # 이미 존재하는 이메일이면 skip
            existing = session.get(User, email)
            if existing:
                print(f"❗ 이미 존재: {email}, 건너뜀")
                continue

            user = User(email=email, password_hash=password_hash)
            session.add(user)

        session.commit()
        print("✅ 더미 사용자 데이터 삽입 완료")
