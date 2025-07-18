from typing import Optional, Union, Annotated

from fastapi import FastAPI, Response, status, HTTPException, Body
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from models import User, utc_now_factory, generate_verification_code
from schemas.user import LoginRequest, PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest, EmailVerificationConfirm, SignupRequest
from email_utility import send_reset_email, send_signup_verification_email
from env import DATABASE_URL, COOKIE_KEY, MAIL_PASSWORD, MAIL_FROM, MAIL_SERVER, MAIL_USERNAME, CODE_EXPIRE_SECONDS, MAX_VERIFICATION_TRIES, VERIFICATION_DELAY
from sqlmodel import create_engine, SQLModel, Session, select
from datetime import timedelta, datetime, timezone
import hashlib
import itsdangerous


app = FastAPI()
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)
serializer = itsdangerous.URLSafeSerializer(COOKIE_KEY)
conf = ConnectionConfig(
    MAIL_USERNAME = MAIL_USERNAME,
    MAIL_PASSWORD = MAIL_PASSWORD,
    MAIL_FROM = MAIL_FROM,
    MAIL_PORT = 465,
    MAIL_SERVER = MAIL_SERVER,
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)
fm = FastMail(conf)

def cookie_generate(original_string: str) -> str:
    """쿠키 값 서명"""
    return serializer.dumps(original_string)

def cookie_load(cookie_string: str) -> Optional[str]:
    """쿠키 복호화 및 검증"""
    try:
        return serializer.loads(cookie_string)
    except itsdangerous.BadSignature:
        return None

def hash_password(password: str) -> str:
    return hashlib.blake2b(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

@app.get("/ping", status_code=204)
async def does_server_alive(response: Response) -> Response:
    """
    서버, 데이터베이스가 살아있는지 확인하는 API입니다.
    """
    response.status_code = status.HTTP_204_NO_CONTENT
    return response

def get_user_by_email(session: Session, email: Union[str, EmailStr]) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()

def authenticate_user(session: Session, email: Union[str, EmailStr], password: str) -> User:
    user = get_user_by_email(session, email)
    if not (user and verify_password(password, user.password_hash)):
        raise HTTPException(status_code=403, detail="계정이 없거나, 비밀번호를 틀렸습니다.")
    if not user.is_active:
        raise HTTPException(status_code=206, detail="이메일 인증이 완료되지 않았습니다.")
    return user

@app.post(
    "/login",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="이메일 기반 로그인",
    response_description="인증 성공 시 쿠키 발급 (204 No Content)",
    responses={
        204: {"description": "로그인 성공"},
        206: {"description": "이메일 인증 미완료"},
        403: {"description": "이메일 또는 비밀번호 오류"},
        422: {"description": "요청 형식 오류 (유효성 검증 실패)"},
    },
    tags=["인증"]
)
async def email_login(login_request: LoginRequest, response: Response):
    """
    사용자의 이메일과 비밀번호를 기반으로 로그인을 수행합니다.

    - **204 No Content**: 로그인 성공 및 쿠키 발급
    - **206 Partial Content**: 이메일 인증이 완료되지 않음
    - **403 Forbidden**: 이메일 또는 비밀번호 오류
    - **422 Unprocessable Entity**: 유효성 검증 실패

    로그인 성공 시 `auth` 쿠키를 HTTPOnly 속성으로 설정합니다.
    """
    with Session(engine) as session:
        user = authenticate_user(session, login_request.email, login_request.password)
        response.set_cookie(
            key='auth',
            value=cookie_generate(user.email),
            httponly=True,
            secure=True,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/signup")
async def signup(signup_request: Annotated[SignupRequest, Body()], response: Response):
    with Session(engine) as session:
        user: Optional[User] = get_user_by_email(session, signup_request.email)
        if user:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
        new_user = User(email=signup_request.email, password_hash=hash_password(signup_request.password))
        session.add(new_user)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post(
    "/signup/verify-email/request",
    summary="회원가입 이메일 인증 코드 발송",
    description="""
회원가입 후 사용자의 이메일로 인증 코드를 전송합니다.

- 인증 코드는 6자리이며 일정 시간 동안만 유효합니다.
- 일정 횟수 이상 요청 시, 일정 시간 동안 차단됩니다.
""",
    response_description="이메일로 인증 코드 발송 완료",
    responses={
        200: {"description": "코드 발송 완료"},
        400: {"description": "유효하지 않은 이메일"},
        429: {"description": "요청 제한 초과"},
    },
    tags=["인증"]
)
async def request_signup_email_verification(request: EmailVerificationRequest):
    with Session(engine) as session:
        user = get_user_by_email(session, request.email)
        if not user:
            raise HTTPException(status_code=400, detail="등록되지 않은 이메일입니다.")

        if user.is_active:
            raise HTTPException(status_code=400, detail="이미 인증된 계정입니다.")

        now = utc_now_factory()

        if user.email_verification_try >= MAX_VERIFICATION_TRIES:
            if user.last_verification_try and now < (residue_time := user.last_verification_try + timedelta(seconds=VERIFICATION_DELAY)):
                raise HTTPException(
                    status_code=429,
                    detail=f"요청이 너무 잦습니다. {residue_time}초 후에 다시 시도하세요."
                )
        user_email = user.email
        code = generate_verification_code()

        user.verification_key = code
        user.key_created_at = now
        user.email_verification_try += 1
        user.last_verification_try = now
        user.updated_at = now

        session.add(user)
        session.commit()

    await send_signup_verification_email(
        fm,
        user_email=user_email,
        verification_code=code,
        expires_minutes=CODE_EXPIRE_SECONDS // 60
    )
    return {"message": "인증 코드가 이메일로 발송되었습니다."}


@app.post(
    "/signup/verify-email/confirm",
    summary="회원가입 이메일 인증 확인",
    description="""
이메일로 발송된 인증 코드를 검증하여 계정을 활성화합니다.

- 인증 성공 시, `is_active = True`로 설정됩니다.
""",
    response_description="계정 인증 완료",
    responses={
        200: {"description": "이메일 인증 완료"},
        400: {"description": "코드 오류 또는 만료"},
    },
    tags=["인증"]
)
def confirm_signup_email_verification(request: EmailVerificationConfirm):
    with Session(engine) as session:
        user = get_user_by_email(session, request.email)
        if not user:
            raise HTTPException(status_code=400, detail="등록되지 않은 이메일입니다.")

        if user.is_active:
            raise HTTPException(status_code=400, detail="이미 인증된 계정입니다.")

        if not user.verification_key or user.verification_key.upper() != request.code.upper():
            raise HTTPException(status_code=400, detail="인증 코드가 일치하지 않습니다.")
        now = utc_now_factory()
        if now > user.key_created_at.replace(tzinfo=timezone.utc) + timedelta(seconds=CODE_EXPIRE_SECONDS):
            raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다.")

        user.is_active = True
        user.verification_key = None
        user.key_created_at = None
        user.email_verification_try = 0
        user.last_verification_try = None
        user.updated_at = now

        session.add(user)
        session.commit()

    return {"message": "이메일 인증이 완료되었습니다."}

@app.post("/reset-password/request")
async def request_password_reset(request: PasswordResetRequest):
    """
    1) 6자리 코드 생성
    2) User.verification_key, key_created_at, email_verification_try 갱신
    3) 이메일 발송
    """
    with Session(engine) as session:
        user: Optional[User] = get_user_by_email(session, request.email)
        if not user:
            raise HTTPException(status_code=400, detail="유효하지 않은 요청입니다.")

        now: datetime = utc_now_factory()

        if user.email_verification_try >= MAX_VERIFICATION_TRIES:
            if user.last_verification_try and now < (residue_time := user.last_verification_try.replace(tzinfo=timezone.utc) + timedelta(
                    seconds=VERIFICATION_DELAY)):
                raise HTTPException(
                    status_code=429,
                    detail=f"너무 잦은 요청입니다. {residue_time.month}월 {residue_time.day}일 {residue_time.hour}시 {residue_time.minute}분 뒤에 다시 시도하세요."
                )
        user_email = user.email
        code = generate_verification_code()
        user.verification_key = code
        user.key_created_at = now
        user.email_verification_try += 1
        user.last_verification_try = now
        user.updated_at = now

        session.add(user)
        session.commit()

    await send_reset_email(
        fm,
        user_email=user_email,
        verification_code=code,
        expires_minutes=CODE_EXPIRE_SECONDS // 60
    )
    return {"message": "비밀번호 재설정 인증 코드를 이메일로 발송했습니다."}


@app.post("/reset-password/confirm")
def confirm_password_reset(request: PasswordResetConfirm):
    """
    1) 코드 일치 및 만료 확인
    2) 비밀번호 해시 저장
    3) verification_key 초기화(Optional)
    """
    with Session(engine) as session:
        user: Optional[User] = get_user_by_email(session, request.email)
        if not user:
            raise HTTPException(status_code=400, detail="유효하지 않은 요청입니다.")

        if not user.verification_key or user.verification_key.upper() != request.code.upper():
            raise HTTPException(status_code=400, detail="인증 코드가 일치하지 않습니다.")
        now = utc_now_factory()
        if now > user.key_created_at.replace(tzinfo=timezone.utc) + timedelta(seconds=CODE_EXPIRE_SECONDS):
            raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다.")

        user.password_hash = hash_password(request.new_password)
        user.updated_at = now
        user.verification_key = None
        user.key_created_at = None
        user.email_verification_try = 0
        user.last_verification_try = None

        session.add(user)
        session.commit()

    return {"message": "비밀번호를 성공적으로 변경하였습니다."}
