import { useMutation, useQuery } from '@tanstack/react-query'
import { apiGet, apiPost } from '@/api/client'
import type { BacktestRequest, BacktestResponse, MarketRegimeResponse } from '@/api/types/quant'

export function useMarketRegime(symbol = 'SPY') {
  return useQuery({
    queryKey: ['quant', 'regime', symbol],
    queryFn: () => apiGet<MarketRegimeResponse>('/api/v1/quant/regime', { symbol }),
    staleTime: 10 * 60_000,
    retry: false,
  })
}

export function useBacktest() {
  return useMutation({
    mutationFn: (request: BacktestRequest) => apiPost<BacktestResponse>('/api/v1/quant/backtest', request),
  })
}
