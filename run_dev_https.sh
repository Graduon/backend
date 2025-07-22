#!/bin/bash

# 개발용 HTTPS 서버 실행 스크립트
echo "🚀 개발용 HTTPS 서버 시작..."

# SSL 인증서가 없으면 생성
if [ ! -f "ssl/server.key" ] || [ ! -f "ssl/server.crt" ]; then
    echo "📋 SSL 인증서가 없습니다. 생성 중..."
    ./generate_ssl_cert.sh
fi

echo ""
echo "🌐 서버 정보:"
echo "   - HTTPS: https://localhost:8000"
echo "   - API 문서: https://localhost:8000/docs"
echo "   - Google OAuth: https://localhost:8000/auth/google/login"
echo ""
echo "⚠️  브라우저에서 SSL 경고가 나타나면 '고급' → '계속 진행'을 클릭하세요."
echo ""
echo "🛑 서버를 종료하려면 Ctrl+C를 누르세요."
echo ""

# HTTPS로 uvicorn 실행
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile ssl/server.key \
    --ssl-certfile ssl/server.crt \
    --reload