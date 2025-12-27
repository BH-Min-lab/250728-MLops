#!/bin/bash

echo "[ENTRYPOINT] Waiting for database..."
for i in {1..15}; do
  mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" > /dev/null 2>&1 && break
  echo "[$i] DB is unavailable - sleeping"
  sleep 1
done

# echo "[ENTRYPOINT] Running Alembic migrations..."
# 최신 마이그레이션 스크립트를 실행 [배포용]
# alembic upgrade head

echo "[ENTRYPOINT] Applying Alembic migrations first..."
alembic upgrade head

echo "[ENTRYPOINT] Running Alembic autogenerate revision..."
# DB가 최신 상태가 된 후에 자동 리비전을 시도
alembic revision --autogenerate -m "auto migration $(date +%Y%m%d%H%M%S)" || echo "No changes to migrate."

echo "[ENTRYPOINT] Applying Alembic migrations after autogenerate..."
alembic upgrade head

echo "[ENTRYPOINT] Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload