# backend

## TODO

- [X] email 기반 로그인 및 문서화
- [ ] Oauth2 인증 및 문서화
  - [ ] Google
  - [ ] Kakao
  - [ ] Apple 

## 개발 준비

[github 협업 관련 참고 링크](https://github.com/Qfourteen/Gamers/blob/main/docs/how_to/%EA%B8%B0%EC%97%AC_%EC%83%81%EC%84%B8.md)

```shell
pip install -r requirements.txt
```

* `fastapi`: Python으로 HTTP 요청을 분석하고 응답을 생성할 수 있게 만들어 줌.
* `uvicorn`: `FastAPI`가 실제 HTTP 요청을 받고 반환할 수 있도록 하는 역할.

### 실행 방법

```bash
uvicorn main:app
```

1. 웹 브라우저에서 `http://localhost:8000` 접속
2. API 문서 자동 생성:
   * Swagger UI: `http://localhost:8000/docs`
     * Swagger 적극적으로 이용하는 걸 권장.
   * Redoc: `http://localhost:8000/redoc`

> 코드를 변경할 시 `ctrl c` 눌러서 `uvicorn` 종료 후, 다시 위 명령어로 실행하면 됨.

### 기본 예제

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
```

### 경로 변수

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

* `/items/42` 요청 시: `{"item_id": 42}` 반환

### 쿼리 파라미터

```python
@app.get("/search/")
def search(q: str = ""):
    return {"query": q}
```

* `/search/?q=fastapi` → `{"query": "fastapi"}`

### 복잡한 요청 처리

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@app.post("/items/")
def create_item(item: Annotated[Item, Body()]):
    return {"name": item.name, "price": item.price}
```

* 요청 예시 (POST `/items/`):

```json
{
  "name": "Book",
  "price": 12.99
}
```

### 오류 반환

```python
from fastapi import HTTPException

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id != 1:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id}
```


## 인증 프로세스

### 회원가입 - 로그인 

| 단계  | 내용                        | API                            |
|-----|---------------------------|--------------------------------|
| 1단계 | 회원가입 폼 작성 후 회원가입 요청       | `/signup`                      |
| 2단계 | 정규 회원으로 전환을 위한 이메일 인증을 신청 | `/signup/verify-email/request` |
| 3단계 | 이메일로 온 코드를 보고 인증 코드를 입력   | `/signup/verify-email/confirm` |
| 4단계 | 로그인 화면으로 돌아가서 로그인(쿠키 발급)  | `/login`                       | 

### 이메일 송신

Gmail을 이용하기 때문에 자동화된 요청을 너무 남발하면 저희 계정에 영향이 갈 가능성이 있습니다.
그러므로 데이터베이스에서 이메일 주소당 송신 횟수를 기록하여 남발을 막고자 합니다.

최대 횟수에 도달하면 정해진 시간 동안 해당 이메일 주소로 보내지 않도록 코드를 작성했습니다.
최대 횟수 증감은 이메일 인증과 비밀번호 재설정이 공유합니다.
최대 횟수와 송신 정지 시간은 유동적으로 조절할 수 있습니다.

* 이메일 인증 코드 보낼 때마다 -> 1회 증가
* 비밀번호 재설정 코드 보낼 때마다 -> 1회 증가
* 이메일 인증을 완료하면 -> 해당 계정의 최대 한도 초기화
* 비밀번호 재설정을 완료하면 -> 해당 계정의 최대 한도 초기화
