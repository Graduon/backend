# schemas/culture.py
from pydantic import BaseModel, Field
from typing import List
from models.culture import GradeValue, YearEnum

# 과목 정보 스키마
class Course(BaseModel):
    course_name: str = Field(..., example="대학영어2")
    credits: float = Field(..., ge=0.5, le=5.0, example=3.0)
    grade: GradeValue = Field(..., example=GradeValue.A)

# 과목 입력 엔트리 스키마
class CourseEntry(BaseModel):
    student_id: str = Field(..., example="20251234")
    student_grade_year: YearEnum = Field(..., example=YearEnum.FRESHMAN.value)
    courses: List[Course]

# 응답 스키마
class SubmitResponse(BaseModel):
    student_id: str
    message: str