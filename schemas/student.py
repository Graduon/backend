from pydantic import BaseModel, Field


class StudentCreateRequest(BaseModel):
    student_id: str = Field(..., description="학번", min_length=1, max_length=20)
    name: str = Field(..., description="이름", min_length=1, max_length=50)


class StudentResponse(BaseModel):
    id: int
    student_id: str
    name: str
    user_email: str | None = None
    google_user_id: int | None = None
    naver_user_id: int | None = None 
    kakao_user_id: int | None = None
    created_at: str
    updated_at: str