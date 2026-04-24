from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class BasketType(str, Enum):
    PROPRIETARY = "PROPRIETARY"
    FUND = "FUND"
    SECURITIES = "SECURITIES"

class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    EVALUATE = "EVALUATE"
    DEPOSIT = "DEPOSIT"

class PriceSource(str, Enum):
    MANUAL = "MANUAL"
    API_KRX = "API_KRX"
    API_BLOOMBERG = "API_BLOOMBERG"

class ScheduleType(str, Enum):
    YEARLY = "YEARLY"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"
    ADHOC = "ADHOC"

class AssetScope(str, Enum):
    ALL = "ALL"
    BASKET_SPECIFIC = "BASKET_SPECIFIC"

class ScheduleStatus(str, Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    CONFIRMED = "CONFIRMED"
    LOCKED = "LOCKED"

class AdjustmentType(str, Enum):
    RESERVE = "RESERVE"
    REVERSAL = "REVERSAL"

# 1. stock_transactions
class StockTransaction(BaseModel):
    id: str
    asset_id: str
    basket_id: str
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

# 2. evaluation_prices
class EvaluationPrice(BaseModel):
    id: str
    asset_id: str
    basket_id: Optional[str] = None
    eval_date: date
    price: float
    price_source: PriceSource
    evaluation_schedule_id: Optional[str] = None
    input_by: str = "system"
    input_at: datetime

# 3. evaluation_schedules
class EvaluationSchedule(BaseModel):
    id: str
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

# 4. tax_adjustments
class TaxAdjustment(BaseModel):
    id: str
    asset_id: str
    basket_id: str
    fiscal_year: int
    evaluation_schedule_id: str
    avg_cost: float
    book_value: float
    tax_value: float
    book_tax_diff: float
    adjustment_type: AdjustmentType
    realized_gain: Optional[float] = None

# 5. holdings_snapshot
class HoldingsSnapshot(BaseModel):
    id: str
    asset_id: str
    basket_id: str
    snapshot_date: date
    holding_quantity: float
    avg_cost: float
    total_cost: float
    eval_price: Optional[float] = None
    eval_amount: Optional[float] = None
    unrealized_gain: Optional[float] = None
    evaluation_schedule_id: str

# API 요청/응답 모델
class BuyRequest(BaseModel):
    asset_id: str
    basket_id: str
    basket_type: BasketType
    trade_date: date
    quantity: float
    unit_price: float

class SellRequest(BaseModel):
    asset_id: str
    basket_id: str
    trade_date: date
    quantity: float
    unit_price: float

class DepositRequest(BaseModel):
    basket_type: BasketType
    basket_id: str
    trade_date: date
    amount: float

class EvalPriceInput(BaseModel):
    asset_id: str
    basket_id: str
    price: float

class EvaluateRequest(BaseModel):
    eval_base_date: date
    schedule_type: ScheduleType
    prices: List[EvalPriceInput]
