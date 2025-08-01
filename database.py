from sqlmodel import SQLModel, create_engine
from models.user import User  # 모델이 정의된 파일로부터 import
from models.google_user import GoogleUser  # Google OAuth2 사용자 모델 import
from models.naver_user import NaverUser  # Naver OAuth2 사용자 모델 import
from models.kakao_user import KakaoUser  # Kakao OAuth2 사용자 모델 import
from models.student import Student
from models.course import Course
# SQLite 경로: 로컬 파일 (필요시 :memory: 사용 가능)
from env import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)  # echo=True는 SQL 쿼리 로그 출력

def init_db():
    SQLModel.metadata.create_all(engine)
    print("===== 데이터베이스 및 테이블이 생성되었습니다. =====")

if __name__ == "__main__":
    init_db()
