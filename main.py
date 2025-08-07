# 외부 라이브러리
from fastapi import FastAPI, Response, status, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from sqlmodel import create_engine, SQLModel, Session, select
from typing import Optional, Union, List
# 직접 작성한 모듈
from auth import router as auth_router, get_user_by_email
from google_auth import router as google_auth_router, get_google_user_by_google_id
from naver_auth import router as naver_auth_router, get_naver_user_by_naver_id
from kakao_auth import router as kakao_auth_router, get_kakao_user_by_kakao_id
from env import DATABASE_URL
from models.student import Student
from models.course import Course
from models.user import User
from models.google_user import GoogleUser
from models.naver_user import NaverUser
from models.kakao_user import KakaoUser
from schemas.student import StudentCreateRequest, StudentResponse
from schemas.course import CourseCreateRequest, CourseResponse
from auth_utils import get_engine, get_serializer, cookie_load

app = FastAPI(
    title="Graduon",
    description="Graduon - 한국외국어대학교 컴퓨터공학부 졸업 요건 서비스",
    version="0.1.0",
)
engine = create_engine(DATABASE_URL, echo=True, pool_size=100, max_overflow=5, pool_timeout=30)
SQLModel.metadata.create_all(engine)

# Include routers
app.include_router(auth_router)
app.include_router(google_auth_router)
app.include_router(naver_auth_router)
app.include_router(kakao_auth_router)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/",
         summary="홈페이지",
         description="메인 로그인 페이지를 반환합니다.",
         response_class=FileResponse)
async def home():
    return FileResponse("static/frontend/index.html")

@app.get("/verify-email",
         summary="이메일 인증 페이지",
         description="이메일 인증 페이지를 반환합니다.",
         response_class=FileResponse)
async def verify_email():
    return FileResponse("static/frontend/verify_email.html")

@app.get("/forgot-password",
         summary="비밀번호 재설정 페이지",
         description="비밀번호 재설정 페이지를 반환합니다.",
         response_class=FileResponse)
async def forgot_password():
    return FileResponse("static/frontend/forgot_password.html")

@app.get("/signup",
         summary="이메일 회원가입 페이지",
         description="이메일 기반 회원가입 페이지를 반환합니다.",
         response_class=FileResponse)
async def signup():
    return FileResponse("static/frontend/email_signup.html")

@app.get("/fill-student-info",
         summary="학생 정보 입력 페이지",
         description="로그인한 사용자의 학생 정보(학번, 이름)를 입력하는 페이지를 반환합니다.",
         response_class=FileResponse)
async def fill_student_info():
    return FileResponse("static/frontend/fill_student_info.html")

@app.get("/dashboard",
         summary="메인 대시보드",
         description="졸업 진행률과 학점 관리 기능을 제공하는 대시보드 페이지를 반환합니다.",
         response_class=FileResponse)
async def dashboard():
    return FileResponse("static/frontend/dashboard.html")

@app.get("/grade-management",
         summary="학점 관리 메인 페이지",
         description="학점 관리 메인 페이지를 반환합니다.",
         response_class=FileResponse)
async def grade_management():
    return FileResponse("static/frontend/grade_management.html")

@app.get("/grade-input",
         summary="학점 입력 페이지",
         description="학점 입력 페이지를 반환합니다.",
         response_class=FileResponse)
async def grade_input():
    return FileResponse("static/frontend/credit_input.html")

@app.get("/graduation-calculator",
         summary="졸업 학점 계산기 페이지",
         description="졸업 학점 계산기 페이지를 반환합니다.",
         response_class=FileResponse)
async def graduation_calculator():
    return FileResponse("static/frontend/graduation_calculator.html")

@app.get("/credit-status",
         summary="학기별 학점 페이지",
         description="학기별 학점 페이지를 반환합니다.",
         response_class=FileResponse)
async def credit_status():
    return FileResponse("static/frontend/credit_status.html")

@app.get("/my",
         summary="마이페이지",
         description="마이페이지를 반환합니다.",
         response_class=FileResponse)
async def my():
    return FileResponse("static/frontend/my.html")

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
        serializer=Depends(get_serializer)
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


def get_student_from_auth(
        auth_info: tuple[str, Union[User, GoogleUser, NaverUser, KakaoUser]],
        session: Session
) -> Student:
    """인증된 사용자의 Student 레코드 조회"""
    auth_type, user = auth_info

    # Student 레코드 조회
    student_stmt = select(Student)
    if auth_type == "email":
        student_stmt = student_stmt.where(Student.user_email == user.email)
    elif auth_type == "google":
        student_stmt = student_stmt.where(Student.google_user_id == user.id)
    elif auth_type == "naver":
        student_stmt = student_stmt.where(Student.naver_user_id == user.id)
    elif auth_type == "kakao":
        student_stmt = student_stmt.where(Student.kakao_user_id == user.id)

    student = session.exec(student_stmt).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="학생 정보가 등록되지 않았습니다. 먼저 학생 정보를 등록해주세요."
        )

    return student


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
    # 이미 등록된 학생인지 확인 (get_student_from_auth에서 예외가 발생하지 않으면 이미 등록됨)
    try:
        get_student_from_auth(auth_info, session)
        # 학생 정보가 이미 있으면 예외 발생
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 학생 정보가 등록되어 있습니다."
        )
    except HTTPException as e:
        # 학생 정보가 없어서 발생한 예외는 무시 (정상적인 신규 등록)
        if e.status_code != status.HTTP_400_BAD_REQUEST or "학생 정보가 등록되지 않았습니다" not in e.detail:
            raise e

    auth_type, user = auth_info

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


@app.post("/courses",
          status_code=status.HTTP_201_CREATED,
          response_model=CourseResponse,
          summary="과목 정보 등록",
          description="현재 로그인된 학생의 과목 정보를 등록합니다.",
          responses={
              201: {"description": "과목 정보 등록 성공"},
              400: {"description": "잘못된 요청 (학생 미등록, 중복 과목, 재수강 조건 위반 등)"},
              401: {"description": "인증 실패 (로그인 필요)"},
          })
async def create_course(
        course_request: CourseCreateRequest,
        auth_info: tuple[str, Union[User, GoogleUser, NaverUser, KakaoUser]] = Depends(authenticate_user_from_cookies),
        session: Session = Depends(lambda: Session(engine))
) -> CourseResponse:
    """
    현재 로그인된 학생의 과목 정보를 등록합니다.
    
    ## 프론트엔드 지침
    - 로그인 상태에서만 호출 가능합니다
    - 학생 정보가 먼저 등록되어 있어야 합니다
    - 같은 과목은 초수강 1번, 재수강 1번까지 총 2번 수강 가능합니다
    - 재수강인 경우 반드시 초수강이 먼저 등록되어 있어야 합니다
    
    ## TODO
    - 과목 삭제 기능 구현 예정
    """

    # 1. Student 레코드 조회
    student = get_student_from_auth(auth_info, session)

    # 2. 재수강인 경우 초수강이 존재하는지 확인
    if course_request.is_retake:
        initial_course_stmt = select(Course).where(
            Course.student_id == student.id,
            Course.course_name == course_request.course_name,
            Course.is_retake == False
        )
        initial_course = session.exec(initial_course_stmt).first()
        if not initial_course:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"재수강 등록을 위해서는 '{course_request.course_name}' 과목의 초수강이 먼저 등록되어 있어야 합니다."
            )

    # 3. 중복 과목 확인 (같은 과목, 같은 재수강 여부)
    existing_course_stmt = select(Course).where(
        Course.student_id == student.id,
        Course.course_name == course_request.course_name,
        Course.is_retake == course_request.is_retake
    )
    existing_course = session.exec(existing_course_stmt).first()
    if existing_course:
        retake_status = "재수강" if course_request.is_retake else "초수강"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{course_request.course_name}' 과목의 {retake_status}은 이미 등록되어 있습니다."
        )

    # 4. Course 레코드 생성
    course = Course(
        student_id=student.id,
        semester=course_request.semester,
        course_name=course_request.course_name,
        credits=course_request.credits,
        grade=course_request.grade,
        is_major=course_request.is_major,
        is_retake=course_request.is_retake
    )

    session.add(course)
    session.commit()
    session.refresh(course)

    # 5. 응답 생성
    return CourseResponse(
        id=course.id,
        student_id=course.student_id,
        semester=course.semester,
        course_name=course.course_name,
        credits=course.credits,
        grade=course.grade,
        is_major=course.is_major,
        is_retake=course.is_retake,
        created_at=course.created_at.isoformat(),
        updated_at=course.updated_at.isoformat()
    )


@app.get("/course/all",
         status_code=status.HTTP_200_OK,
         response_model=List[CourseResponse],
         summary="모든 과목 조회",
         description="현재 로그인된 학생의 모든 과목 정보를 조회합니다.",
         responses={
             200: {"description": "과목 조회 성공"},
             400: {"description": "학생 미등록"},
             401: {"description": "인증 실패 (로그인 필요)"},
         }
         )
async def get_all_courses(
        auth_info: tuple[str, Union[User, GoogleUser, NaverUser, KakaoUser]] = Depends(authenticate_user_from_cookies),
        session: Session = Depends(lambda: Session(engine))
) -> List[CourseResponse]:
    # 1. Student 레코드 조회
    student = get_student_from_auth(auth_info, session)

    # 2. 해당 학기의 모든 과목 조회
    courses_stmt = select(Course).where(
        Course.student_id == student.id,
    ).order_by(Course.course_name, Course.is_retake)  # 과목명 순, 초수강 먼저

    courses = session.exec(courses_stmt).all()

    # 3. 응답 생성
    return [
        CourseResponse(
            id=course.id,
            student_id=course.student_id,
            semester=course.semester,
            course_name=course.course_name,
            credits=course.credits,
            grade=course.grade,
            is_major=course.is_major,
            is_retake=course.is_retake,
            created_at=course.created_at.isoformat(),
            updated_at=course.updated_at.isoformat()
        )
        for course in courses
    ]


@app.get("/courses/semester/{semester}",
         status_code=status.HTTP_200_OK,
         response_model=List[CourseResponse],
         summary="학기별 과목 조회",
         description="현재 로그인된 학생의 특정 학기 과목 정보를 조회합니다.",
         responses={
             200: {"description": "과목 조회 성공"},
             400: {"description": "학생 미등록"},
             401: {"description": "인증 실패 (로그인 필요)"},
         })
async def get_courses_by_semester(
        semester: str,
        auth_info: tuple[str, Union[User, GoogleUser, NaverUser, KakaoUser]] = Depends(authenticate_user_from_cookies),
        session: Session = Depends(lambda: Session(engine))
) -> List[CourseResponse]:
    """
    현재 로그인된 학생의 특정 학기 과목 정보를 조회합니다.
    
    ## 프론트엔드 지침
    - 로그인 상태에서만 호출 가능합니다
    - 학생 정보가 먼저 등록되어 있어야 합니다
    - semester 파라미터는 URL 경로에 포함 (예: /courses/semester/1-1)
    - 해당 학기에 등록된 모든 과목을 반환합니다 (초수강, 재수강 모두 포함)
    """

    # 1. Student 레코드 조회
    student = get_student_from_auth(auth_info, session)

    # 2. 해당 학기의 모든 과목 조회
    courses_stmt = select(Course).where(
        Course.student_id == student.id,
        Course.semester == semester
    ).order_by(Course.course_name, Course.is_retake)  # 과목명 순, 초수강 먼저

    courses = session.exec(courses_stmt).all()

    # 3. 응답 생성
    return [
        CourseResponse(
            id=course.id,
            student_id=course.student_id,
            semester=course.semester,
            course_name=course.course_name,
            credits=course.credits,
            grade=course.grade,
            is_major=course.is_major,
            is_retake=course.is_retake,
            created_at=course.created_at.isoformat(),
            updated_at=course.updated_at.isoformat()
        )
        for course in courses
    ]


@app.get("/student/status",
         status_code=status.HTTP_200_OK,
         summary="학생 정보 등록 상태 확인",
         description="현재 로그인된 사용자에게 Student 테이블에 연관된 정보가 있는지 확인합니다.",
         responses={
             200: {"description": "학생 정보 상태 확인 성공"},
             401: {"description": "인증 실패 (로그인 필요)"},
         })
async def get_student_status(
        auth_info: tuple[str, Union[User, GoogleUser, NaverUser, KakaoUser]] = Depends(authenticate_user_from_cookies),
        session: Session = Depends(lambda: Session(engine))
):
    """
    현재 로그인된 사용자의 학생 정보 등록 상태를 확인합니다.
    
    ## 프론트엔드 지침
    - 로그인 상태에서만 호출 가능합니다
    - 학생 정보가 등록되어 있으면 Student 정보를 반환합니다
    - 학생 정보가 등록되지 않았으면 has_student_info: false를 반환합니다
    - 이 API로 학생 정보 등록 페이지로 리다이렉션할지 결정할 수 있습니다
    """
    try:
        # 학생 정보 조회 시도
        student = get_student_from_auth(auth_info, session)
        auth_type, user = auth_info
        
        # OAuth 사용자 정보 추가 (프로필 이미지용)
        auth_user_info = {}
        if auth_type == "email":
            auth_user_info = {"email": user.email}
        elif auth_type == "google":
            auth_user_info = {"email": user.email, "name": user.name, "picture": user.picture}
        elif auth_type == "naver":
            auth_user_info = {"email": user.email, "name": user.name, "picture": user.picture}
        elif auth_type == "kakao":
            auth_user_info = {"nickname": user.nickname, "picture": user.picture}
        
        # 학생 정보가 있는 경우
        return {
            "has_student_info": True,
            "auth_type": auth_type,
            "auth_user_info": auth_user_info,
            "student": {
                "id": student.id,
                "student_id": student.student_id,
                "name": student.name,
                "user_email": student.user_email,
                "google_user_id": student.google_user_id,
                "naver_user_id": student.naver_user_id,
                "kakao_user_id": student.kakao_user_id,
                "created_at": student.created_at.isoformat(),
                "updated_at": student.updated_at.isoformat()
            }
        }
    except HTTPException as e:
        # 학생 정보가 없는 경우 (get_student_from_auth에서 400 에러)
        if e.status_code == status.HTTP_400_BAD_REQUEST and "학생 정보가 등록되지 않았습니다" in e.detail:
            auth_type, user = auth_info
            user_info = {}
            
            if auth_type == "email":
                user_info = {"email": user.email}
            elif auth_type == "google":
                user_info = {"email": user.email, "name": user.name, "picture": user.picture}
            elif auth_type == "naver":
                user_info = {"email": user.email, "name": user.name, "picture": user.picture}
            elif auth_type == "kakao":
                user_info = {"nickname": user.nickname, "picture": user.picture}
            
            return {
                "has_student_info": False,
                "auth_type": auth_type,
                "user_info": user_info
            }
        else:
            # 다른 예외는 그대로 전파
            raise e


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
