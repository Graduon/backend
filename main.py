# 외부 라이브러리
from fastapi import FastAPI, Response, status, HTTPException, Request, Depends
from sqlmodel import create_engine, SQLModel, Session, select
from typing import Optional, Union
# 직접 작성한 모듈
from auth import router as auth_router, get_user_by_email
from google_auth import router as google_auth_router, get_google_user_by_google_id
from naver_auth import router as naver_auth_router, get_naver_user_by_naver_id
from kakao_auth import router as kakao_auth_router, get_kakao_user_by_kakao_id
from env import DATABASE_URL
from models.student import Student
from models.user import User
from models.google_user import GoogleUser
from models.naver_user import NaverUser
from models.kakao_user import KakaoUser
from schemas.student import StudentCreateRequest, StudentResponse
from auth_utils import get_engine, get_serializer, cookie_load

app = FastAPI(
    title="Graduon",
    description="Graduon - 한국외국어대학교 컴퓨터공학부 졸업 요건 서비스",
    version="0.1.0",
)
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)

# Include routers
app.include_router(auth_router)
app.include_router(google_auth_router)
app.include_router(naver_auth_router)
app.include_router(kakao_auth_router)



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


def authenticate_user_from_cookies(
    request: Request,
    session: Session = Depends(lambda: Session(engine)),
    serializer = Depends(get_serializer)
) -> tuple[str, Union[User, GoogleUser, NaverUser, KakaoUser]]:
    """쿠키에서 사용자 인증 정보를 추출하고 검증"""
    
    # Request 객체에서 모든 쿠키 가져오기
    cookies = request.cookies
    
    # 이메일 인증 확인
    if "auth" in cookies:
        auth_cookie = cookies.get("auth")
        if auth_cookie:
            user_email = cookie_load(auth_cookie, serializer)
            if user_email:
                user = get_user_by_email(session, user_email)
                if user and user.is_active:
                    return ("email", user)
    
    # Google 인증 확인
    if "auth-google" in cookies:
        auth_google_cookie = cookies.get("auth-google")
        if auth_google_cookie:
            google_id = cookie_load(auth_google_cookie, serializer)
            if google_id:
                user = get_google_user_by_google_id(session, google_id)
                if user and user.is_active:
                    return ("google", user)
    
    # Naver 인증 확인
    if "auth-naver" in cookies:
        auth_naver_cookie = cookies.get("auth-naver")
        if auth_naver_cookie:
            naver_id = cookie_load(auth_naver_cookie, serializer)
            if naver_id:
                user = get_naver_user_by_naver_id(session, naver_id)
                if user and user.is_active:
                    return ("naver", user)
    
    # Kakao 인증 확인
    if "auth-kakao" in cookies:
        auth_kakao_cookie = cookies.get("auth-kakao")
        if auth_kakao_cookie:
            kakao_id = cookie_load(auth_kakao_cookie, serializer)
            if kakao_id:
                user = get_kakao_user_by_kakao_id(session, kakao_id)
                if user and user.is_active:
                    return ("kakao", user)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="로그인이 필요합니다. 유효한 인증 쿠키가 없습니다."
    )


@app.post("/students",
          status_code=status.HTTP_201_CREATED,
          response_model=StudentResponse,
          summary="학생 정보 등록",
          description="현재 로그인된 사용자에 대해 학생 정보(학번, 이름)를 등록합니다.",
          responses={
              201: {"description": "학생 정보 등록 성공"},
              400: {"description": "잘못된 요청 (이미 등록된 학생, 중복된 학번 등)"},
              401: {"description": "인증 실패 (로그인 필요)"},
          })
async def create_student(
    student_request: StudentCreateRequest,
    auth_info: tuple[str, Union[User, GoogleUser, NaverUser, KakaoUser]] = Depends(authenticate_user_from_cookies),
    session: Session = Depends(lambda: Session(engine))
) -> StudentResponse:
    """
    현재 로그인된 사용자의 학생 정보를 등록합니다.
    
    ## 프론트엔드 지침
    - 로그인 상태에서만 호출 가능합니다
    - 한 사용자당 하나의 학생 정보만 등록 가능합니다
    - 학번은 전체 시스템에서 고유해야 합니다
    """
    auth_type, user = auth_info
    
    # 이미 등록된 학생인지 확인
    existing_student_stmt = select(Student)
    if auth_type == "email":
        existing_student_stmt = existing_student_stmt.where(Student.user_email == user.email)
    elif auth_type == "google":
        existing_student_stmt = existing_student_stmt.where(Student.google_user_id == user.id)
    elif auth_type == "naver":
        existing_student_stmt = existing_student_stmt.where(Student.naver_user_id == user.id)
    elif auth_type == "kakao":
        existing_student_stmt = existing_student_stmt.where(Student.kakao_user_id == user.id)
    
    existing_student = session.exec(existing_student_stmt).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 학생 정보가 등록되어 있습니다."
        )
    
    # 학번 중복 확인
    student_id_stmt = select(Student).where(Student.student_id == student_request.student_id)
    existing_student_id = session.exec(student_id_stmt).first()
    if existing_student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"학번 '{student_request.student_id}'는 이미 등록되어 있습니다."
        )
    
    # Student 레코드 생성
    student_data = {
        "student_id": student_request.student_id,
        "name": student_request.name,
    }
    
    if auth_type == "email":
        student_data["user_email"] = user.email
    elif auth_type == "google":
        student_data["google_user_id"] = user.id
    elif auth_type == "naver":
        student_data["naver_user_id"] = user.id
    elif auth_type == "kakao":
        student_data["kakao_user_id"] = user.id
    
    student = Student(**student_data)
    session.add(student)
    session.commit()
    session.refresh(student)
    
    # 응답 생성
    return StudentResponse(
        id=student.id,
        student_id=student.student_id,
        name=student.name,
        user_email=student.user_email,
        google_user_id=student.google_user_id,
        naver_user_id=student.naver_user_id,
        kakao_user_id=student.kakao_user_id,
        created_at=student.created_at.isoformat(),
        updated_at=student.updated_at.isoformat()
    )


@app.get("/logout",
         status_code=status.HTTP_204_NO_CONTENT,
         summary="로그아웃",
         description="어떤 방식으로 로그인했건, 모두 로그아웃되게 만들 수 있습니다.",
         responses={
             204: {"description": "로그아웃 성공"},
         })
async def logout(response: Response) -> Response:
    response.set_cookie(key="auth", value=" ", max_age=0)
    response.set_cookie(key="auth-google", value=" ", max_age=0)
    response.set_cookie(key="auth-naver", value=" ", max_age=0)
    response.set_cookie(key="auth-kakao", value=" ", max_age=0)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
