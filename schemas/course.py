from pydantic import BaseModel, Field


class CourseCreateRequest(BaseModel):
    semester: str = Field(..., description="수강 학기 (예: '1학년 1학기')", min_length=1, max_length=50)
    course_name: str = Field(..., description="과목명", min_length=1, max_length=100)
    credits: int = Field(..., description="학점 수", ge=1, le=10)
    grade: float = Field(..., description="등급 (0.0~4.5)", ge=0.0, le=4.5)
    is_major: bool = Field(default=False, description="전공 과목 여부")
    is_retake: bool = Field(default=False, description="재수강 여부")


class CourseResponse(BaseModel):
    id: int
    student_id: int
    semester: str
    course_name: str
    credits: int
    grade: float
    is_major: bool
    is_retake: bool
    created_at: str
    updated_at: str