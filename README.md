# backend

## 개발 준비

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
def create_item(item: Item):
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
