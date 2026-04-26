from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
from datetime import datetime

from sqlmodel import select

from app.models.tax import (
    BuyRequest, SellRequest, EvaluateRequest, DepositRequest,
    BasketType, TransactionType, PriceSource, ScheduleStatus, AssetScope, AdjustmentType
)
from app.models.db_models import (
    DBStockTransaction, DBEvaluationPrice, DBEvaluationSchedule,
    DBTaxAdjustment, DBHoldingsSnapshot
)
from app.core.database import SessionDep
from app.core.calculations import calc_avg_cost, get_holding_quantity, calculate_settlement_date

router = APIRouter()


@router.post("/deposit")
def deposit_cash(req: DepositRequest, session: SessionDep):
    tx = DBStockTransaction(
        id=str(uuid.uuid4()),
        asset_id="CASH",
        basket_id=req.basket_id,
        basket_type=req.basket_type,
        transaction_type=TransactionType.DEPOSIT,
        trade_date=req.trade_date,
        settlement_date=req.trade_date,  # 입금은 즉시 결제 완료 처리
        quantity=1,
        unit_price=req.amount,
        total_amount=req.amount,
        fiscal_year=req.trade_date.year,
        created_at=datetime.now()
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@router.post("/buy")
def buy_stock(req: BuyRequest, session: SessionDep):
    settlement_date = calculate_settlement_date(req.basket_type, req.trade_date)

    tx = DBStockTransaction(
        id=str(uuid.uuid4()),
        asset_id=req.asset_id,
        basket_id=req.basket_id,
        basket_type=req.basket_type,
        transaction_type=TransactionType.BUY,
        trade_date=req.trade_date,
        settlement_date=settlement_date,
        quantity=req.quantity,
        unit_price=req.unit_price,
        total_amount=req.quantity * req.unit_price,
        fiscal_year=req.trade_date.year,
        created_at=datetime.now()
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@router.post("/sell")
def sell_stock(req: SellRequest, session: SessionDep):
    # 1. 보유수량 검증
    holding_qty = get_holding_quantity(session, req.asset_id, req.basket_id, req.trade_date)
    if req.quantity > holding_qty:
        raise HTTPException(status_code=400, detail="InsufficientHoldingError: 매도 수량이 보유 수량을 초과합니다.")

    # 2. 총평균단가 계산
    avg_cost = calc_avg_cost(session, req.asset_id, req.basket_id, req.trade_date)

    # 3. 처분손익 계산
    realized_gain = (req.unit_price - avg_cost) * req.quantity

    # 4. basket_type 찾기 (가장 최근 BUY 기록에서 추출)
    buy_tx = session.exec(
        select(DBStockTransaction)
        .where(
            DBStockTransaction.asset_id == req.asset_id,
            DBStockTransaction.basket_id == req.basket_id,
            DBStockTransaction.transaction_type == TransactionType.BUY
        )
        .order_by(DBStockTransaction.created_at.desc())
    ).first()
    basket_type = buy_tx.basket_type if buy_tx else BasketType.PROPRIETARY

    settlement_date = calculate_settlement_date(basket_type, req.trade_date)

    # 5. 유보 추인액(Tax Reversal) 계산
    tax_reversal = 0.0
    latest_snapshot = session.exec(
        select(DBHoldingsSnapshot)
        .where(
            DBHoldingsSnapshot.asset_id == req.asset_id,
            DBHoldingsSnapshot.basket_id == req.basket_id
        )
        .order_by(DBHoldingsSnapshot.snapshot_date.desc())
    ).first()

    if latest_snapshot and latest_snapshot.holding_quantity > 0:
        ratio = req.quantity / latest_snapshot.holding_quantity
        snapshot_reserve = latest_snapshot.eval_amount - latest_snapshot.total_cost
        tax_reversal = snapshot_reserve * ratio

        # 추인 원장 기록
        if tax_reversal != 0:
            tax_adj = DBTaxAdjustment(
                id=str(uuid.uuid4()),
                asset_id=req.asset_id,
                basket_id=req.basket_id,
                fiscal_year=req.trade_date.year,
                evaluation_schedule_id="SELL_EVENT",
                avg_cost=avg_cost,
                book_value=0,
                tax_value=0,
                book_tax_diff=-tax_reversal,  # 반대 부호로 기록
                adjustment_type=AdjustmentType.REVERSAL,
                realized_gain=realized_gain
            )
            session.add(tax_adj)

    tx = DBStockTransaction(
        id=str(uuid.uuid4()),
        asset_id=req.asset_id,
        basket_id=req.basket_id,
        basket_type=basket_type,
        transaction_type=TransactionType.SELL,
        trade_date=req.trade_date,
        settlement_date=settlement_date,
        quantity=req.quantity,
        unit_price=req.unit_price,
        total_amount=req.quantity * req.unit_price,
        avg_cost_snapshot=avg_cost,
        realized_gain=realized_gain,
        tax_reversal=tax_reversal,
        fiscal_year=req.trade_date.year,
        created_at=datetime.now()
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@router.post("/evaluate")
def evaluate_stocks(req: EvaluateRequest, session: SessionDep):
    # STEP 1: 스케줄 생성
    schedule = DBEvaluationSchedule(
        id=str(uuid.uuid4()),
        schedule_type=req.schedule_type,
        eval_base_date=req.eval_base_date,
        asset_scope=AssetScope.ALL,
        status=ScheduleStatus.CONFIRMED,
        auto_triggered=False,
        confirmed_by="admin",
        confirmed_at=datetime.now(),
        created_at=datetime.now()
    )
    session.add(schedule)

    results = []
    for price_input in req.prices:
        # STEP 2: 가격 원장 기록
        eval_price = DBEvaluationPrice(
            id=str(uuid.uuid4()),
            asset_id=price_input.asset_id,
            basket_id=price_input.basket_id,
            eval_date=req.eval_base_date,
            price=price_input.price,
            price_source=PriceSource.MANUAL,
            evaluation_schedule_id=schedule.id,
            input_at=datetime.now()
        )
        session.add(eval_price)

        # 보유수량 확인
        qty = get_holding_quantity(session, price_input.asset_id, price_input.basket_id, req.eval_base_date)
        if qty <= 0:
            continue

        avg_cost = calc_avg_cost(session, price_input.asset_id, price_input.basket_id, req.eval_base_date)
        total_cost = avg_cost * qty
        eval_amount = price_input.price * qty

        snapshot = DBHoldingsSnapshot(
            id=str(uuid.uuid4()),
            asset_id=price_input.asset_id,
            basket_id=price_input.basket_id,
            snapshot_date=req.eval_base_date,
            holding_quantity=qty,
            avg_cost=avg_cost,
            total_cost=total_cost,
            eval_price=price_input.price,
            eval_amount=eval_amount,
            unrealized_gain=eval_amount - total_cost,
            evaluation_schedule_id=schedule.id
        )
        session.add(snapshot)

        # STEP 3-4: Tax Adjustment
        book_tax_diff = eval_amount - total_cost
        tax_adj = DBTaxAdjustment(
            id=str(uuid.uuid4()),
            asset_id=price_input.asset_id,
            basket_id=price_input.basket_id,
            fiscal_year=req.eval_base_date.year,
            evaluation_schedule_id=schedule.id,
            avg_cost=avg_cost,
            book_value=eval_amount,
            tax_value=total_cost,
            book_tax_diff=book_tax_diff,
            adjustment_type=AdjustmentType.RESERVE if book_tax_diff > 0 else AdjustmentType.REVERSAL
        )
        session.add(tax_adj)
        results.append(tax_adj)

    session.commit()
    return {"message": "평가 및 세무조정 완료", "schedule_id": schedule.id, "adjustments_count": len(results)}


@router.get("/dashboard")
def get_dashboard_data(session: SessionDep):
    """현재 보유 잔고(총평균단가 반영) 및 전체 트랜잭션 반환"""
    today = datetime.now().date()

    # 고유 asset_id + basket_id 조합 수집
    buy_sell_txs = session.exec(
        select(DBStockTransaction)
        .where(DBStockTransaction.transaction_type.in_([TransactionType.BUY, TransactionType.SELL]))
    ).all()

    asset_basket_keys: Dict[str, Dict[str, Any]] = {}
    for tx in buy_sell_txs:
        key = f"{tx.asset_id}_{tx.basket_id}"
        if key not in asset_basket_keys:
            asset_basket_keys[key] = {
                "asset_id": tx.asset_id,
                "basket_id": tx.basket_id,
                "basket_type": tx.basket_type,
            }

    # calc_avg_cost / get_holding_quantity로 통일 산출
    portfolio = []
    for info in asset_basket_keys.values():
        qty = get_holding_quantity(session, info["asset_id"], info["basket_id"], today)
        if qty <= 0:
            continue

        avg_cost = calc_avg_cost(session, info["asset_id"], info["basket_id"], today)

        # 최신 평가 내역 찾기
        latest_snapshot = session.exec(
            select(DBHoldingsSnapshot)
            .where(
                DBHoldingsSnapshot.asset_id == info["asset_id"],
                DBHoldingsSnapshot.basket_id == info["basket_id"]
            )
            .order_by(DBHoldingsSnapshot.snapshot_date.desc())
        ).first()

        tax_reserve = 0
        eval_price = 0
        eval_amount = 0
        if latest_snapshot:
            ratio = qty / latest_snapshot.holding_quantity if latest_snapshot.holding_quantity > 0 else 0
            tax_reserve = (latest_snapshot.eval_amount - latest_snapshot.total_cost) * ratio
            eval_price = latest_snapshot.eval_price
            eval_amount = eval_price * qty

        portfolio.append({
            "asset_id": info["asset_id"],
            "basket_id": info["basket_id"],
            "basket_type": info["basket_type"],
            "quantity": qty,
            "avg_cost": avg_cost,
            "tax_reserve": tax_reserve,
            "eval_price": eval_price,
            "eval_amount": eval_amount
        })

    # 현금 흐름 계산
    settled_cash = 0.0
    receivable_cash = 0.0

    all_txs = session.exec(select(DBStockTransaction)).all()
    for tx in all_txs:
        if tx.transaction_type == TransactionType.DEPOSIT:
            settled_cash += tx.total_amount
        elif tx.transaction_type == TransactionType.BUY:
            if tx.settlement_date <= today:
                settled_cash -= tx.total_amount
            else:
                receivable_cash -= tx.total_amount
        elif tx.transaction_type == TransactionType.SELL:
            if tx.settlement_date <= today:
                settled_cash += tx.total_amount
            else:
                receivable_cash += tx.total_amount

    # 최근 거래 내역 (정렬)
    sorted_txs = session.exec(
        select(DBStockTransaction).order_by(DBStockTransaction.created_at.desc())
    ).all()

    return {
        "portfolio": portfolio,
        "transactions": sorted_txs,
        "cash_flow": {
            "settled_cash": settled_cash,
            "receivable_cash": receivable_cash
        }
    }
