# routers/grades.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Tuple
from sqlmodel import Session, select
from datetime import datetime, timezone

from schemas.culture import Course, CourseEntry, SubmitResponse
from models.culture_data import CultureData, CultureCourse
from models.culture import GradeValue
from culture.auth_helper import get_current_user_info
from auth_utils import get_engine

router = APIRouter()

@router.post("/submit_data/", response_model=SubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_data(
    course_entry: CourseEntry, 
    user_info: Tuple[str, str] = Depends(get_current_user_info),
    engine = Depends(get_engine)
):
    """학생의 과목 및 성적 정보를 받아 저장하거나 업데이트합니다. (로그인 필요)"""
    user_type, user_identifier = user_info
    student_id = course_entry.student_id
    student_grade_year = course_entry.student_grade_year.value

    with Session(engine) as session:
        # 기존 데이터 찾기
        statement = select(CultureData).where(
            CultureData.user_type == user_type,
            CultureData.user_identifier == user_identifier,
            CultureData.student_id == student_id
        )
        existing_data = session.exec(statement).first()
        
        if existing_data:
            # 기존 데이터 업데이트
            existing_data.grade_year = student_grade_year
            existing_data.updated_at = datetime.now(timezone.utc)
            
            # 기존 과목들 삭제
            course_statement = select(CultureCourse).where(
                CultureCourse.culture_data_id == existing_data.id
            )
            existing_courses = session.exec(course_statement).all()
            for course in existing_courses:
                session.delete(course)
        else:
            # 새 데이터 생성
            existing_data = CultureData(
                user_type=user_type,
                user_identifier=user_identifier,
                student_id=student_id,
                grade_year=student_grade_year
            )
            session.add(existing_data)
            session.flush()  # ID 생성을 위해
        
        # 새 과목들 추가
        for course in course_entry.courses:
            new_course = CultureCourse(
                culture_data_id=existing_data.id,
                course_name=course.course_name,
                credits=course.credits,
                grade=course.grade.value
            )
            session.add(new_course)
        
        session.commit()
        
    return {"student_id": student_id, "message": "과목 및 성적 정보가 성공적으로 저장되었습니다."}

@router.get("/get_grades/{student_id}", response_model=List[Course])
async def get_grades(
    student_id: str, 
    user_info: Tuple[str, str] = Depends(get_current_user_info),
    engine = Depends(get_engine)
):
    """특정 학생이 수강한 모든 과목 목록을 반환합니다. (로그인 필요)"""
    user_type, user_identifier = user_info
    
    with Session(engine) as session:
        # 사용자의 해당 학번 데이터 찾기
        statement = select(CultureData).where(
            CultureData.user_type == user_type,
            CultureData.user_identifier == user_identifier,
            CultureData.student_id == student_id
        )
        culture_data = session.exec(statement).first()
        
        if not culture_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 학번의 학생 정보를 찾을 수 없습니다."
            )
        
        # 과목 목록 조회
        course_statement = select(CultureCourse).where(
            CultureCourse.culture_data_id == culture_data.id
        )
        courses = session.exec(course_statement).all()
        
        # Course 스키마 형태로 변환
        result = []
        for course in courses:
            result.append(Course(
                course_name=course.course_name,
                credits=course.credits,
                grade=GradeValue(course.grade)
            ))
        
        return result