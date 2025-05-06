FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY . .

# 환경 변수 설정
ENV PORT=5000
ENV HOST=0.0.0.0

# healthcheck 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/ || exit 1

# Flask 앱 실행
# 시작 스크립트에 실행 권한 부여
RUN chmod +x start.sh

# 시작 스크립트를 통해 애플리케이션 실행
CMD ["./start.sh"]