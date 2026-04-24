import { useState } from 'react'
import { X } from 'lucide-react'
import type { BasketType } from '../../store/useTaxStore'

interface BuyModalProps {
  onClose: () => void
  onSave: (d: any) => Promise<void>
  isLoading: boolean
}

export default function BuyModal({ onClose, onSave, isLoading }: BuyModalProps) {
  const [form, setForm] = useState({
    asset_id: '',
    basket_type: 'PROPRIETARY' as BasketType,
    basket_id: '',
    trade_date: new Date().toISOString().split('T')[0],
    quantity: '',
    unit_price: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await onSave({
      ...form,
      quantity: parseFloat(form.quantity),
      unit_price: parseFloat(form.unit_price)
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-indigo-50/50">
          <h3 className="font-semibold text-lg text-slate-800">매수 등록 (Buy)</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">종목 코드/명</label>
            <input required type="text" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={form.asset_id} onChange={e => setForm({...form, asset_id: e.target.value})} placeholder="KR7005930003" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">바스켓 구분</label>
              <select className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={form.basket_type} onChange={e => setForm({...form, basket_type: e.target.value as BasketType})}>
                <option value="PROPRIETARY">고유계좌</option>
                <option value="FUND">펀드</option>
                <option value="SECURITIES">증권사</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">바스켓 ID/코드</label>
              <input required type="text" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={form.basket_id} onChange={e => setForm({...form, basket_id: e.target.value})} placeholder="펀드코드 등" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">매매체결일</label>
              <input required type="date" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={form.trade_date} onChange={e => setForm({...form, trade_date: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">수량</label>
              <input required type="number" step="0.01" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={form.quantity} onChange={e => setForm({...form, quantity: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">단가(₩)</label>
              <input required type="number" step="0.01" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" value={form.unit_price} onChange={e => setForm({...form, unit_price: e.target.value})} />
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-2">* 결제일(settlement_date)은 바스켓 구분에 따라 자동 산출됩니다.</p>
          <div className="pt-4 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200">취소</button>
            <button type="submit" disabled={isLoading} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50">매수 저장</button>
          </div>
        </form>
      </div>
    </div>
  )
}
