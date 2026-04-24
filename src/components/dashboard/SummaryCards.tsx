import { Wallet, BarChart3 } from 'lucide-react'
import type { CashFlow } from '../../store/useTaxStore'

interface SummaryCardsProps {
  cashFlow: CashFlow
  totalEvalAmount: number
  totalTaxReserve: number
}

export default function SummaryCards({ cashFlow, totalEvalAmount, totalTaxReserve }: SummaryCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-emerald-200 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-10">
          <Wallet className="w-16 h-16 text-emerald-600" />
        </div>
        <p className="text-sm font-medium text-emerald-600 mb-1">결제 완료 현금 (가용)</p>
        <h3 className="text-3xl font-bold text-emerald-700">₩{cashFlow?.settled_cash.toLocaleString(undefined, {maximumFractionDigits: 0}) || 0}</h3>
      </div>
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <p className="text-sm font-medium text-slate-500 mb-1">결제 대기 (미수/미지급금)</p>
        <h3 className={`text-3xl font-bold ${cashFlow?.receivable_cash > 0 ? 'text-blue-600' : cashFlow?.receivable_cash < 0 ? 'text-rose-600' : 'text-slate-800'}`}>
          ₩{cashFlow?.receivable_cash.toLocaleString(undefined, {maximumFractionDigits: 0}) || 0}
        </h3>
      </div>
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <p className="text-sm font-medium text-slate-500 mb-1">총 평가금액</p>
        <h3 className="text-3xl font-bold text-slate-800">₩{totalEvalAmount.toLocaleString(undefined, {maximumFractionDigits: 0})}</h3>
      </div>
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-indigo-200 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-10">
          <BarChart3 className="w-16 h-16 text-indigo-600" />
        </div>
        <p className="text-sm font-medium text-indigo-600 mb-1">총 세무 유보잔액</p>
        <h3 className="text-3xl font-bold text-indigo-700">₩{totalTaxReserve.toLocaleString(undefined, {maximumFractionDigits: 0})}</h3>
      </div>
    </div>
  )
}
