# course_database.py
from typing import Dict, List, Union 
from models import Course, YearEnum 

# 임시 데이터 저장소
student_courses_db: Dict[str, Dict[str, Union[int, List[Course]]]] = {}

# 학년별 수강 가능한 교양 과목 목록
COURSES_BY_YEAR: Dict[YearEnum, List[Dict]] = {
    YearEnum.FRESHMAN: [
        {"course_name": "대학독일어2", "credits": 3.0},
        {"course_name": "대학러시아어2", "credits": 3.0},
        {"course_name": "대학말레이.인도네이사어2", "credits": 3.0},
        {"course_name": "대학베트남어2", "credits": 3.0},
        {"course_name": "대학스와힐리어2", "credits": 3.0},
        {"course_name": "대학스페인어2", "credits": 3.0},
        {"course_name": "대학아랍어2", "credits": 3.0},
        {"course_name": "대학이탈리아어2", "credits": 3.0},
        {"course_name": "대학일본어2", "credits": 3.0},
        {"course_name": "대학중국어2", "credits": 3.0},
        {"course_name": "대학포르투갈어2", "credits": 3.0},
        {"course_name": "대학프랑스어2", "credits": 3.0},
        {"course_name": "대학영어2", "credits": 3.0},
        {"course_name": "미네르바인문(1)읽기와 쓰기", "credits": 3.0},
        {"course_name": "미네르바인문(2)읽기와토의.토론", "credits": 3.0},
        {"course_name": "Media English (RC)", "credits": 2.0},
        {"course_name": "TOEIC Speaking (RC)", "credits": 2.0},
        {"course_name": "English for Engineering (RC)", "credits": 2.0},
        {"course_name": "신입생세미나", "credits": 1.0},
        {"course_name": "문맥으로읽는공학기술용어", "credits": 3.0},
        {"course_name": "AI공학개론", "credits": 3.0},
        {"course_name": "공업수학1", "credits": 3.0},
    ],
    YearEnum.SOPHOMORE: [
        {"course_name": "창의적 사고와 글쓰기", "credits": 3.0},
        {"course_name": "대학영어 2", "credits": 2.0},
        {"course_name": "데이터와 사회", "credits": 3.0},
        {"course_name": "철학의 이해", "credits": 2.0},
    ],
    YearEnum.JUNIOR: [
        {"course_name": "세계 문화와 예술", "credits": 3.0},
        {"course_name": "인간과 환경", "credits": 3.0},
        {"course_name": "기술과 사회", "credits": 2.0},
    ],
    YearEnum.SENIOR: [
        {"course_name": "시사 영어 토론", "credits": 2.0},
        {"course_name": "미래 사회와 윤리", "credits": 3.0},
        {"course_name": "취업과 진로", "credits": 1.0},
    ],
}