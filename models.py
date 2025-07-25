# models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

# 학년 정의
class YearEnum(Enum):
    FRESHMAN = 1
    SOPHOMORE = 2
    JUNIOR = 3
    SENIOR = 4

# 성적 등급 정의
class GradeValue(Enum):
    APLUS = "A+"
    A = "A0"
    BPLUS = "B+"
    B = "B0"
    CPLUS = "C+"
    C = "C0"
    DPLUS = "D+"
    D = "D0"
    F = "F"
    P = "P"
    NP = "NP"

    def get_points(self) -> float:
        grade_map = {
            self.APLUS: 4.5, self.A: 4.0,
            self.BPLUS: 3.5, self.B: 3.0,
            self.CPLUS: 2.5, self.C: 2.0,
            self.DPLUS: 1.5, self.D: 1.0,
            self.F: 0.0,
            self.P: 0.0,
            self.NP: 0.0
        }
        return grade_map.get(self, 0.0)

# 과목 정보 모델
class Course(BaseModel):
    course_name: str = Field(..., example="대학영어2")
    credits: float = Field(..., ge=0.5, le=5.0, example=3.0)
    grade: GradeValue = Field(..., example=GradeValue.A)

# 과목 입력 엔트리 모델
class CourseEntry(BaseModel):
    student_id: str = Field(..., example="20251234")
    student_grade_year: YearEnum = Field(..., example=YearEnum.FRESHMAN.value)
    courses: List[Course]

# 응답 모델
class SubmitResponse(BaseModel):
    student_id: str
    message: str