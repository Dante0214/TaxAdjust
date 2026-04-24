import { create } from "zustand";
import axios from "axios";

export type BasketType = "PROPRIETARY" | "FUND" | "SECURITIES";

export interface PortfolioItem {
  asset_id: string;
  basket_id: string;
  basket_type: BasketType;
  quantity: number;
  avg_cost: number;
  tax_reserve: number;
  eval_price?: number;
  eval_amount?: number;
}

export interface StockTransaction {
  id: string;
  asset_id: string;
  basket_id: string;
  basket_type: BasketType;
  transaction_type: "BUY" | "SELL" | "EVALUATE" | "DEPOSIT";
  trade_date: string;
  settlement_date: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
  avg_cost_snapshot?: number;
  realized_gain?: number;
  tax_reversal?: number;
}

export interface CashFlow {
  settled_cash: number;
  receivable_cash: number;
}

interface TaxStore {
  portfolio: PortfolioItem[];
  transactions: StockTransaction[];
  cash_flow: CashFlow;
  isLoading: boolean;
  error: string | null;
  fetchDashboard: () => Promise<void>;
  buyStock: (data: any) => Promise<void>;
  evaluateStocks: (data: any) => Promise<void>;
  sellStock: (data: any) => Promise<void>;
  depositCash: (data: any) => Promise<void>;
}

const API_URL = "http://localhost:8000/api/tax";

export const useTaxStore = create<TaxStore>((set) => ({
  portfolio: [],
  transactions: [],
  cash_flow: { settled_cash: 0, receivable_cash: 0 },
  isLoading: false,
  error: null,

  fetchDashboard: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.get(`${API_URL}/dashboard`);
      set({
        portfolio: response.data.portfolio,
        transactions: response.data.transactions,
        cash_flow: response.data.cash_flow,
        isLoading: false,
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  depositCash: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await axios.post(`${API_URL}/deposit`, data);
      set((state) => {
        state.fetchDashboard();
        return { isLoading: false };
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  buyStock: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await axios.post(`${API_URL}/buy`, data);
      set((state) => {
        state.fetchDashboard();
        return { isLoading: false };
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  evaluateStocks: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await axios.post(`${API_URL}/evaluate`, data);
      set((state) => {
        state.fetchDashboard();
        return { isLoading: false };
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  sellStock: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await axios.post(`${API_URL}/sell`, data);
      set((state) => {
        state.fetchDashboard();
        return { isLoading: false };
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },
}));
