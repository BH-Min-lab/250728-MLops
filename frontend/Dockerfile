# 1. Node 이미지
FROM node:18-alpine

# 2. 작업 디렉토리
WORKDIR /app

# 3. 의존성 파일만 먼저 복사 (캐시 최적화)
COPY package.json package-lock.json ./

# 4. 의존성 설치
RUN npm install

# 5. 나머지 모든 소스 코드 복사
COPY . .

# 6. 외부 접속 허용
ENV HOST=0.0.0.0

# 7. 포트 노출
EXPOSE 5173

# 8. 개발 서버 실행
CMD ["npm", "run", "dev"]
