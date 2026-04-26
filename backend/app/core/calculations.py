from datetime import date, timedelta
from typing import List
import holidays

from sqlmodel import Session, select
from app.models.db_models import DBStockTransaction
from app.models.tax import BasketType, TransactionType

# 한국 공휴일 캘린더 (모듈 레벨에서 1회 생성, 필요한 연도 자동 확장)
_kr_holidays = holidays.country_holidays("KR")


def calculate_settlement_date(basket_type: BasketType, trade_date: date) -> date:
    """
    영업일 기준 결제일 산출
    - 고유계좌(PROPRIETARY) / 증권사(SECURITIES): T+2 영업일
    - 펀드(FUND): T+3 영업일
    주말(토·일) 및 한국 공휴일을 제외한 영업일 기준으로 계산합니다.
    """
    business_days = 2 if basket_type in (BasketType.PROPRIETARY, BasketType.SECURITIES) else 3
    return _get_nth_business_day(trade_date, business_days)


def _get_nth_business_day(start_date: date, n: int) -> date:
    """
    start_date 이후 n번째 영업일을 반환합니다.
    영업일 = 토·일·한국 공휴일을 제외한 날
    """
    current = start_date
    count = 0
    while count < n:
        current += timedelta(days=1)
        if _is_business_day(current):
            count += 1
    return current


def _is_business_day(d: date) -> bool:
    """토·일·한국공휴일이면 False"""
    if d.weekday() >= 5:  # 5=토, 6=일
        return False
    if d in _kr_holidays:
        return False
    return True


def calc_avg_cost(
    session: Session,
    asset_id: str,
    basket_id: str,
    up_to_date: date
) -> float:
    """
    총평균단가 계산 로직 — 이동잔존금액법 (Running Balance)

    시간순으로 매수/매도를 재현하면서
    매도 시 해당 시점의 총평균단가 × 매도수량만큼 잔존금액을 차감합니다.
    """
    stmt = (
        select(DBStockTransaction)
        .where(
            DBStockTransaction.asset_id == asset_id,
            DBStockTransaction.basket_id == basket_id,
            DBStockTransaction.trade_date <= up_to_date,
            DBStockTransaction.transaction_type.in_([TransactionType.BUY, TransactionType.SELL])
        )
        .order_by(DBStockTransaction.trade_date, DBStockTransaction.created_at)
    )
    relevant_txs = session.exec(stmt).all()

    running_qty = 0.0
    running_amount = 0.0

    for t in relevant_txs:
        if t.transaction_type == TransactionType.BUY:
            running_amount += t.total_amount
            running_qty += t.quantity
        elif t.transaction_type == TransactionType.SELL:
            if running_qty > 0:
                current_avg = running_amount / running_qty
                running_amount -= t.quantity * current_avg
                running_qty -= t.quantity

    if running_qty <= 0:
        return 0.0
    return running_amount / running_qty


def get_holding_quantity(
    session: Session,
    asset_id: str,
    basket_id: str,
    up_to_date: date
) -> float:
    """보유수량 산출 (매수 합계 - 매도 합계)"""
    stmt = (
        select(DBStockTransaction)
        .where(
            DBStockTransaction.asset_id == asset_id,
            DBStockTransaction.basket_id == basket_id,
            DBStockTransaction.trade_date <= up_to_date,
        )
    )
    relevant_txs = session.exec(stmt).all()

    qty = 0.0
    for t in relevant_txs:
        if t.transaction_type == TransactionType.BUY:
            qty += t.quantity
        elif t.transaction_type == TransactionType.SELL:
            qty -= t.quantity
    return qty
