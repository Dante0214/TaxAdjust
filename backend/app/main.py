from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as tax_router

app = FastAPI(
    title="Tax Adjustment Management API",
    description="상장주식 매수/평가/매도 세무조정 및 유보금 검증 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 개발 환경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tax_router, prefix="/api/tax", tags=["Tax"])

@app.get("/")
def root():
    return {"message": "Tax Adjustment API is running"}
