import { useState, useEffect } from "react";
import { useTaxStore } from "../store/useTaxStore";

// Dashboard 하위 컴포넌트
import Sidebar from "../components/dashboard/Sidebar";
import SummaryCards from "../components/dashboard/SummaryCards";
import PortfolioTable from "../components/dashboard/PortfolioTable";
import TransactionTable from "../components/dashboard/TransactionTable";

// 모달/슬라이드오버
import DepositModal from "../components/modals/DepositModal";
import BuyModal from "../components/modals/BuyModal";
import SellModal from "../components/modals/SellModal";
import EvalSlideOver from "../components/modals/EvalSlideOver";

export default function Dashboard() {
  const {
    portfolio,
    transactions,
    cash_flow,
    fetchDashboard,
    buyStock,
    sellStock,
    evaluateStocks,
    depositCash,
    isLoading,
  } = useTaxStore();

  const [isBuyOpen, setIsBuyOpen] = useState(false);
  const [isSellOpen, setIsSellOpen] = useState(false);
  const [isEvalOpen, setIsEvalOpen] = useState(false);
  const [isDepositOpen, setIsDepositOpen] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const totalEvalAmount = portfolio.reduce(
    (acc, curr) => acc + (curr.eval_amount || 0),
    0,
  );
  const totalTaxReserve = portfolio.reduce(
    (acc, curr) => acc + curr.tax_reserve,
    0,
  );

  return (
    <div className="flex h-screen w-full bg-[#f8fafc] text-slate-900 font-sans overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        onDepositOpen={() => setIsDepositOpen(true)}
        onBuyOpen={() => setIsBuyOpen(true)}
        onEvalOpen={() => setIsEvalOpen(true)}
        onSellOpen={() => setIsSellOpen(true)}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto relative">
        <div className="absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] opacity-30 pointer-events-none z-0"></div>
        <div className="relative z-10 p-8 max-w-7xl mx-auto w-full space-y-6">
          <header className="mb-8">
            <h2 className="text-2xl font-bold text-slate-800">
              세무조정 대시보드
            </h2>
            <p className="text-slate-500 mt-1">
              총평균법에 따른 종목/바스켓별 취득단가 및 유보잔액을 확인합니다.
            </p>
          </header>

          <SummaryCards
            cashFlow={cash_flow}
            totalEvalAmount={totalEvalAmount}
            totalTaxReserve={totalTaxReserve}
          />

          <PortfolioTable portfolio={portfolio} />
          <TransactionTable transactions={transactions} />
        </div>
      </main>

      {/* Modals */}
      {isDepositOpen && (
        <DepositModal
          onClose={() => setIsDepositOpen(false)}
          onSave={depositCash}
          isLoading={isLoading}
        />
      )}
      {isBuyOpen && (
        <BuyModal
          onClose={() => setIsBuyOpen(false)}
          onSave={buyStock}
          isLoading={isLoading}
        />
      )}
      {isSellOpen && (
        <SellModal
          onClose={() => setIsSellOpen(false)}
          onSave={sellStock}
          isLoading={isLoading}
          portfolio={portfolio}
        />
      )}
      {isEvalOpen && (
        <EvalSlideOver
          onClose={() => setIsEvalOpen(false)}
          onSave={evaluateStocks}
          isLoading={isLoading}
          portfolio={portfolio}
        />
      )}
    </div>
  );
}
