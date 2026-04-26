from sqlmodel import create_engine, Session, SQLModel
from typing import Annotated
from fastapi import Depends

SQLITE_FILE = "tax_adjust.db"
SQLITE_URL = f"sqlite:///{SQLITE_FILE}"

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """앱 시작 시 호출 — 테이블이 없으면 자동 생성"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """요청마다 DB 세션을 제공하고, 종료 시 자동 close"""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
