## 문서 목적

이 문서는 `TaxAdjust` 웹앱 프로젝트의 **기획서(제품/업무/화면/정책)** 와 **개발문서(아키텍처/실행/환경/API/DB)** 를 한 곳에 정리합니다.

> 기준 구현: `backend/app`(FastAPI + SQLModel + SQLite) 및 `src`(React + Vite) 코드 베이스.

---

## 1. 프로젝트 개요 (Project Overview)

**TaxAdjust**는 상장주식 거래를 “바스켓(고유계정/펀드/증권사)” 단위로 관리하면서,
매수 → 평가 → 매도 라이프사이클 전 과정에서 다음을 자동화/가시화하는 세무조정 관리 웹앱입니다.

- **총평균단가(이동잔존금액법)** 기반 취득단가 산출
- **평가손익 기반 세무 유보(RESERVE) / 환입(REVERSAL)** 원장 자동 생성
- **결제일(T+2/T+3, 한국 영업일 기준)** 산출 및 **정산(가용/결제대기) 현금흐름** 집계

### 1.1. 대상 사용자

- 회계/세무 담당자(법인 고유계정, 증권사 계정, 펀드 계정 등)
- 운용/관리 담당자(포트폴리오 요약 및 거래 이력 조회)

### 1.2. 용어 정의

- **자산(asset)**: 종목코드(`asset_id`)로 식별되는 주식(또는 현금 `CASH`)
- **바스켓(basket)**: 계정/펀드/증권사 등의 관리 단위(`basket_id`, `basket_type`)
- **유보(RESERVE)**: 평가금액이 취득원가보다 큰 경우 발생시키는 조정
- **환입(REVERSAL)**: 평가금액이 취득원가보다 작은 경우 또는 매도에 의해 유보를 일부/전부 되돌리는 조정
- **정산(결제)**: 체결일과 결제일이 다를 수 있으며, 결제일까지는 “결제대기(receivable)”로 분리 집계

---

## 2. 제품 기획서 (PRD)

### 2.1. 핵심 목표 (Goals)

- **정확성**: 바스켓/종목별 보유수량, 총평균단가, 평가/세무 차이의 일관된 계산
- **추적성**: 평가 스케줄 단위로 가격/스냅샷/세무조정이 연결되어 감사 추적이 가능
- **업무 효율**: 다종목 평가 일괄 입력 및 자동 원장 생성으로 결산 업무 단순화

### 2.2. 주요 기능 (Scope)

#### 2.2.1. 자본금 입금(Deposit)

- 바스켓별 현금 입금 거래 생성
- 입금은 즉시 결제 완료(체결일=결제일)

#### 2.2.2. 매수(Buy)

- 입력: 종목, 바스켓, 수량, 단가, 거래일
- 결제일 자동 산출(한국 영업일 기준)
  - `PROPRIETARY`, `SECURITIES`: **T+2**
  - `FUND`: **T+3**

#### 2.2.3. 평가(Evaluate)

- 입력: 평가 기준일, 스케줄 유형, (종목+바스켓)별 평가 단가 목록
- 결과(자동):
  - **평가 스케줄 생성**
  - **평가 단가 원장 생성**
  - 보유 종목에 대해 **보유 스냅샷 생성**
  - 평가금액(book_value)과 취득원가(tax_value) 차이로 **세무조정(RESERVE/REVERSAL) 생성**

#### 2.2.4. 매도(Sell)

- 보유수량 초과 매도 차단
- 총평균단가 산출 후 실현손익 계산
- 최신 스냅샷(평가) 기반으로 매도 수량 비율만큼 유보를 **부분 환입(tax_reversal)** 처리

#### 2.2.5. 대시보드(Dashboard)

- 포트폴리오: 보유 수량/총평균단가/최근 평가단가/평가금액/유보잔액 요약
- 현금흐름: 가용현금(settled), 결제대기(receivable) 분리 집계
- 최근 거래내역: 매수/매도/입금 거래를 최신순 제공

### 2.3. 화면 구성(권장 IA)

현재 구현은 대시보드 중심(모달/슬라이드오버) 구조이며, 문서상 권장 화면은 아래와 같습니다.

- **Dashboard**
  - 요약 카드: 가용현금 / 결제대기 / 평가금액 합계 / 유보잔액 합계
  - 포트폴리오 테이블: 바스켓·종목 단위 잔고/평가
  - 거래내역 테이블: BUY/SELL/DEPOSIT 내역
  - 액션: Deposit, Buy, Sell, Evaluate(다종목)
- **평가/결산 이력(추가 권장)**
  - 평가 스케줄 목록/상세(가격/스냅샷/세무조정 연결 조회)

### 2.4. 업무 정책/규칙 (Business Rules)

- **보유수량 산출**: \( \sum BUY - \sum SELL \)
- **총평균단가**: 이동잔존금액법(거래를 시간순 재현하여 매도 시점 평균으로 잔존금액 차감)
- **세무조정 분류**: `book_tax_diff = book_value - tax_value`
  - `book_tax_diff > 0` → `RESERVE`
  - `book_tax_diff <= 0` → `REVERSAL`
- **결제일 산출**: 주말/한국공휴일 제외 영업일 기준(`holidays` 라이브러리)
- **현금흐름 집계**
  - 결제일이 오늘 이하이면 `settled_cash`에 반영
  - 결제일이 미래이면 `receivable_cash`에 반영(부호 포함)

### 2.5. 에러/검증 정책

- **매도 수량 검증 실패**: HTTP 400, 메시지에 `InsufficientHoldingError` 포함

---

## 3. 개발 문서 (Engineering)

### 3.1. 기술 스택

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Zustand, Axios
- **Backend**: Python, FastAPI, SQLModel(SQLAlchemy)
- **DB**: SQLite 파일(`tax_adjust.db`)

### 3.2. 프로젝트 구조(백엔드)

```
├── src/                          # 프론트엔드 (React + TypeScript)
│   ├── pages/
│   │   └── Dashboard.tsx         # 메인 대시보드 페이지
│   ├── components/
│   │   ├── dashboard/            # 대시보드 하위 컴포넌트
│   │   │   ├── Sidebar.tsx       #   사이드바 (Quick Actions)
│   │   │   ├── SummaryCards.tsx   #   요약 카드 4종
│   │   │   ├── PortfolioTable.tsx #   보유잔고 테이블
│   │   │   └── TransactionTable.tsx # 거래내역 테이블
│   │   └── modals/               # 모달/슬라이드오버 컴포넌트
│   │       ├── DepositModal.tsx   #   자본금 입금
│   │       ├── BuyModal.tsx       #   매수 등록
│   │       ├── SellModal.tsx      #   매도 실행
│   │       └── EvalSlideOver.tsx  #   다종목 평가
│   └── store/
│       └── useTaxStore.ts        # Zustand 상태관리 (API 호출 포함)
│
├── backend/                      # 백엔드 (FastAPI + SQLite)
│   └── app/
│       ├── main.py               # FastAPI 앱 엔트리포인트 (DB 자동 초기화)
│       ├── api/
│       │   └── endpoints.py      # API 엔드포인트 (매수/매도/평가/대시보드)
│       ├── models/
│       │   ├── tax.py            # Pydantic Enum/Request 모델
│       │   └── db_models.py      # SQLModel DB 테이블 모델 (5개 테이블)
│       └── core/
│           ├── database.py       # SQLite 엔진 + 세션 관리
│           └── calculations.py   # 핵심 계산 로직 (총평균단가, 영업일)
│
├── package.json                  # 프론트엔드 의존성
└── index.html                    # Vite 엔트리
```

### 3.3. 실행 방법(로컬)

- 프론트엔드 설치 및 실행

```bash
npm install
npm run dev
```

- 백엔드 설치 및 실행

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3.4. API 명세(현재 구현)

Base path: `/api/tax`

#### 3.4.1. `POST /deposit`

- 목적: 바스켓별 자본금 입금(현금 거래 생성)
- Request(`DepositRequest`)
  - `basket_type`: `PROPRIETARY | FUND | SECURITIES`
  - `basket_id`: string
  - `trade_date`: date(YYYY-MM-DD)
  - `amount`: number

#### 3.4.2. `POST /buy`

- 목적: 매수 거래 생성 + 결제일 자동 산출
- Request(`BuyRequest`)
  - `asset_id`, `basket_id`, `basket_type`, `trade_date`, `quantity`, `unit_price`

#### 3.4.3. `POST /sell`

- 목적: 매도 거래 생성 + 실현손익/유보환입 계산
- Request(`SellRequest`)
  - `asset_id`, `basket_id`, `trade_date`, `quantity`, `unit_price`

#### 3.4.4. `POST /evaluate`

- 목적: 평가 스케줄 생성 + 가격/스냅샷/세무조정 생성
- Request(`EvaluateRequest`)
  - `eval_base_date`: date
  - `schedule_type`: `YEARLY | QUARTERLY | MONTHLY | ADHOC`
  - `prices`: `{ asset_id, basket_id, price }[]`

#### 3.4.5. `GET /dashboard`

- 목적: 포트폴리오/거래내역/현금흐름 집계 반환
- Response(요약)
  - `portfolio`: (asset_id, basket_id, basket_type, quantity, avg_cost, tax_reserve, eval_price, eval_amount)[]
  - `transactions`: `stock_transactions` 레코드 최신순
  - `cash_flow`: `{ settled_cash, receivable_cash }`

---

## 4. 데이터베이스 테이블 설계 (Database Schema Design)

요청 형식에 맞춰 **컬럼 / 타입 / 제약 / 설명**으로 정리합니다.  
실제 정의는 `backend/app/models/db_models.py`의 SQLModel 모델을 기준으로 합니다.

> 타입 표기 규칙: SQLite에 매핑되는 대표 타입으로 표기하고, Enum은 `TEXT(Enum)`로 표기합니다.

### 4.1. `stock_transactions` (거래 원장)

주식 매수/매도 및 입금(현금) 거래 내역을 기록합니다.

| 컬럼명 | 타입 | 제약 사항 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `TEXT` | PK | 거래 고유 ID (UUID 문자열) |
| `asset_id` | `TEXT` | INDEX, NOT NULL | 자산(종목) 코드. 현금 입금은 `"CASH"` 사용 |
| `basket_id` | `TEXT` | INDEX, NOT NULL | 바스켓 식별자 |
| `basket_type` | `TEXT(Enum)` | NOT NULL | `BasketType`: `PROPRIETARY`, `FUND`, `SECURITIES` |
| `transaction_type` | `TEXT(Enum)` | NOT NULL | `TransactionType`: `BUY`, `SELL`, `EVALUATE`, `DEPOSIT` |
| `trade_date` | `DATE` | NOT NULL | 체결일 |
| `settlement_date` | `DATE` | NOT NULL | 결제일 (영업일 기준) |
| `quantity` | `REAL` | NOT NULL | 수량 (입금은 1로 고정) |
| `unit_price` | `REAL` | NOT NULL | 단가 (입금은 `amount`) |
| `total_amount` | `REAL` | NOT NULL | 총금액 (`quantity * unit_price`, 입금은 `amount`) |
| `avg_cost_snapshot` | `REAL` | NULL | 거래 시점 총평균단가 (매도 기록용) |
| `realized_gain` | `REAL` | NULL | 실현손익 (매도 시) |
| `tax_reversal` | `REAL` | NULL | 유보 환입액 (매도 시) |
| `fiscal_year` | `INTEGER` | NOT NULL | 회계연도 (거래일 연도) |
| `created_by` | `TEXT` | NOT NULL, DEFAULT `"system"` | 생성 주체 |
| `created_at` | `DATETIME` | NOT NULL | 생성일시 |

### 4.2. `evaluation_prices` (평가 단가 원장)

평가 스케줄에 의해 입력된 종목별 평가 단가를 저장합니다.

| 컬럼                     | 타입         | 제약                         | 설명                                               |
| :--- | :---| :--- | :----
| `id`                     | `TEXT`       | PK                           | 평가 단가 고유 ID(UUID 문자열)                     |
| `asset_id`               | `TEXT`       | INDEX, NOT NULL              | 종목 코드                                          |
| `basket_id`              | `TEXT`       | NULL                         | 바스켓 식별자(현재 평가 입력은 바스켓 단위로 사용) |
| `eval_date`              | `DATE`       | NOT NULL                     | 평가 기준일                                        |
| `price`                  | `REAL`       | NOT NULL                     | 평가 단가                                          |
| `price_source`           | `TEXT(Enum)` | NOT NULL                     | `PriceSource`: `MANUA, API_KRX ,API_BLOOMBERG` |
| `evaluation_schedule_id` | `TEXT`       | NULL                         | 연결된 평가 스케줄 ID                              |
| `input_by`               | `TEXT`       | NOT NULL, DEFAULT `"system"` | 입력 주체                                          |
| `input_at`               | `DATETIME`   | NOT NULL                     | 입력일시                                           |

### 4.3. `evaluation_schedules` (평가 스케줄)

평가 실행 단위를 관리합니다(확정/잠금 등 상태 포함).

| 컬럼             | 타입          | 제약     | 설명                               |
| :--------------- | :----------- | :------- | :--------------------------------- | 
| `id`             | `TEXT`       | PK       | 스케줄 ID(UUID 문자열)             |
| `schedule_type`  | `TEXT(Enum)` | NOT NULL | `ScheduleType`: `YEARLY, QUARTERLY, MONTHLY, ADHOC`  |
| `eval_base_date` | `DATE`       | NOT NULL | 평가 기준일                        |
| `asset_scope`    | `TEXT(Enum)` | NOT NULL | `AssetScope`: `ALL, BASKET_SPECIFIC` |
| `basket_id`      | `TEXT`       | NULL     | `BASKET_SPECIFIC`일 때 대상 바스켓 |
| `status`         | `TEXT(Enum)` | NOT NULL | `ScheduleStatus`: `PENDING, IN_REVIEW, CONFIRMED, LOCKED` |
| `auto_triggered` | `BOOLEAN`    | NOT NULL | 자동 생성 여부                     |
| `confirmed_by`   | `TEXT`       | NULL     | 확정자                             |
| `confirmed_at`   | `DATETIME`   | NULL     | 확정일시                           |
| `locked_at`      | `DATETIME`   | NULL     | 잠금일시                           |
| `created_at`     | `DATETIME`   | NOT NULL | 생성일시                           |

### 4.4. `tax_adjustments` (세무조정 원장)

평가 시점의 장부가액(book)과 세무가액(tax) 차이를 기록합니다.
 
| 컬럼        				    | 타입         | 제약                   | 설명                                   |
| :----------------------- | :----------- | :-------------- | :------------------------------------------------ |
| `id`                     | `TEXT`       | PK              | 세무조정 ID(UUID 문자열)                          |
| `asset_id`               | `TEXT`       | INDEX, NOT NULL | 종목 코드                                         |
| `basket_id`              | `TEXT`       | INDEX, NOT NULL | 바스켓 식별자                                     |
| `fiscal_year`            | `INTEGER`    | NOT NULL        | 회계연도                                          |
| `evaluation_schedule_id` | `TEXT`       | NOT NULL        | 평가 스케줄 ID(매도 이벤트는 `"SELL_EVENT"` 사용) |
| `avg_cost`               | `REAL`       | NOT NULL        | 총평균단가                                        |
| `book_value`             | `REAL`       | NOT NULL        | 장부가액(평가금액)                                |
| `tax_value`              | `REAL`       | NOT NULL        | 세무가액(취득원가)                                |
| `book_tax_diff`          | `REAL`       | NOT NULL        | `book_value - tax_value`                          |
| `adjustment_type`        | `TEXT(Enum)` | NOT NULL        | `AdjustmentType`: `RESERVE, REVERSAL` |
| `realized_gain`          | `REAL`       | NULL            | 실현손익(매도 환입 기록 시 사용)                  |

### 4.5. `holdings_snapshot` (보유 스냅샷)

평가 시점의 보유수량/총평균단가/평가금액/미실현손익을 스냅샷으로 보존합니다.

| 컬럼                     | 타입   | 제약            | 설명                                   |
| :----------------------- | :----- | :-------------- | :------------------------------------- |
| `id`                     | `TEXT` | PK              | 스냅샷 ID(UUID 문자열)                 |
| `asset_id`               | `TEXT` | INDEX, NOT NULL | 종목 코드                              |
| `basket_id`              | `TEXT` | INDEX, NOT NULL | 바스켓 식별자                          |
| `snapshot_date`          | `DATE` | NOT NULL        | 스냅샷 기준일(평가 기준일)             |
| `holding_quantity`       | `REAL` | NOT NULL        | 보유 수량                              |
| `avg_cost`               | `REAL` | NOT NULL        | 총평균단가                             |
| `total_cost`             | `REAL` | NOT NULL        | 총원가(`holding_quantity * avg_cost`)  |
| `eval_price`             | `REAL` | NULL            | 평가 단가                              |
| `eval_amount`            | `REAL` | NULL            | 평가 금액                              |
| `unrealized_gain`        | `REAL` | NULL            | 미실현손익(`eval_amount - total_cost`) |
| `evaluation_schedule_id` | `TEXT` | NOT NULL        | 생성한 평가 스케줄 ID                  |

---
