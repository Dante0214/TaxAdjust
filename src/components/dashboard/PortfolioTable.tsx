import type { PortfolioItem } from '../../store/useTaxStore'

interface PortfolioTableProps {
  portfolio: PortfolioItem[]
}

export default function PortfolioTable({ portfolio }: PortfolioTableProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
        <h3 className="text-lg font-semibold text-slate-800">보유 잔고 스냅샷</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <th className="px-6 py-4 font-semibold">종목(Asset ID)</th>
              <th className="px-6 py-4 font-semibold">바스켓 구분</th>
              <th className="px-6 py-4 font-semibold text-right">보유수량</th>
              <th className="px-6 py-4 font-semibold text-right">총평균 취득단가</th>
              <th className="px-6 py-4 font-semibold text-right">현재 평가금액</th>
              <th className="px-6 py-4 font-semibold text-right text-indigo-600">유보잔액</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {portfolio.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">데이터가 없습니다.</td></tr>
            ) : (
              portfolio.map((p, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50">
                  <td className="px-6 py-4 font-medium text-slate-800">{p.asset_id}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-slate-100 text-slate-600">
                      {p.basket_type} - {p.basket_id || '고유계정'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">{p.quantity.toLocaleString()}</td>
                  <td className="px-6 py-4 text-right">₩{p.avg_cost.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                  <td className="px-6 py-4 text-right">
                    {p.eval_price ? (
                      <>
                        <div>₩{(p.eval_amount || 0).toLocaleString(undefined, {maximumFractionDigits: 0})}</div>
                        <div className="text-xs text-slate-400">(@₩{p.eval_price.toLocaleString()})</div>
                      </>
                    ) : (
                      <span className="text-slate-400 text-xs">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right font-semibold text-indigo-600">₩{p.tax_reserve.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
