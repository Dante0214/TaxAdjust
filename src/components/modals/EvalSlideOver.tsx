import { useState } from 'react'
import { X } from 'lucide-react'
import type { PortfolioItem } from '../../store/useTaxStore'

interface EvalSlideOverProps {
  onClose: () => void
  onSave: (d: any) => Promise<void>
  isLoading: boolean
  portfolio: PortfolioItem[]
}

export default function EvalSlideOver({ onClose, onSave, isLoading, portfolio }: EvalSlideOverProps) {
  const [evalDate, setEvalDate] = useState(new Date().toISOString().split('T')[0])
  const [scheduleType, setScheduleType] = useState('YEARLY')
  const [prices, setPrices] = useState<{[key: string]: string}>({})

  const handleSubmit = async () => {
    const pricesList = Object.entries(prices).filter(([_, v]) => v !== '').map(([k, v]) => {
      const [asset_id, basket_id] = k.split('||')
      return { asset_id, basket_id, price: parseFloat(v) }
    })
    
    if (pricesList.length === 0) return alert('평가 단가를 하나 이상 입력하세요.')

    await onSave({
      eval_base_date: evalDate,
      schedule_type: scheduleType,
      prices: pricesList
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white shadow-2xl w-full max-w-md h-full flex flex-col slide-in-from-right animate-in duration-300">
        <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-amber-50">
          <div>
            <h3 className="font-semibold text-lg text-slate-800">평가 실행 (다종목)</h3>
            <p className="text-xs text-amber-700 mt-1">스케줄 확정 및 세무조정 원장 생성</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">기준일</label>
              <input type="date" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none" value={evalDate} onChange={e => setEvalDate(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">평가 유형</label>
              <select className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none" value={scheduleType} onChange={e => setScheduleType(e.target.value)}>
                <option value="YEARLY">연간 (Yearly)</option>
                <option value="QUARTERLY">분기 (Quarterly)</option>
                <option value="MONTHLY">월간 (Monthly)</option>
              </select>
            </div>
          </div>

          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div className="bg-slate-50 px-4 py-2 text-xs font-semibold text-slate-500 uppercase border-b border-slate-200 flex justify-between">
              <span>바스켓 및 종목명</span>
              <span>평가가격 입력 (₩)</span>
            </div>
            <div className="divide-y divide-slate-100">
              {portfolio.length === 0 ? (
                <div className="p-4 text-center text-sm text-slate-400">보유 종목이 없습니다.</div>
              ) : (
                portfolio.map(p => {
                  const key = `${p.asset_id}||${p.basket_id}`
                  return (
                    <div key={key} className="flex justify-between items-center p-3">
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-slate-700">{p.asset_id}</span>
                        <span className="text-xs text-slate-400">{p.basket_type} - {p.basket_id || '고유계정'}</span>
                      </div>
                      <input 
                        type="number" 
                        className="w-32 px-3 py-1.5 text-sm text-right border border-slate-300 rounded focus:ring-2 focus:ring-amber-500 outline-none" 
                        placeholder="0.00"
                        value={prices[key] || ''}
                        onChange={e => setPrices({...prices, [key]: e.target.value})}
                      />
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>
        
        <div className="p-4 border-t border-slate-100 flex justify-end gap-2 bg-slate-50">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-100">취소</button>
          <button onClick={handleSubmit} disabled={isLoading || portfolio.length === 0} className="px-4 py-2 text-sm font-medium text-white bg-amber-500 rounded-lg hover:bg-amber-600 disabled:opacity-50">확정 및 계산 실행</button>
        </div>
      </div>
    </div>
  )
}
