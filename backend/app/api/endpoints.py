from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import uuid
from datetime import datetime

from app.models.tax import (
    StockTransaction, EvaluationPrice, EvaluationSchedule, TaxAdjustment, HoldingsSnapshot,
    BuyRequest, SellRequest, EvaluateRequest, DepositRequest,
    BasketType, TransactionType, PriceSource, ScheduleStatus, AssetScope, AdjustmentType
)
from app.core.calculations import (
    calc_avg_cost, get_holding_quantity, calculate_settlement_date
)

router = APIRouter()

# In-Memory Database (List)
db_stock_transactions: List[StockTransaction] = []
db_evaluation_prices: List[EvaluationPrice] = []
db_evaluation_schedules: List[EvaluationSchedule] = []
db_tax_adjustments: List[TaxAdjustment] = []
db_holdings_snapshot: List[HoldingsSnapshot] = []

@router.post("/deposit", response_model=StockTransaction)
def deposit_cash(req: DepositRequest):
    tx = StockTransaction(
        id=str(uuid.uuid4()),
        asset_id="CASH",
        basket_id=req.basket_id,
        basket_type=req.basket_type,
        transaction_type=TransactionType.DEPOSIT,
        trade_date=req.trade_date,
        settlement_date=req.trade_date, # 입금은 즉시 결제 완료 처리
        quantity=1,
        unit_price=req.amount,
        total_amount=req.amount,
        fiscal_year=req.trade_date.year,
        created_at=datetime.now()
    )
    db_stock_transactions.append(tx)
    return tx

@router.post("/buy", response_model=StockTransaction)
def buy_stock(req: BuyRequest):
    settlement_date = calculate_settlement_date(req.basket_type, req.trade_date)
    
    tx = StockTransaction(
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
    db_stock_transactions.append(tx)
    return tx

@router.post("/sell", response_model=StockTransaction)
def sell_stock(req: SellRequest):
    # 1. 보유수량 검증
    holding_qty = get_holding_quantity(db_stock_transactions, req.asset_id, req.basket_id, req.trade_date)
    if req.quantity > holding_qty:
        raise HTTPException(status_code=400, detail="InsufficientHoldingError: 매도 수량이 보유 수량을 초과합니다.")
    
    # 2. 총평균단가 계산
    avg_cost = calc_avg_cost(db_stock_transactions, req.asset_id, req.basket_id, req.trade_date)
    
    # 3. 처분손익 계산
    realized_gain = (req.unit_price - avg_cost) * req.quantity
    
    # 4. basket_type 찾기 (가장 최근 BUY 기록에서 추출)
    basket_type = BasketType.PROPRIETARY
    for t in db_stock_transactions:
        if t.asset_id == req.asset_id and t.basket_id == req.basket_id and t.transaction_type == TransactionType.BUY:
            basket_type = t.basket_type
            break
            
    settlement_date = calculate_settlement_date(basket_type, req.trade_date)
    
    # 5. 유보 추인액(Tax Reversal) 계산
    tax_reversal = 0
    latest_snapshot = next((s for s in reversed(db_holdings_snapshot) 
                            if s.asset_id == req.asset_id and s.basket_id == req.basket_id), None)
    if latest_snapshot and latest_snapshot.holding_quantity > 0:
        ratio = req.quantity / latest_snapshot.holding_quantity
        snapshot_reserve = latest_snapshot.eval_amount - latest_snapshot.total_cost
        tax_reversal = snapshot_reserve * ratio
        
        # 추인 원장 기록
        if tax_reversal != 0:
            tax_adj = TaxAdjustment(
                id=str(uuid.uuid4()),
                asset_id=req.asset_id,
                basket_id=req.basket_id,
                fiscal_year=req.trade_date.year,
                evaluation_schedule_id="SELL_EVENT",
                avg_cost=avg_cost,
                book_value=0,
                tax_value=0,
                book_tax_diff=-tax_reversal, # 반대 부호로 기록
                adjustment_type=AdjustmentType.REVERSAL,
                realized_gain=realized_gain
            )
            db_tax_adjustments.append(tax_adj)
    
    tx = StockTransaction(
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
    db_stock_transactions.append(tx)
    return tx

@router.post("/evaluate")
def evaluate_stocks(req: EvaluateRequest):
    # STEP 1: 스케줄러 (자동) -> 본 데모에서는 API 요청 시 스케줄 즉시 생성
    schedule = EvaluationSchedule(
        id=str(uuid.uuid4()),
        schedule_type=req.schedule_type,
        eval_base_date=req.eval_base_date,
        asset_scope=AssetScope.ALL,
        status=ScheduleStatus.CONFIRMED, # 모달 확정 로직이므로 즉시 CONFIRMED
        auto_triggered=False,
        confirmed_by="admin",
        confirmed_at=datetime.now(),
        created_at=datetime.now()
    )
    db_evaluation_schedules.append(schedule)
    
    # 평가 대상 식별 및 세무조정
    results = []
    for price_input in req.prices:
        # STEP 2: 가격 원장 기록
        eval_price = EvaluationPrice(
            id=str(uuid.uuid4()),
            asset_id=price_input.asset_id,
            basket_id=price_input.basket_id,
            eval_date=req.eval_base_date,
            price=price_input.price,
            price_source=PriceSource.MANUAL,
            evaluation_schedule_id=schedule.id,
            input_at=datetime.now()
        )
        db_evaluation_prices.append(eval_price)
        
        # 특정 바스켓에 대해서만 평가 진행
        qty = get_holding_quantity(db_stock_transactions, price_input.asset_id, price_input.basket_id, req.eval_base_date)
        if qty <= 0:
            continue
            
        avg_cost = calc_avg_cost(db_stock_transactions, price_input.asset_id, price_input.basket_id, req.eval_base_date)
        total_cost = avg_cost * qty
        eval_amount = price_input.price * qty
        
        snapshot = HoldingsSnapshot(
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
        db_holdings_snapshot.append(snapshot)
        
        # STEP 3-4: Tax Adjustment (book_value = eval_amount, tax_value = total_cost)
        book_tax_diff = eval_amount - total_cost
        tax_adj = TaxAdjustment(
            id=str(uuid.uuid4()),
            asset_id=price_input.asset_id,
            basket_id=price_input.basket_id,
            fiscal_year=req.eval_base_date.year,
            evaluation_schedule_id=schedule.id,
            avg_cost=avg_cost,
            book_value=eval_amount,
            tax_value=total_cost,
            book_tax_diff=book_tax_diff,
            adjustment_type=AdjustmentType.RESERVE if book_tax_diff > 0 else AdjustmentType.REVERSAL # 예시 판단
        )
        db_tax_adjustments.append(tax_adj)
        results.append(tax_adj)
            
    return {"message": "평가 및 세무조정 완료", "schedule_id": schedule.id, "adjustments_count": len(results)}

@router.get("/dashboard")
def get_dashboard_data():
    """
    현재 보유 잔고(총평균단가 반영) 및 전체 트랜잭션 반환
    """
    today = datetime.now().date()
    
    # 고유 asset_id + basket_id 조합 수집
    asset_basket_keys: Dict[str, Dict[str, Any]] = {}
    for tx in db_stock_transactions:
        if tx.transaction_type not in (TransactionType.BUY, TransactionType.SELL):
            continue
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
        qty = get_holding_quantity(db_stock_transactions, info["asset_id"], info["basket_id"], today)
        if qty <= 0:
            continue
            
        avg_cost = calc_avg_cost(db_stock_transactions, info["asset_id"], info["basket_id"], today)
        
        # 최신 평가 내역 찾기 (가장 최근 스냅샷)
        latest_snapshot = next((s for s in reversed(db_holdings_snapshot) 
                             if s.asset_id == info["asset_id"] and s.basket_id == info["basket_id"]), None)
        
        tax_reserve = 0
        eval_price = 0
        eval_amount = 0
        if latest_snapshot:
            # 잔존수량 비율만큼 유보액 적용 (단순화)
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
    settled_cash = 0
    receivable_cash = 0
    today = datetime.now().date()
    
    for tx in db_stock_transactions:
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
                
    # 내역 조회를 위한 정렬된 리스트 반환 (가장 최근이 위로)
    sorted_txs = sorted(db_stock_transactions, key=lambda x: x.created_at, reverse=True)
            
    return {
        "portfolio": portfolio,
        "transactions": sorted_txs,
        "cash_flow": {
            "settled_cash": settled_cash,
            "receivable_cash": receivable_cash
        }
    }
