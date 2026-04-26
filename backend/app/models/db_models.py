"""
SQLModel 기반 DB 테이블 모델
기존 Pydantic 모델(tax.py)의 Enum/Request 모델은 그대로 사용하고,
DB 테이블 전용 모델만 여기에 정의합니다.
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date, datetime

from app.models.tax import BasketType, TransactionType, PriceSource, ScheduleType, AssetScope, ScheduleStatus, AdjustmentType


# ─── 1. stock_transactions ────────────────────────────────────────
class DBStockTransaction(SQLModel, table=True):
    __tablename__ = "stock_transactions"

    id: str = Field(primary_key=True)
    asset_id: str = Field(index=True)
    basket_id: str = Field(index=True)
    basket_type: BasketType
    transaction_type: TransactionType
    trade_date: date
    settlement_date: date
    quantity: float
    unit_price: float
    total_amount: float
    avg_cost_snapshot: Optional[float] = None
    realized_gain: Optional[float] = None
    tax_reversal: Optional[float] = None
    fiscal_year: int
    created_by: str = "system"
    created_at: datetime


# ─── 2. evaluation_prices ─────────────────────────────────────────
class DBEvaluationPrice(SQLModel, table=True):
    __tablename__ = "evaluation_prices"

    id: str = Field(primary_key=True)
    asset_id: str = Field(index=True)
    basket_id: Optional[str] = None
    eval_date: date
    price: float
    price_source: PriceSource
    evaluation_schedule_id: Optional[str] = None
    input_by: str = "system"
    input_at: datetime


# ─── 3. evaluation_schedules ──────────────────────────────────────
class DBEvaluationSchedule(SQLModel, table=True):
    __tablename__ = "evaluation_schedules"

    id: str = Field(primary_key=True)
    schedule_type: ScheduleType
    eval_base_date: date
    asset_scope: AssetScope
    basket_id: Optional[str] = None
    status: ScheduleStatus
    auto_triggered: bool
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    created_at: datetime


# ─── 4. tax_adjustments ───────────────────────────────────────────
class DBTaxAdjustment(SQLModel, table=True):
    __tablename__ = "tax_adjustments"

    id: str = Field(primary_key=True)
    asset_id: str = Field(index=True)
    basket_id: str = Field(index=True)
    fiscal_year: int
    evaluation_schedule_id: str
    avg_cost: float
    book_value: float
    tax_value: float
    book_tax_diff: float
    adjustment_type: AdjustmentType
    realized_gain: Optional[float] = None


# ─── 5. holdings_snapshot ─────────────────────────────────────────
class DBHoldingsSnapshot(SQLModel, table=True):
    __tablename__ = "holdings_snapshot"

    id: str = Field(primary_key=True)
    asset_id: str = Field(index=True)
    basket_id: str = Field(index=True)
    snapshot_date: date
    holding_quantity: float
    avg_cost: float
    total_cost: float
    eval_price: Optional[float] = None
    eval_amount: Optional[float] = None
    unrealized_gain: Optional[float] = None
    evaluation_schedule_id: str
