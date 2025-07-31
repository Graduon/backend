from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import UniqueConstraint


def utc_now_factory(tz=timezone.utc):
    return datetime.now(tz)


class Course(SQLModel, table=True):
    __table_args__ = (
        # (학생, 과목명, 재수강여부) 조합이 unique
        # 이를 통해 초수강 1번, 재수강 1번까지 총 2번 수강 가능
        UniqueConstraint('student_id', 'course_name', 'is_retake', name='uq_student_course_retake'),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", nullable=False)  # Student와 1:다 관계
    
    course_name: str = Field(nullable=False)  # 과목 이름
    semester: str = Field(nullable=False)  # 수강 학기 (예: "1학년 1학기")
    credits: int = Field(nullable=False)  # 학점 수
    grade: float = Field(nullable=False)  # 등급 (4.5, 4.0 등)
    is_major: bool = Field(default=False)  # 전공 과목 여부
    is_retake: bool = Field(default=False)  # 재수강 여부
    
    created_at: datetime = Field(default_factory=utc_now_factory)
    updated_at: datetime = Field(default_factory=utc_now_factory)