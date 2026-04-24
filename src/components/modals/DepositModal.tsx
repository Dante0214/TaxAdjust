import { useState } from 'react'
import { X } from 'lucide-react'
import type { BasketType } from '../../store/useTaxStore'

interface DepositModalProps {
  onClose: () => void
  onSave: (data: { basket_type: BasketType; basket_id: string; trade_date: string; amount: number }) => Promise<void>
  isLoading: boolean
}

export default function DepositModal({ onClose, onSave, isLoading }: DepositModalProps) {
  const [form, setForm] = useState({
    basket_type: 'PROPRIETARY' as BasketType,
    basket_id: 'CASH_POOL_1',
    trade_date: new Date().toISOString().split('T')[0],
    amount: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await onSave({
      ...form,
      amount: parseFloat(form.amount)
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-emerald-50/50">
          <h3 className="font-semibold text-lg text-slate-800">자본금 입금 (Deposit)</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">바스켓 구분</label>
            <select className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" value={form.basket_type} onChange={e => setForm({...form, basket_type: e.target.value as BasketType})}>
              <option value="PROPRIETARY">고유계좌</option>
              <option value="FUND">펀드</option>
              <option value="SECURITIES">증권사</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">바스켓 ID/코드</label>
            <input required type="text" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" value={form.basket_id} onChange={e => setForm({...form, basket_id: e.target.value})} placeholder="펀드코드 등" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">입금일 (결제일)</label>
            <input required type="date" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" value={form.trade_date} onChange={e => setForm({...form, trade_date: e.target.value})} />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">입금 금액(₩)</label>
            <input required type="number" step="1" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} />
          </div>
          <p className="text-xs text-slate-500 mt-2">* 입금 즉시 가용 현금으로 처리됩니다.</p>
          <div className="pt-4 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200">취소</button>
            <button type="submit" disabled={isLoading} className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50">입금 처리</button>
          </div>
        </form>
      </div>
    </div>
  )
}
