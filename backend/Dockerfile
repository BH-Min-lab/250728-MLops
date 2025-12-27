# Python 3.11.13 기반 이미지 사용
FROM python:3.10.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# ✅ entrypoint.sh 복사 및 실행 권한 부여
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# ✅ entrypoint를 기본 실행 명령으로 설정
ENTRYPOINT ["/app/entrypoint.sh"]
