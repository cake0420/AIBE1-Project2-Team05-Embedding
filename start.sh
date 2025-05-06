#!/bin/bash
set -e

echo "Starting embedding API server..."

# 환경 확인
echo "Environment: PORT=$PORT, HOST=$HOST"

# gunicorn으로 애플리케이션 시작
exec gunicorn -c gunicorn_config.py api.index:app