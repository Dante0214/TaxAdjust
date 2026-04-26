from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as tax_router
from app.core.database import create_db_and_tables

# DB 모델 import — SQLModel.metadata에 등록되어야 create_all이 테이블 생성 가능
import app.models.db_models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 SQLite DB 및 테이블 자동 생성"""
    create_db_and_tables()
    yield


app = FastAPI(
    title="Tax Adjustment Management API",
    description="상장주식 매수/평가/매도 세무조정 및 유보금 검증 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tax_router, prefix="/api/tax", tags=["Tax"])


@app.get("/")
def root():
    return {"message": "Tax Adjustment API is running"}
