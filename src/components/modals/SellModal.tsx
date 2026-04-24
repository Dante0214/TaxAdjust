import { useState } from 'react'
import { X } from 'lucide-react'
import type { PortfolioItem } from '../../store/useTaxStore'

interface SellModalProps {
  onClose: () => void
  onSave: (d: any) => Promise<void>
  isLoading: boolean
  portfolio: PortfolioItem[]
}

export default function SellModal({ onClose, onSave, isLoading, portfolio }: SellModalProps) {
  const [selectedAsset, setSelectedAsset] = useState('')
  const [form, setForm] = useState({
    trade_date: new Date().toISOString().split('T')[0],
    quantity: '',
    unit_price: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedAsset) return
    const [asset_id, basket_id] = selectedAsset.split('||')
    await onSave({
      asset_id,
      basket_id,
      ...form,
      quantity: parseFloat(form.quantity),
      unit_price: parseFloat(form.unit_price)
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-rose-50/50">
          <h3 className="font-semibold text-lg text-slate-800">매도 실행 (Sell)</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">매도 자산 (종목 + 바스켓)</label>
            <select required className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 outline-none" value={selectedAsset} onChange={e => setSelectedAsset(e.target.value)}>
              <option value="">선택하세요</option>
              {portfolio.map((p, idx) => (
                <option key={idx} value={`${p.asset_id}||${p.basket_id}`}>
                  {p.asset_id} ({p.basket_id}) - 잔고 {p.quantity}주
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">매매체결일</label>
              <input required type="date" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 outline-none" value={form.trade_date} onChange={e => setForm({...form, trade_date: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">수량</label>
              <input required type="number" step="0.01" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 outline-none" value={form.quantity} onChange={e => setForm({...form, quantity: e.target.value})} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">매도단가(₩)</label>
            <input required type="number" step="0.01" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 outline-none" value={form.unit_price} onChange={e => setForm({...form, unit_price: e.target.value})} />
          </div>
          <p className="text-xs text-slate-500 mt-2">* 백엔드에서 총평균단가를 다시 계산하여 처분손익 및 유보추인을 처리합니다.</p>
          <div className="pt-4 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200">취소</button>
            <button type="submit" disabled={isLoading} className="px-4 py-2 text-sm font-medium text-white bg-rose-600 rounded-lg hover:bg-rose-700 disabled:opacity-50">매도 실행</button>
          </div>
        </form>
      </div>
    </div>
  )
}
