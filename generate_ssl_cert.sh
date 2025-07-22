#!/bin/bash

# 개발용 자체서명 SSL 인증서 생성 스크립트
echo "🔐 개발용 SSL 인증서 생성 중..."

# ssl 디렉토리 생성
mkdir -p ssl

# 개인키 생성
openssl genrsa -out ssl/server.key 2048

# 인증서 서명 요청(CSR) 생성 및 자체서명 인증서 생성
# -subj 옵션으로 대화형 입력 건너뛰기
openssl req -new -x509 -key ssl/server.key -out ssl/server.crt -days 365 \
    -subj "/C=KR/ST=Seoul/L=Seoul/O=Development/CN=localhost"

# 파일 권한 설정
chmod 600 ssl/server.key
chmod 644 ssl/server.crt

echo "✅ SSL 인증서 생성 완료!"
echo "   - 개인키: ssl/server.key"
echo "   - 인증서: ssl/server.crt"
echo "   - 유효기간: 365일"
echo ""
echo "⚠️  브라우저에서 '안전하지 않음' 경고가 나타나면 '고급' → '계속 진행'을 클릭하세요."
echo "   이는 자체서명 인증서이기 때문에 정상적인 경고입니다."