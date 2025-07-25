# culture.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import grades, course_options # 라우터 임포트

app = FastAPI(
    title="졸업 학점 계산기",
    description="교양 과목 선택 및 계산",
)

# CORS 설정
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000", #프엔 주소 추가해야할 필요있습니다(?)
    "http://127.0.0.1:5500", # VS Code Live Server 기본 포트
    "http://localhost:3000", # React 기본 포트
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함 (API 엔드포인트들을 애플리케이션에 연결)
app.include_router(grades.router, prefix="/api/grades", tags=["성적 관리"])
app.include_router(course_options.router, prefix="/api/options", tags=["과목/학년 옵션"])
