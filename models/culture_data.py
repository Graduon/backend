# models/culture_data.py
from sqlmodel import SQLModel, Field, JSON, Column
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from models.culture import YearEnum


def utc_now_factory(tz=timezone.utc):
    return datetime.now(tz)


class CultureData(SQLModel, table=True):
    """모든 사용자 유형의 교양과목 성적 데이터를 저장하는 통합 테이블"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 사용자 식별 정보
    user_type: str = Field(nullable=False, index=True)  # 'email', 'google', 'kakao', 'naver'
    user_identifier: str = Field(nullable=False, index=True)  # email, google_id, kakao_id, naver_id
    
    # 학생 정보
    student_id: str = Field(nullable=False)  # 학번
    grade_year: int = Field(nullable=False)  # 학년 (1,2,3,4)
    
    # 과목 데이터 (JSON으로 저장)
    courses_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # 타임스탬프
    created_at: datetime = Field(default_factory=utc_now_factory)
    updated_at: datetime = Field(default_factory=utc_now_factory)
    
    class Config:
        # user_type + user_identifier + student_id 조합이 유니크해야 함
        # (한 사용자가 여러 학번을 가질 수 있다고 가정)
        table_args = (
            {"sqlite_autoincrement": True},
        )


class CultureCourse(SQLModel, table=True):
    """개별 과목 정보를 저장하는 테이블 (정규화된 방식)"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # CultureData와의 관계
    culture_data_id: int = Field(foreign_key="culturedata.id", nullable=False)
    
    # 과목 정보
    course_name: str = Field(nullable=False)
    credits: float = Field(nullable=False)
    grade: str = Field(nullable=False)  # GradeValue enum의 값
    
    # 타임스탬프
    created_at: datetime = Field(default_factory=utc_now_factory)
    updated_at: datetime = Field(default_factory=utc_now_factory)