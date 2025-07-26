# routers/course_options.py
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Union
from models.culture import GradeValue, YearEnum
from models.course_database import COURSES_BY_YEAR

router = APIRouter()

@router.get("/get_grade_options/", response_model=List[str])
async def get_grade_options():
    """유효한 모든 성적 등급 옵션 목록을 반환"""
    return [grade.value for grade in GradeValue]

@router.get("/get_years_options/", response_model=List[Dict[str, int]])
async def get_years_options():
    """유효한 모든 학년 옵션 목록을 반환"""
    return [{"year": year_enum.value} for year_enum in YearEnum]

@router.get("/get_courses_by_year/{year_value}", response_model=List[Dict[str, Union[str, float]]])
async def get_courses_by_year(year_value: int):
    """특정 학년에 해당하는 수강 가능한 과목 목록을 반환"""
    try:
        selected_year_enum = YearEnum(year_value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 학년 값입니다: {year_value}. 유효한 학년은 {', '.join([str(y.value) for y in YearEnum])} 입니다."
        )

    courses = COURSES_BY_YEAR.get(selected_year_enum)
    if not courses:
        return []
    return courses