# 로그인 API 명세

> 이 명세는 `naver_auth.py` 개발용으로만 사용합니다.

## API 기본 정보

| 메서드      | 인증     | 요청 URL                                   | 출력 포맷     | 설명                |
|----------|--------|------------------------------------------|-----------|-------------------|
| GET/POST | Oauth2 | https://nid.naver.com/oauth2.0/authorize | URL 리다이렉트 | 네이버 로그인 인증 요청     |
| GET/POST | Oauth2 | https://nid.naver.com/oauth2.0/token     | json      | 접근 토큰 발급/갱신/삭제 요청 |

## 요청 변수

### 네이버 로그인 인증 요청

| 요청 변수명        | 타입     | 필수 여부 | 기본값  | 설명                                                                                           |
|---------------|--------|-------|------|----------------------------------------------------------------------------------------------|
| response_type | string | Yes   | code | 인증 과정에 대한 내부 구분값으로 'code'로 전송해야 함                                                            |
| client_id     | string | Yes   |      | 애플리케이션 등록 시 발급받은 Client ID 값                                                                 |
| redirect_uri  | string | Yes   |      | 애플리케이션을 등록 시 입력한 Callback URL 값으로 URL 인코딩을 적용한 값                                             |
| state         | string | Yes   |      | 사이트 간 요청 위조(cross-site request forgery) 공격을 방지하기 위해 애플리케이션에서 생성한 상태 토큰값으로 URL 인코딩을 적용한 값을 사용 |
| scope         | string | No    |      | 접근 허용 범위를 처리하기 위한 내부 구분값으로 전송할 필요 없음                                                         |

### 접근 토큰 발급/갱신/삭제 요청 

**접근 토큰 갱신 / 삭제 요청시 access_token 값은 URL 인코딩하셔야 합니다**

| 요청 변수명           | 타입     | 필수 여부   | 기본값     | 설명                                                                                           |
|------------------|--------|---------|---------|----------------------------------------------------------------------------------------------|
| grant_type       | string | Yes     | code    | 인증 과정에 대한 구분값. 발급: 'authorization_code', 갱신: 'refresh_token', 삭제: 'delete'                   |
| client_id        | string | Yes     |         | 애플리케이션 등록 시 발급받은 Client ID 값                                                                 |
| client_secret    | string | Yes     |         | 애플리케이션 등록 시 발급받은 Client secret 값                                                             |
| code             | string | 발급 때 필수 |         | 로그인 인증 요청 API 호출에 성공하고 리턴받은 인증코드값 (authorization code)                                       |
| state            | string | 발급 때 필수 |         | 사이트 간 요청 위조(cross-site request forgery) 공격을 방지하기 위해 애플리케이션에서 생성한 상태 토큰값으로 URL 인코딩을 적용한 값을 사용 |
| refresh_token    | string | 갱신 때 필수 |         | 네이버 사용자 인증에 성공하고 발급받은 갱신 토큰(refresh token)                                                   |
| access_token     | string | 삭제 때 필수 |         | 발급받은 접근 토큰으로 URL 인코딩을 적용한 값을 사용                                                              |
| service_provider | string | 삭제 때 필수 | 'NAVER' | 인증 제공자 이름으로 'NAVER'로 세팅해 전송                                                                  |

## 출력 결과

###  네이버 로그인 인증 요청

네이버 로그인 인증 요청 API를 호출했을 때 사용자가 네이버로 로그인하지 않은 상태이면 네이버 로그인 화면으로 이동하고, 사용자가 네이버에 로그인한 상태이면 기본 정보 제공 동의 확인 화면으로 이동합니다. 네이버 로그인과 정보 제공 동의 과정이 완료되면 콜백 URL에 code값과 state 값이 URL 문자열로 전송됩니다. code 값은 접근 토큰 발급 요청에 사용합니다. API 요청 실패시에는 에러 코드와 에러 메시지가 전송됩니다.

* API 요청 성공시 : http://콜백URL/redirect?code={code값}&state={state값}
* API 요청 실패시 : http://콜백URL/redirect?state={state값}&error={에러코드값}&error_description={에러메시지}


| 필드                | 	타입     | 설명                                                           |
|-------------------|---------|--------------------------------------------------------------|
| code              | 	string | 	네이버 로그인 인증에 성공하면 반환받는 인증 코드, 접근 토큰(access token) 발급에 사용     |
| state             | 	string | 	사이트 간 요청 위조 공격을 방지하기 위해 애플리케이션에서 생성한 상태 토큰으로 URL 인코딩을 적용한 값 |
| error             | 	string | 	네이버 로그인 인증에 실패하면 반환받는 에러 코드                                 |
| error_description | 	string | 	네이버 로그인 인증에 실패하면 반환받는 에러 메시지                                |

### 접근 토큰 발급 요청

| 필드                | 	타입      | 	설명                                              |
|-------------------|----------|--------------------------------------------------|
| access_token      | 	string  | 	접근 토큰, 발급 후 expires_in 파라미터에 설정된 시간(초)이 지나면 만료됨 |
| refresh_token     | 	string  | 	갱신 토큰, 접근 토큰이 만료될 경우 접근 토큰을 다시 발급받을 때 사용        |
| token_type        | 	string  | 	접근 토큰의 타입으로 Bearer와 MAC의 두 가지를 지원               |
| expires_in        | 	integer | 	접근 토큰의 유효 기간(초 단위)                              |
| error             | 	string  | 	에러 코드                                           |
| error_description | 	string  | 	에러 메시지                                          |

### 접근 토큰 갱신 요청

| 필드                | 	타입      | 	설명                                              |
|-------------------|----------|--------------------------------------------------|
| access_token      | 	string  | 	접근 토큰, 발급 후 expires_in 파라미터에 설정된 시간(초)이 지나면 만료됨 |
| token_type        | 	string  | 	접근 토큰의 타입으로 Bearer와 MAC의 두 가지를 지원               |
| expires_in        | 	integer | 	접근 토큰의 유효 기간(초 단위)                              |
| error	            | string   | 	에러 코드                                           |
| error_description | 	string  | 	에러 메시지                                          |

### 접근 토큰 삭제 요청

| 필드                | 	타입       | 	설명                        |
|-------------------|-----------|----------------------------|
| access_token      | 	string   | 	삭제 처리된 접근 토큰 값            |
| result            | 	string   | 	처리 결과가 성공이면 'success'가 리턴 |
| expires_in        | 	integer	 | 접근 토큰의 유효 기간(초 단위)         |
| error	            | string    | 	에러 코드                     |
| error_description | 	string   | 	에러 메시지                    |


# 회원 프로필 조회 API 명세

## API 기본 정보

* 메서드: GET
* 인증: Oauth2
* 요청 URL: https://openapi.naver.com/v1/nid/me
* 출력 포맷: json

## 요청 헤더

Authorization
: 접근 토큰(access token)을 전달하는 헤더
다음과 같은 형식으로 헤더 값에 접근 토큰(access token)을 포함합니다. 토큰 타입은 "Bearer"로 값이 고정돼 있습니다. Authorization: {토큰 타입] {접근 토큰]

예시:
```text
Authorization: Bearer AAAAOLtP40eH6P5S4Z4FpFl77n3FD5I+W3ost3oDZq/nbcS+7MAYXwXbT3Y7Ib3dnvcqHkcK0e5/rw6ajF7S/QlJAgUukpp1OGkG0vzi16hcRNYX6RcQ6kPxB0oAvqfUPJiJw==
```

## 출력 결과

회원의 네이버아이디는 출력결과에 포함되지 않습니다. 대신 프로필조회 api 호출 결과에 포함되는 'id'라는 값을 이용해서 회원을 구분하시길 바랍니다. 'id'값은 각 애플리케이션마다 회원 별로 유니크한 값으로, 같은 네이버 회원이라도 네이버 로그인을 적용한 애플리케이션이 다르면 id값이 다른 점 유념하시길 바랍니다. 또한 가이드상에는 명시안되어 있지만 출력결과에 포함된 'enc_id'라는 값은 내부적으로 쓰는 값이므로 애플리케이션 개발에서 사용할 일이 없다고 보면되겠습니다.

| 필드                     | 	타입     | 	필수 여부 | 	설명                                                                                                                                   |
|------------------------|---------|--------|---------------------------------------------------------------------------------------------------------------------------------------|
| resultcode             | 	String | 	Y     | 	API 호출 결과 코드                                                                                                                         |
| message                | 	String | 	Y     | 	호출 결과 메시지                                                                                                                            |
| response/id            | 	String | 	Y     | 	동일인 식별 정보. 네이버 아이디마다 고유하게 발급되는 유니크한 일련번호 값(API 호출 결과로 네이버 아이디값은 제공하지 않으며, 대신 'id'라는 애플리케이션당 유니크한 일련번호값을 이용해서 자체적으로 회원정보를 구성하셔야 합니다.) |
| response/nickname      | 	String | 	Y     | 	사용자 별명(별명이 설정되어 있지 않으면 id*** 형태로 리턴됩니다.)                                                                                             |
| response/name          | 	String | 	Y     | 	사용자 이름                                                                                                                               |
| response/email         | 	String | 	Y     | 	사용자 메일 주소. 기본적으로 네이버 내정보에 등록되어 있는 '기본 이메일' 즉 네이버ID@naver.com 값이나, 사용자가 다른 외부메일로 변경했을 경우는 변경된 이메일 주소로 됩니다.                            |
| response/gender        | 	String | 	Y     | 	성별. F: 여성, M: 남성, U: 확인불가                                                                                                            |
| response/age           | 	String | 	Y     | 	사용자 연령대                                                                                                                              |
| response/birthday      | 	String | 	Y     | 	사용자 생일(MM-DD 형식)                                                                                                                     |
| response/profile_image | 	String | 	Y     | 	사용자 프로필 사진 URL                                                                                                                       |
| response/birthyear     | 	String | 	Y     | 	출생연도                                                                                                                                 |
| response/mobile        | 	String | 	Y     | 	휴대전화번호                                                                                                                               |
