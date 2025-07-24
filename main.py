# 외부 라이브러리
from fastapi import FastAPI, Response, status
from sqlmodel import create_engine, SQLModel
# 직접 작성한 모듈
from auth import router as auth_router
from google_auth import router as google_auth_router
from naver_auth import router as naver_auth_router
from env import DATABASE_URL

app = FastAPI(
    title="Graduon",
    description="Graduon - 한국외국어대학교 컴퓨터공학부 졸업 요건 서비스",
    version="0.1.0",
)
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)

# Include routers
app.include_router(auth_router)
app.include_router(google_auth_router)
app.include_router(naver_auth_router)



@app.get("/ping",
         status_code=status.HTTP_204_NO_CONTENT,
         summary="서버 기동 확인",
         response_description="서버와 데이터베이스가 정상 작동함을 응답 (204 No Content)",
         responses={
             204: {"description": "서버와 데이터베이스 모두 살아있음"},
             500: {"description": "서버 혹은 데이터베이스가 죽었음"},
         }
         )
async def does_server_alive(response: Response) -> Response:
    """
    서버, 데이터베이스가 살아있는지 확인하는 API입니다.

    ## 프론트엔드 지침
    서버가 살아있는지 확인할 때 사용할 수 있는 다재다능한 API입니다.
    """
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


