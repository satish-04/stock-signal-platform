import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/api/client'
import type { SignalListResponse, SignalStatus, TechnicalSignalResponse, TradeSignalResponse } from '@/api/types/signals'

export function useSignals(params: { status?: SignalStatus; symbol?: string; limit?: number } = {}) {
  return useQuery({
    queryKey: ['signals', params],
    queryFn: () => apiGet<SignalListResponse>('/api/v1/signals', params),
    refetchInterval: 5_000,
  })
}

export function useSignal(signalId: string | undefined) {
  return useQuery({
    queryKey: ['signals', 'detail', signalId],
    queryFn: () => apiGet<TradeSignalResponse>(`/api/v1/signals/${signalId}`),
    enabled: !!signalId,
  })
}

export function useTechnicalSignal(
  symbol: string | undefined,
  params: { duration?: string; bar_size?: string; use_rth?: boolean } = {},
) {
  return useQuery({
    queryKey: ['signals', 'technical', symbol, params],
    queryFn: () => apiGet<TechnicalSignalResponse>(`/api/v1/signals/technical/${symbol}`, params),
    enabled: !!symbol,
  })
}
