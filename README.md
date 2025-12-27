# 31IE - AI 기반 상품 추천 시스템

E-commerce 플랫폼을 위한 MLOps 기반 상품 추천 시스템입니다. Wide & Deep 딥러닝 모델을 사용하여 사용자의 거래 이력과 행동 패턴을 기반으로 개인화된 상품을 추천합니다.

## 기술 스택

### Frontend
- **React 18.2** + TypeScript
- **Vite 6.0** (빌드 도구)
- **Tailwind CSS** + Shadcn UI
- **React Router DOM**

### Backend (API Server)
- **FastAPI 0.111**
- **SQLAlchemy 2.0** (ORM)
- **MySQL 8.0**
- **Alembic** (DB 마이그레이션)

### Backend ML (ML 추론 서버)
- **FastAPI 0.111**
- **PyTorch 2.1** (딥러닝)
- **Scikit-learn 1.2**
- **Pandas / NumPy**

### Infrastructure
- **Docker** & **Docker Compose**

## 프로젝트 구조

```
31IE/
├── frontend/                    # React 프론트엔드
│   ├── src/
│   │   ├── api/                # API 클라이언트
│   │   ├── components/         # UI 컴포넌트
│   │   ├── screens/            # 페이지 컴포넌트
│   │   └── assets/             # 정적 파일
│   ├── Dockerfile
│   └── package.json
│
├── backend/                     # FastAPI REST API 서버
│   ├── main.py                 # 앱 진입점
│   ├── application/            # 비즈니스 로직
│   │   ├── schemas/            # Pydantic 스키마
│   │   └── services/           # 서비스 레이어
│   ├── interface/              # API 라우터
│   ├── infra/                  # 인프라 레이어
│   │   ├── db/                 # DB 설정
│   │   └── db_models/          # SQLAlchemy 모델
│   ├── alembic/                # DB 마이그레이션
│   ├── static/images/          # 상품 이미지
│   ├── Dockerfile
│   └── requirements.txt
│
├── backendMl/                   # ML 추론 서버
│   ├── main.py                 # ML 서버 진입점
│   ├── config.yaml             # 모델 하이퍼파라미터
│   ├── model/                  # ML 모델
│   │   ├── model_arch.py       # Wide & Deep 아키텍처
│   │   ├── model_weight/       # 학습된 모델 가중치
│   │   ├── inference.py        # 추론 로직
│   │   └── preprocess.py       # 전처리
│   ├── background/             # 백그라운드 워커
│   │   ├── sync_worker.py      # 데이터 동기화
│   │   └── inference_worker.py # 일일 추론 스케줄러
│   ├── curd/                   # CRUD 작업
│   ├── Dockerfile
│   └── requirements.txt
│
└── docker-compose.yml           # 컨테이너 오케스트레이션
```

## 시스템 아키텍처

```
┌─────────────────┐
│   Frontend      │ Port 5173
│   (React)       │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   Backend API   │ Port 8000
│   (FastAPI)     │──────────────┐
└────────┬────────┘              │
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   MySQL DB      │◄────│   ML Backend    │ Port 8001
│   (Port 3307)   │     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘
```

## 주요 기능

### 1. 프론트엔드
- 네비게이션 바, 배너 캐러셀 (3초 자동 회전)
- 추천 상품 그리드 (4열 레이아웃)
- 상품 카드: 이미지, 제목, 가격 표시
- 로딩 상태 및 에러 핸들링

### 2. Backend API
- **엔드포인트**: `GET /recommendations/home?user_id={id}`
- **응답**: 사용자 닉네임 + 추천 상품 목록
- 상품 이미지 정적 파일 서빙

### 3. ML Backend
- **Wide & Deep 신경망** 모델
  - Wide: 선형 레이어 (memorization)
  - Deep: 다층 신경망 + BatchNorm + Dropout
  - 출력: 16개 상품 카테고리
- **백그라운드 워커**:
  - Sync Worker: 메인 DB ↔ ML DB 동기화
  - Inference Worker: 일일 추론 스케줄링

## 데이터베이스 모델

- **User**: 사용자 정보
- **Product**: 상품 정보
- **Category**: 상품 카테고리
- **ProductImage**: 상품 이미지
- **ProductReview**: 상품 리뷰
- **Order / OrderItem**: 주문 정보
- **Recommendation**: 추천 결과 저장
- **Coupon**: 쿠폰 정보

## 실행 방법

### Docker Compose (권장)

```bash
# 전체 서비스 실행
docker-compose up

# 백그라운드 실행
docker-compose up -d

# 서비스 중지
docker-compose down
```

### 개별 실행

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**ML Backend**
```bash
cd backendMl
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 포트 구성

| 서비스 | 포트 |
|--------|------|
| Frontend | 5173 |
| Backend API | 8000 |
| ML Backend | 8001 |
| MySQL | 3307 |

## API 응답 예시

```json
{
  "user_nickname": "홍길동",
  "recommendations": [
    {
      "product_id": 1,
      "category_id": 3,
      "title": "상품명",
      "price": 29900.0,
      "image_url": "/static/images/products/category3/product1.jpg"
    }
  ]
}
```

## 모델 설정 (config.yaml)

```yaml
input_dim: 특성 차원
hidden_dims: [256, 128, 64]
output_dim: 16  # 카테고리 수
dropout: 0.3
```

## 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.
