# routers/grades.py
from fastapi import APIRouter, HTTPException, status
from typing import List
from models import Course, CourseEntry, SubmitResponse, GradeValue # 모델 임포트
from course_database import student_courses_db # 데이터베이스 임포트

router = APIRouter()

@router.post("/submit_data/", response_model=SubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_data(course_entry: CourseEntry):
    """학생의 과목 및 성적 정보를 받아 저장하거나 업데이트합니다."""
    student_id = course_entry.student_id
    student_grade_year = course_entry.student_grade_year.value

    if student_id not in student_courses_db:
        student_courses_db[student_id] = {
            "grade_year": student_grade_year,
            "courses": []
        }
    else:
        student_courses_db[student_id]["grade_year"] = student_grade_year

    for new_course in course_entry.courses:
        found = False
        for existing_course in student_courses_db[student_id]["courses"]:
            if existing_course.course_name == new_course.course_name:
                existing_course.credits = new_course.credits
                existing_course.grade = new_course.grade
                found = True
                break
        if not found:
            student_courses_db[student_id]["courses"].append(new_course)

    print(f"Current DB for {student_id}: {student_courses_db[student_id]}")
    return {"student_id": student_id, "message": "과목 및 성적 정보가 성공적으로 저장되었습니다."}

@router.get("/get_grades/{student_id}", response_model=List[Course])
async def get_grades(student_id: str):
    """특정 학생이 수강한 모든 과목 목록을 반환합니다."""
    if student_id not in student_courses_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 학번의 학생 정보를 찾을 수 없습니다."
        )
    return student_courses_db[student_id]["courses"]