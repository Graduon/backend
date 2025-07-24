# backend

## 목차

- [TODO](#todo)
- [개발 준비](#개발-준비)
  - [실행 방법](#실행-방법)
  - [기본 예제](#기본-예제)
  - [경로 변수](#경로-변수)
  - [쿼리 파라미터](#쿼리-파라미터)
  - [복잡한 요청 처리](#복잡한-요청-처리)
  - [오류 반환](#오류-반환)
- [인증 프로세스](#인증-프로세스)
  - [이메일 기반 회원가입 - 로그인](#이메일-기반-회원가입---로그인)
  - [Google OAuth2 로그인](#google-oauth2-로그인)
  - [네이버 OAuth2 로그인](#네이버-oauth2-로그인)
  - [카카오 OAuth2 로그인](#카카오-oauth2-로그인)
  - [이메일 송신](#이메일-송신)
- [HTTPS 개발 환경 설정](#https-개발-환경-설정)
  - [자동 설정 (권장)](#자동-설정-권장)
  - [수동 설정](#수동-설정)
  - [브라우저 SSL 경고 해결](#브라우저-ssl-경고-해결)
  - [파일 구조](#파일-구조)
- [쿠키 인증 시스템](#쿠키-인증-시스템)
  - [쿠키 종류](#쿠키-종류)
  - [쿠키 속성](#쿠키-속성)
  - [쿠키 서명 시스템](#쿠키-서명-시스템)
  - [프론트엔드 쿠키 확인](#프론트엔드-쿠키-확인)

## TODO

- [X] email 기반 로그인 및 문서화
- [X] Oauth2 인증 및 문서화
  - [X] Google
  - [X] Kakao
  - [X] Naver 

## 개발 준비

[github 협업 관련 참고 링크](https://github.com/Qfourteen/Gamers/blob/main/docs/how_to/%EA%B8%B0%EC%97%AC_%EC%83%81%EC%84%B8.md)

```shell
pip install -r requirements.txt
```

* `fastapi`: Python으로 HTTP 요청을 분석하고 응답을 생성할 수 있게 만들어 줌.
* `uvicorn`: `FastAPI`가 실제 HTTP 요청을 받고 반환할 수 있도록 하는 역할.

### 실행 방법

#### 개발용 HTTP 서버 (기본)
```bash
uvicorn main:app
```

#### 개발용 HTTPS 서버 (Google OAuth2용)
```bash
./run_dev_https.sh
```

**HTTPS 서버 접속:**
1. 웹 브라우저에서 `https://localhost:8000` 접속
2. API 문서:
   * Swagger UI: `https://localhost:8000/docs`
   * Redoc: `https://localhost:8000/redoc`
3. 소셜 로그인:
   * Google: `https://localhost:8000/auth/google/login`
   * 네이버: `https://localhost:8000/auth/naver/login`
   * 카카오: `https://localhost:8000/auth/kakao/login`

> ⚠️ HTTPS 서버 첫 실행시 브라우저에서 "안전하지 않음" 경고가 나타납니다.  
> "고급" → "계속 진행"을 클릭하여 접속하세요. (자체서명 인증서이므로 정상입니다)

> 코드를 변경할 시 `ctrl c` 눌러서 서버 종료 후, 다시 실행하면 됩니다.

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

### 이메일 기반 회원가입 - 로그인 

| 단계  | 내용                        | API                            |
|-----|---------------------------|--------------------------------|
| 1단계 | 회원가입 폼 작성 후 회원가입 요청       | `/signup`                      |
| 2단계 | 정규 회원으로 전환을 위한 이메일 인증을 신청 | `/signup/verify-email/request` |
| 3단계 | 이메일로 온 코드를 보고 인증 코드를 입력   | `/signup/verify-email/confirm` |
| 4단계 | 로그인 화면으로 돌아가서 로그인(쿠키 발급)  | `/login`                       |

### Google OAuth2 로그인

Google 로그인은 별도의 회원가입 없이 **자동으로 계정이 생성**됩니다.

| 단계  | 내용                   | API                             |
|-----|----------------------|---------------------------------|
| 1단계 | Google 로그인 페이지로 이동   | `/auth/google/login`            |
| 2단계 | Google에서 로그인 완료 후 콜백 | `/auth/google/callback` (자동 호출) |
| 3단계 | 자동 회원가입/로그인 및 쿠키 발급  | 완료                              |

#### Google OAuth2 설정 (개발자용)

**1. Google Cloud Console 설정:**
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "APIs & Services" → "Credentials" 이동
4. "Create Credentials" → "OAuth 2.0 Client IDs" 선택
5. Application type: "Web application"
6. Authorized redirect URIs에 추가:
   ```
   https://localhost:8000/auth/google/callback
   ```
7. Client ID와 Client Secret을 `env.py`에 설정

**2. 환경 변수 설정:**
```python
# env.py
GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
GOOGLE_REDIRECT_URI = "https://localhost:8000/auth/google/callback"
```

#### 프론트엔드 구현 예시

**JavaScript로 Google 로그인 버튼:**
```javascript
// Google 로그인 시작
function startGoogleLogin() {
    window.location.href = "https://localhost:8000/auth/google/login";
}

// 또는 새 창에서 열기
function openGoogleLogin() {
    const popup = window.open(
        "https://localhost:8000/auth/google/login",
        "google-login",
        "width=500,height=600"
    );
    
    // 팝업이 닫히면 페이지 새로고침 (쿠키 확인용)
    const checkClosed = setInterval(() => {
        if (popup.closed) {
            clearInterval(checkClosed);
            location.reload(); // 로그인 상태 확인
        }
    }, 1000);
}
```

**React 예시:**
```jsx
function GoogleLoginButton() {
    const handleGoogleLogin = () => {
        window.location.href = "https://localhost:8000/auth/google/login";
    };

    return (
        <button onClick={handleGoogleLogin}>
            Google로 로그인
        </button>
    );
}
``` 

### 네이버 OAuth2 로그인

네이버 로그인은 별도의 회원가입 없이 **자동으로 계정이 생성**됩니다.

| 단계  | 내용                   | API                             |
|-----|----------------------|---------------------------------|
| 1단계 | 네이버 로그인 페이지로 이동   | `/auth/naver/login`             |
| 2단계 | 네이버에서 로그인 완료 후 콜백 | `/auth/naver/callback` (자동 호출) |
| 3단계 | 자동 회원가입/로그인 및 쿠키 발급 | 완료                              |

#### 네이버 OAuth2 설정 (개발자용)

**1. 네이버 개발자센터 설정:**
1. [네이버 개발자센터](https://developers.naver.com/) 접속
2. "Application" → "애플리케이션 등록" 선택
3. 애플리케이션 정보 입력:
   - 애플리케이션 이름: 원하는 이름
   - 사용 API: 네이버 로그인
4. 서비스 URL 설정:
   ```
   https://localhost:8000
   ```
5. Callback URL 설정:
   ```
   https://localhost:8000/auth/naver/callback
   ```
6. Client ID와 Client Secret을 `env.py`에 설정

**2. 환경 변수 설정:**
```python
# env.py
NAVER_CLIENT_ID = "your-naver-client-id"
NAVER_CLIENT_SECRET = "your-naver-client-secret"
NAVER_REDIRECT_URI = "https://localhost:8000/auth/naver/callback"
```

#### 프론트엔드 구현 예시

**JavaScript로 네이버 로그인 버튼:**
```javascript
// 네이버 로그인 시작
function startNaverLogin() {
    window.location.href = "https://localhost:8000/auth/naver/login";
}

// 또는 새 창에서 열기
function openNaverLogin() {
    const popup = window.open(
        "https://localhost:8000/auth/naver/login",
        "naver-login",
        "width=500,height=600"
    );
    
    // 팝업이 닫히면 페이지 새로고침 (쿠키 확인용)
    const checkClosed = setInterval(() => {
        if (popup.closed) {
            clearInterval(checkClosed);
            location.reload(); // 로그인 상태 확인
        }
    }, 1000);
}
```

**React 예시:**
```jsx
function NaverLoginButton() {
    const handleNaverLogin = () => {
        window.location.href = "https://localhost:8000/auth/naver/login";
    };

    return (
        <button onClick={handleNaverLogin}>
            네이버로 로그인
        </button>
    );
}
```

### 카카오 OAuth2 로그인

카카오 로그인은 별도의 회원가입 없이 **자동으로 계정이 생성**됩니다.

| 단계  | 내용                   | API                             |
|-----|----------------------|---------------------------------|
| 1단계 | 카카오 로그인 페이지로 이동   | `/auth/kakao/login`             |
| 2단계 | 카카오에서 로그인 완료 후 콜백 | `/auth/kakao/callback` (자동 호출) |
| 3단계 | 자동 회원가입/로그인 및 쿠키 발급 | 완료                              |

#### 카카오 OAuth2 설정 (개발자용)

**1. 카카오 개발자센터 설정:**
1. [카카오 개발자센터](https://developers.kakao.com/) 접속
2. "내 애플리케이션" → "애플리케이션 추가하기" 선택
3. 애플리케이션 정보 입력 후 생성
4. "앱 설정" → "플랫폼" → "Web 플랫폼 등록":
   ```
   https://localhost:8000
   ```
5. "제품 설정" → "카카오 로그인" → "Redirect URI 등록":
   ```
   https://localhost:8000/auth/kakao/callback
   ```
6. "보안" → "Client Secret" 생성 (선택사항)
7. REST API 키와 Client Secret을 `env.py`에 설정

**2. 환경 변수 설정:**
```python
# env.py
KAKAO_CLIENT_ID = "your-kakao-rest-api-key"
KAKAO_CLIENT_SECRET = "your-kakao-client-secret"  # 선택사항
KAKAO_REDIRECT_URI = "https://localhost:8000/auth/kakao/callback"
```

#### 프론트엔드 구현 예시

**JavaScript로 카카오 로그인 버튼:**
```javascript
// 카카오 로그인 시작
function startKakaoLogin() {
    window.location.href = "https://localhost:8000/auth/kakao/login";
}

// 또는 새 창에서 열기
function openKakaoLogin() {
    const popup = window.open(
        "https://localhost:8000/auth/kakao/login",
        "kakao-login",
        "width=500,height=600"
    );
    
    // 팝업이 닫히면 페이지 새로고침 (쿠키 확인용)
    const checkClosed = setInterval(() => {
        if (popup.closed) {
            clearInterval(checkClosed);
            location.reload(); // 로그인 상태 확인
        }
    }, 1000);
}
```

**React 예시:**
```jsx
function KakaoLoginButton() {
    const handleKakaoLogin = () => {
        window.location.href = "https://localhost:8000/auth/kakao/login";
    };

    return (
        <button onClick={handleKakaoLogin}>
            카카오로 로그인
        </button>
    );
}
```

**특이사항:**
- 카카오는 **이메일 정보를 제공하지 않습니다.**

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

## HTTPS 개발 환경 설정

Google OAuth2는 보안상 **HTTPS 환경에서만 작동**합니다. 개발 과정에서 HTTPS를 사용하기 위해 자체서명 SSL 인증서를 사용합니다.

### 자동 설정 (권장)

```bash
# HTTPS 개발 서버 실행 (SSL 인증서 자동 생성)
./run_dev_https.sh
```

이 스크립트는 다음 작업을 자동으로 수행합니다:
1. SSL 인증서가 없으면 자동 생성
2. HTTPS로 uvicorn 서버 실행
3. 개발에 필요한 모든 URL 정보 표시

### 수동 설정

**1. SSL 인증서 생성:**
```bash
# SSL 인증서 생성 스크립트 실행
./generate_ssl_cert.sh
```

또는 직접 OpenSSL 명령어로:
```bash
# ssl 디렉토리 생성
mkdir -p ssl

# 개인키 및 자체서명 인증서 생성
openssl genrsa -out ssl/server.key 2048
openssl req -new -x509 -key ssl/server.key -out ssl/server.crt -days 365 \
    -subj "/C=KR/ST=Seoul/L=Seoul/O=Development/CN=localhost"
```

**2. HTTPS 서버 실행:**
```bash
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile ssl/server.key \
    --ssl-certfile ssl/server.crt \
    --reload
```

### 브라우저 SSL 경고 해결

자체서명 인증서를 사용하므로 브라우저에서 "안전하지 않음" 경고가 표시됩니다:

1. **Chrome/Edge:** "고급" → "localhost로 이동(안전하지 않음)"
2. **Firefox:** "고급" → "위험을 감수하고 계속"
3. **Safari:** "고급" → "웹 사이트 방문"

이는 개발 환경에서 정상적인 동작입니다.

### 파일 구조

```
backend/
├── ssl/                    # SSL 인증서 (gitignore됨)
│   ├── server.key         # 개인키
│   └── server.crt         # 인증서
├── generate_ssl_cert.sh   # SSL 인증서 생성 스크립트
├── run_dev_https.sh       # HTTPS 서버 실행 스크립트
└── ...
```

## 쿠키 인증 시스템

### 쿠키 종류

**1. 이메일 기반 인증:**
- **쿠키명:** `auth`
- **값:** 이메일 주소 (itsdangerous로 서명)
- **용도:** 이메일/비밀번호 로그인 사용자

**2. Google OAuth2 인증:**
- **쿠키명:** `auth-google`
- **값:** 사용자 ID (itsdangerous로 서명)
- **용도:** Google 로그인 사용자

**3. 네이버 OAuth2 인증:**
- **쿠키명:** `auth-naver`
- **값:** 사용자 ID (itsdangerous로 서명)
- **용도:** 네이버 로그인 사용자

**4. 카카오 OAuth2 인증:**
- **쿠키명:** `auth-kakao`
- **값:** 사용자 ID (itsdangerous로 서명)
- **용도:** 카카오 로그인 사용자

### 쿠키 속성

모든 인증 쿠키는 다음 속성을 가집니다:
```python
response.set_cookie(
    key='auth',  # 또는 'auth-google', 'auth-naver', 'auth-kakao'
    value=signed_data,
    httponly=True,    # JavaScript에서 접근 불가 (XSS 방지)
    secure=True,      # HTTPS에서만 전송
    max_age=31536000  # 1년 (선택적)
)
```

### 쿠키 서명 시스템

**itsdangerous 라이브러리 사용:**
- **서명 키:** `env.py`의 `COOKIE_KEY`
- **서명 방식:** URLSafeSerializer
- **보안:** 쿠키 값 변조 불가, 서명 검증으로 무결성 보장

**구현 예시:**
```python
from itsdangerous import URLSafeSerializer

# 쿠키 생성
serializer = URLSafeSerializer(COOKIE_KEY)
signed_data = serializer.dumps("user_data")

# 쿠키 검증
try:
    user_data = serializer.loads(signed_cookie_value)
    # 유효한 쿠키
except:
    # 유효하지 않은 쿠키 (변조됨)
```

### 프론트엔드 쿠키 확인

**JavaScript로 로그인 상태 확인:**
```javascript
// 쿠키 존재 여부만 확인 (값은 HTTPOnly로 접근 불가)
function isLoggedIn() {
    return document.cookie.includes('auth=') || 
           document.cookie.includes('auth-google=') ||
           document.cookie.includes('auth-naver=') ||
           document.cookie.includes('auth-kakao=');
}

// 로그아웃 (서버 API 호출 필요)
function logout() {
    fetch('/logout', { method: 'POST' })
        .then(() => location.reload());
}
```

**쿠키 기반 인증의 장점:**
- XSS 공격에 안전 (HTTPOnly)
- CSRF 공격 방지 가능 (SameSite 속성)
- 서버에서 쿠키 유효성 완전 제어
- JWT와 달리 서버측에서 즉시 무효화 가능
