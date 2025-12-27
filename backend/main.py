# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from interface.recommendation_router import router as recommendation_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="🧠 홈 추천 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # To Do. 개발이 끝나고 배포 시 실제 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(recommendation_router)