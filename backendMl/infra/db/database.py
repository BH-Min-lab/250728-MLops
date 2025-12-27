# infra/db/database.py
# 두 DB 세션: MainSessionLocal, MLSessionEngine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# 공통 접속 정보
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# 운영 DB (Main)
Main_DB_NAME = os.getenv("MYSQL_DATABASE")
Main_DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{Main_DB_NAME}"
MainEngine = create_engine(Main_DB_URL, pool_pre_ping=True)
MainSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=MainEngine)

# ML 데이터 DB
ML_DB_NAME = os.getenv("ML_DB_NAME")
ML_DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{ML_DB_NAME}"
MLEngine = create_engine(ML_DB_URL, pool_pre_ping=True)
MLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=MLEngine)