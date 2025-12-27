# [file] main.py  
# [description] FastAPI 서버 내 백그라운드 스레드로 운영 DB와 ML DB 동기화 작업 주기 실행
from fastapi import FastAPI
import threading
import logging
from background.sync_worker import sync_worker
from background.inference_worker import inference_worker

app = FastAPI(title="🧠 추론용 FastAPI 서버")

def start_background_workers():
    threading.Thread(target=sync_worker, daemon=True).start()
    # threading.Thread(target=inference_worker, daemon=True).start()

@app.on_event("startup")
def on_startup():
    logging.info("Starting background workers")
    start_background_workers()

@app.get("/")
async def root():
    return {"message": "🧠 서버 정상 작동 중입니다."}