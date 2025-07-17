from fastapi import FastAPI, Response, status

app = FastAPI()

@app.get("/ping", status_code=204)
async def does_server_alive(response: Response) -> Response:
    """
    서버, 데이터베이스가 살아있는지 확인하는 API입니다.
    """
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
