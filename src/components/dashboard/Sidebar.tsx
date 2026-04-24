import { Building2, TrendingUp, HandCoins, BarChart3, Wallet } from 'lucide-react'

interface SidebarProps {
  onDepositOpen: () => void
  onBuyOpen: () => void
  onEvalOpen: () => void
  onSellOpen: () => void
}

export default function Sidebar({ onDepositOpen, onBuyOpen, onEvalOpen, onSellOpen }: SidebarProps) {
  return (
    <aside className="w-64 flex flex-col bg-white border-r border-slate-200 shadow-sm shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-slate-100">
        <Building2 className="w-6 h-6 text-indigo-600 mr-2" />
        <h1 className="text-lg font-bold tracking-tight text-slate-800">Tax<span className="text-indigo-600">Adjust</span></h1>
      </div>
      
      <div className="flex-1 overflow-y-auto py-6 px-4 space-y-2">
        <div className="px-2 pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
          빠른 실행 (Quick Actions)
        </div>
        <button onClick={onDepositOpen} className="w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 transition-colors">
          <Wallet className="w-5 h-5 mr-3 text-emerald-500" />
          자본금 입금 (Deposit)
        </button>
        <button onClick={onBuyOpen} className="w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 transition-colors">
          <TrendingUp className="w-5 h-5 mr-3 text-indigo-500" />
          매수 등록 (Buy)
        </button>
        <button onClick={onEvalOpen} className="w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-700 hover:bg-amber-50 hover:text-amber-700 transition-colors">
          <BarChart3 className="w-5 h-5 mr-3 text-amber-500" />
          다종목 평가 (Evaluate)
        </button>
        <button onClick={onSellOpen} className="w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-700 hover:bg-rose-50 hover:text-rose-700 transition-colors">
          <HandCoins className="w-5 h-5 mr-3 text-rose-500" />
          매도 실행 (Sell)
        </button>
      </div>
    </aside>
  )
}
