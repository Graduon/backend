# 외부 라이브러리
from fastapi import FastAPI, Response, status, HTTPException, Body
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from sqlmodel import create_engine, SQLModel, Session, select
import itsdangerous
# 내부 라이브러리
from typing import Optional, Union, Annotated
from datetime import timedelta, datetime, timezone
import hashlib
# 직접 작성한 모듈
from models import User, utc_now_factory, generate_verification_code
from schemas.user import (LoginRequest, PasswordResetRequest, PasswordResetConfirm,
                          EmailVerificationRequest, EmailVerificationConfirm, SignupRequest)
from email_utility import send_reset_email, send_signup_verification_email
from env import (DATABASE_URL, COOKIE_KEY, MAIL_PASSWORD, MAIL_FROM,
                 MAIL_SERVER, MAIL_USERNAME, CODE_EXPIRE_SECONDS, MAX_VERIFICATION_TRIES,
                 VERIFICATION_DELAY)

app = FastAPI(
    title="Graduon",
    description="Graduon - 한국외국어대학교 컴퓨터공학부 졸업 요건 서비스",
    version="0.1.0",
)
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)
serializer = itsdangerous.URLSafeSerializer(COOKIE_KEY)
conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=465,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
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


def get_user_by_email(session: Session, email: Union[str, EmailStr]) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()


def authenticate_user(session: Session, email: Union[str, EmailStr], password: str) -> User:
    user = get_user_by_email(session, email)
    if not (user and verify_password(password, user.password_hash)):
        raise HTTPException(status_code=403, detail="계정이 없거나, 비밀번호를 틀렸습니다.")
    if not user.is_active:
        raise HTTPException(status_code=206, detail="이메일 인증이 완료되지 않았습니다.")
    return user


@app.get("/ping",
         status_code=status.HTTP_204_NO_CONTENT,
         summary="서버 기동 확인",
         response_description="서버와 데이터베이스가 정상 작동함을 응답 (204 No Content)",
         responses={
             204: {"description": "서버와 데이터베이스 모두 살아있음"},
             500: {"description": "서버 혹은 데이터베이스가 죽었음"},
         }
         )
async def does_server_alive(response: Response) -> Response:
    """
    서버, 데이터베이스가 살아있는지 확인하는 API입니다.

    ## 프론트엔드 지침
    서버가 살아있는지 확인할 때 사용할 수 있는 다재다능한 API입니다.
    """
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


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

    ## 프론트엔드 지침

    Json으로 `LoginRequest`를 구성하여 요청을 보내주세요.

    서버에서도 이메일과 비밀번호 유효성(글자수, 잘못된 이메일 형식 등)을 점검하지만,
    UI 측면에서 프론트엔드에서도 이 유효성 검증을 하는 것이 좋을 것 같습니다.

    보안상의 이유로, 이메일이나 비밀번호를 틀린 경우, 어떤 것을 틀렸는지 알려주지 않습니다.
    프론트엔드에서 이를 구현할 때 참고하세요.

    `206` 상태 응답이 오면 이메일 인증 코드를 요청하고, 입력할 수 있도록 적절히 안내해야 합니다.
    """
    with Session(engine) as session:
        user = authenticate_user(session, login_request.email, login_request.password)
        if login_request.session_continue:
            response.set_cookie(
                key='auth',
                value=cookie_generate(user.email),
                httponly=True,
                secure=True,
                max_age=365 * 24 * 60 * 60,
            )
        else:
            response.set_cookie(
                key='auth',
                value=cookie_generate(user.email),
                httponly=True,
                secure=True,
            )
        response.status_code = status.HTTP_204_NO_CONTENT
        return response


@app.post("/signup",
          status_code=status.HTTP_204_NO_CONTENT,
          summary="이메일 기반 회원가입",
          response_description="(204 No Content)",
          responses={
              204: {"description": "회원가입 성공"},
              400: {"description": "이미 가입한 이메일이 있음"},
              422: {"description": "요청 형식 오류 (유효성 검증 실패)"},
          },
          tags=["인증"]
          )
async def signup(signup_request: Annotated[SignupRequest, Body()], response: Response):
    """
    사용자의 이메일과 비밀번호를 기반으로 회원가입을 수행합니다.

    - **204 No Content**: 회원가입 성공
    - **400 Bad Request**: 이미 가입한 이메일
    - **422 Unprocessable Entity**: 유효성 검증 실패

    ## 프론트엔드 지침

    Json으로 `SignupRequest`를 구성하여 요청을 보내주세요.

    ### 204 No Content
    회원가입에 성공했다고 해서 이메일 코드를 자동으로 보내지 않습니다.
    프론트엔드에서 이메일 인증의 필요성, 방법을 설명해주고 이메일 인증 코드 송신을 유도해야 합니다.
    이메일 인증 코드 입력 후 통과까지 해야 사용자 인증 쿠키를 발급합니다. 자세한 인증 프로세스는 `README를` 참고하세요.

    ### 400 Bad Request
    데이터베이스에 이미 email-password 기반으로 가입한 이메일 주소가 있을 때 반환합니다.
    로그인 화면과 헷갈렸거나, 비밀번호를 까먹은 것일 수 있으므로 사용자에게 두 선택지를 제안해주면 좋을 것 같습니다.
    """
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
    status_code=status.HTTP_200_OK,
    summary="회원가입 이메일 인증 코드 발송",
    response_description="이메일로 인증 코드 발송 완료",
    responses={
        200: {"description": "코드 발송 완료"},
        400: {"description": "유효하지 않은 이메일"},
        429: {"description": "요청 제한 초과"},
        422: {"description": "요청 형식 오류 (유효성 검증 실패)"},
    },
    tags=["인증"]
)
async def request_signup_email_verification(request: EmailVerificationRequest):
    """
    ## 개요
    회원가입 후 사용자의 이메일로 인증 코드를 전송합니다.

    - 인증 코드는 6자리이며 일정 시간 동안만 유효합니다.
    - 일정 횟수 이상 요청 시, 일정 시간 동안 차단됩니다.

    ## 상세
    이 API를 호출하면 이메일로 인증 코드를 보냅니다.

    - **200 Success**: 이메일 송신 성공
    - **400 Bad Request**: 존재하지 않거나, 할 필요가 없는 이메일 주소
    - **429 Too Many**: 송신 한도 초과
    - **422 Unprocessable Entity**: 유효성 검증 실패

    ## 프론트엔드 지침

    Json을 `EmailVerificationRequest`를 구성하여 요청을 보내주세요.

    **이 작업은 기본적으로 소요 시간이 깁니다. 사용자에게 적절한 로딩 화면을 보여줄 필요가 있습니다.**

    ### 200 Success
    이메일을 보내는데 성공했습니다.
    필요가 있을지는 모르겠는데, 해당 계정에 남아있는 이메일 송신 한도를 json으로 보냅니다.
    이메일 송신 한도는 비밀번호 재설정용 송신과 공유하며, 어떤 작업(이메일 검증, 비밀번호 재설정)이든 성공하면 송신 한도를 0으로 초기화합니다.
    이메일 정책 관련해서는 `README`를 참고하세요.

    ### 400 Bad Request
    이미 인증되었기에 인증할 필요가 없거나, 회원가입하지 않은 이메일로 이 요청을 보내면 발생합니다.
    논리적으로 이미 인증된 계정이라면 이메일 인증 화면으로 돌아올 수 없고, 회원가입하지 않은 상태에서도 인증 화면으로 들어올 수 없기에 악의적이 요청을 의심합니다.

    ### 429 Too Many
    해당 이메일 주소에게 보낼 수 있는 이메일 송신 한도를 초과하였습니다.
    사용자에게 이메일 송신 정책을 소개해주세요.
    body text에 언제 다시 시도할 수 있는지 정보가 있습니다:
    ```text
    너무 잦은 요청입니다.
    7월 20일 14시 55분 뒤에 다시 시도하세요.
    ```
    """
    with (Session(engine) as session):
        user = get_user_by_email(session, request.email)
        if not user:
            raise HTTPException(status_code=400, detail="등록되지 않은 이메일입니다.")

        if user.is_active:
            raise HTTPException(status_code=400, detail="이미 인증된 계정입니다.")

        now = utc_now_factory()

        if user.email_verification_try >= MAX_VERIFICATION_TRIES:
            if user.last_verification_try and \
                    now < (residue_time := user.last_verification_try + timedelta(seconds=VERIFICATION_DELAY)):
                raise HTTPException(
                    status_code=429,
                    detail=f"""너무 잦은 요청입니다. 
                    {residue_time.month}월 {residue_time.day}일 {residue_time.hour}시 {residue_time.minute}분 
                    뒤에 다시 시도하세요."""
                )
        user_email = user.email
        code = generate_verification_code()

        user.verification_key = code
        user.key_created_at = now
        user.email_verification_try += 1
        user.last_verification_try = now
        user.updated_at = now

        current_verification_try = user.email_verification_try

        session.add(user)
        session.commit()

    await send_signup_verification_email(
        fm,
        user_email=user_email,
        verification_code=code,
        expires_minutes=CODE_EXPIRE_SECONDS // 60
    )
    return {"try": current_verification_try}


@app.post(
    "/signup/verify-email/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원가입 이메일 인증 확인",
    response_description="계정 인증 완료",
    responses={
        204: {"description": "이메일 인증 완료"},
        400: {"description": "코드 오류 또는 만료"},
        422: {"description": "요청 형식 오류 (유효성 검증 실패)"},
    },
    tags=["인증"]
)
def confirm_signup_email_verification(request: EmailVerificationConfirm):
    """
    ## 개요
    이메일로 발송된 인증 코드를 검증하여 계정을 활성화합니다.

    - 인증 성공 시, 내부 데이터베이스에서 `is_active = True`로 설정됩니다.

    ## 상세
    사용자가 이메일 인증 코드를 입력할 준비가 되었으면 이 API를 호출합니다.

    - **204 No Content**: 인증 성공.
    - **400 Bad Request**: 코드가 틀림 | 코드가 이미 만료됨 | 이미 인증한 계정 | 회원가입하지 않은 이메일

    ## 프론트엔드 구현 지침

    Json으로 `EmailVerificationConfirm`를 구성하여 요청을 보내주세요.

    ## 204 No Content
    사용자에게 로그인 화면으로 안내하세요.
    사용자가 직접 로그인을 수행해야 최종적으로 쿠키를 발급받을 수 있습니다.
    자세한 인증 프로세스는 `README를` 참고하세요.

    ## 400 Bad Request
    아래 네 가지 경우가 있으며, body text를 통해 각 경우를 식별할 수 있습니다.
    1. 애초에 가입한 이메일이 아닐 때.
    2. 이미 인증을 완료한 계정일 때.
    3. 인증 코드가 아예 틀린 경우.
    4. 인증 코드는 맞지만, 너무 늦게 입력한 경우.
    """
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

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/reset-password/request",
      status_code=status.HTTP_200_OK,
      summary="이메일 재설정용 코드 송신",
      description="""

      """,
      response_description="이메일 송신 완료",
      responses={
          200: {"description": "이메일 송신 완료"},
          400: {"description": "존재하지 않는 계정"},
          429: {"description": "요청 제한 초과"},
          422: {"description": "요청 형식 오류 (유효성 검증 실패)"},
      },
      tags=["인증"]
)
async def request_password_reset(request: PasswordResetRequest):
    """
    ## 개요
    이메일로 비밀번호 재설정용 인증 코드를 전송합니다.

    - 인증 코드는 6자리이며 일정 시간 동안만 유효합니다.
    - 일정 횟수 이상 요청 시, 일정 시간 동안 차단됩니다.

    ## 상세
    이 API를 호출하면 이메일로 인증 코드를 보냅니다.

    - **200 Success**: 이메일 송신 성공
    - **400 Bad Request**: 존재하지 않는 이메일 주소
    - **429 Too Many**: 송신 한도 초과
    - **422 Unprocessable Entity**: 유효성 검증 실패

    ## 프론트엔드 지침

    Json을 `PasswordResetRequest`를 구성하여 요청을 보내주세요.

    **이 작업은 기본적으로 소요 시간이 깁니다. 사용자에게 적절한 로딩 화면을 보여줄 필요가 있습니다.**

    ### 200 Success
    이메일을 보내는데 성공했습니다.
    필요가 있을지는 모르겠는데, 해당 계정에 남아있는 이메일 송신 한도를 json으로 보냅니다.
    이메일 송신 한도는 비밀번호 재설정용 송신과 공유하며, 어떤 작업(이메일 검증, 비밀번호 재설정)이든 성공하면 송신 한도를 0으로 초기화합니다.
    이메일 정책 관련해서는 `README`를 참고하세요.

    ### 400 Bad Request
    회원가입하지 않은 이메일로 이 요청을 보내면 발생합니다.

    ### 429 Too Many
    해당 이메일 주소에게 보낼 수 있는 이메일 송신 한도를 초과하였습니다.
    사용자에게 이메일 송신 정책을 소개해주세요.
    body text에 언제 다시 시도할 수 있는지 정보가 있습니다:
    ```text
    너무 잦은 요청입니다.
    7월 20일 14시 55분 뒤에 다시 시도하세요.
    ```
    """
    with Session(engine) as session:
        user: Optional[User] = get_user_by_email(session, request.email)
        if not user:
            raise HTTPException(status_code=400, detail="유효하지 않은 요청입니다.")

        now: datetime = utc_now_factory()

        if user.email_verification_try >= MAX_VERIFICATION_TRIES:
            if user.last_verification_try and now < (
            residue_time := user.last_verification_try.replace(tzinfo=timezone.utc) + timedelta(
                    seconds=VERIFICATION_DELAY)):
                raise HTTPException(
                    status_code=429,
                    detail=f"""너무 잦은 요청입니다. 
                    {residue_time.month}월 {residue_time.day}일 {residue_time.hour}시 {residue_time.minute}분 
                    뒤에 다시 시도하세요."""
                )
        user_email = user.email
        code = generate_verification_code()
        user.verification_key = code
        user.key_created_at = now
        user.email_verification_try += 1
        user.last_verification_try = now
        user.updated_at = now

        current_verification_try = user.email_verification_try

        session.add(user)
        session.commit()

    await send_reset_email(
        fm,
        user_email=user_email,
        verification_code=code,
        expires_minutes=CODE_EXPIRE_SECONDS // 60
    )
    return {"try": current_verification_try}


@app.post("/reset-password/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="비밀번호 재설정 완료",
    response_description="계정 비밀번호 변경 완료",
    responses={
        204: {"description": "비밀번호 변경 완료"},
        400: {"description": "코드 오류 또는 만료"},
        422: {"description": "요청 형식 오류 (유효성 검증 실패)"},
    },
    tags=["인증"]
)
def confirm_password_reset(request: PasswordResetConfirm, response: Response):
    """
    ## 개요
    이메일로 발송된 인증 코드를 검증하여 계정의 비밀번호를 변경합니다.

    ## 상세
    사용자가 비밀번호 재설정 인증 코드를 입력할 준비가 되었으면 이 API를 호출합니다.

    - **204 No Content**: 인증 성공.
    - **400 Bad Request**: 코드가 틀림 | 코드가 이미 만료됨 | 회원가입하지 않은 이메일

    ## 프론트엔드 구현 지침

    Json으로 `PasswordResetConfirm`를 구성하여 요청을 보내주세요.

    ## 204 No Content
    비밀번호 변경에 성공했습니다.
    로그인 화면으로 안내해주세요.

    ## 400 Bad Request
    아래 네 가지 경우가 있으며, body text를 통해 각 경우를 식별할 수 있습니다.
    1. 애초에 가입한 이메일이 아닐 때.
    3. 인증 코드가 아예 틀린 경우.
    4. 인증 코드는 맞지만, 너무 늦게 입력한 경우.
    """
    with Session(engine) as session:
        user: Optional[User] = get_user_by_email(session, request.email)
        if not user:
            raise HTTPException(status_code=400, detail="등록되지 않은 이메일입니다.")

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

    response.set_cookie(
        key='auth',
        value=" ",
        httponly=True,
        secure=True,
        max_age=0,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return Response(status_code=status.HTTP_204_NO_CONTENT)
