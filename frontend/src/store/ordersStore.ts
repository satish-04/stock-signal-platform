import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface OrderBlotterEntry {
  intentId: string
  executionId?: string
  symbol: string
  optionSymbol: string
  side: string
  quantity: number
  createdAt: string
}

interface OrdersState {
  entries: OrderBlotterEntry[]
  addIntent: (entry: OrderBlotterEntry) => void
  linkExecution: (intentId: string, executionId: string) => void
}

// The backend exposes no "list order intents/executions" endpoint (create + lookup-by-id
// only), so the Orders page tracks what this browser session created as a local blotter.
export const useOrdersStore = create<OrdersState>()(
  persist(
    (set) => ({
      entries: [],
      addIntent: (entry) => set((state) => ({ entries: [entry, ...state.entries].slice(0, 100) })),
      linkExecution: (intentId, executionId) =>
        set((state) => ({
          entries: state.entries.map((e) => (e.intentId === intentId ? { ...e, executionId } : e)),
        })),
    }),
    { name: 'stock-signal-orders-blotter' },
  ),
)
