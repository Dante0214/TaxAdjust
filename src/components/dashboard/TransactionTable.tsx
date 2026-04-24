import type { StockTransaction } from '../../store/useTaxStore'

interface TransactionTableProps {
  transactions: StockTransaction[]
}

export default function TransactionTable({ transactions }: TransactionTableProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
        <h3 className="text-lg font-semibold text-slate-800">최근 거래 및 세무 추인 내역</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <th className="px-6 py-4 font-semibold">구분</th>
              <th className="px-6 py-4 font-semibold">체결일 / 결제일</th>
              <th className="px-6 py-4 font-semibold">종목(바스켓)</th>
              <th className="px-6 py-4 font-semibold text-right">수량/단가</th>
              <th className="px-6 py-4 font-semibold text-right">거래대금</th>
              <th className="px-6 py-4 font-semibold text-right text-rose-600">유보 추인액(Reversal)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {transactions.slice(0, 10).map((tx) => (
              <tr key={tx.id} className="hover:bg-slate-50/50">
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold ${
                    tx.transaction_type === 'BUY' ? 'bg-indigo-100 text-indigo-700' :
                    tx.transaction_type === 'SELL' ? 'bg-rose-100 text-rose-700' :
                    tx.transaction_type === 'DEPOSIT' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {tx.transaction_type}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-slate-800">{tx.trade_date}</div>
                  <div className="text-xs text-slate-500">{tx.settlement_date}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-slate-800">{tx.asset_id}</div>
                  <div className="text-xs text-slate-500">{tx.basket_id}</div>
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="text-sm font-medium text-slate-800">{tx.quantity.toLocaleString()}주</div>
                  <div className="text-xs text-slate-500">@₩{tx.unit_price.toLocaleString()}</div>
                </td>
                <td className="px-6 py-4 text-right font-medium text-slate-800">
                  ₩{tx.total_amount.toLocaleString(undefined, {maximumFractionDigits: 0})}
                </td>
                <td className="px-6 py-4 text-right font-semibold text-rose-600">
                  {tx.tax_reversal ? `₩${tx.tax_reversal.toLocaleString(undefined, {maximumFractionDigits: 0})}` : '-'}
                </td>
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">거래 내역이 없습니다.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
