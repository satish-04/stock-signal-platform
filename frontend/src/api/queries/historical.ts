import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/api/client'
import type { HistoricalBarsResponse } from '@/api/types/historical'
import type { TechnicalAnalysisResponse } from '@/api/types/analysis'

export type MarketQueryParams = {
  duration?: string
  bar_size?: string
  use_rth?: boolean
}

export function useHistoricalBars(symbol: string | undefined, params: MarketQueryParams = {}) {
  return useQuery({
    queryKey: ['historical', symbol, params],
    queryFn: () => apiGet<HistoricalBarsResponse>(`/api/v1/historical/${symbol}`, params),
    enabled: !!symbol,
    retry: false,
  })
}

export function useTechnicalAnalysis(symbol: string | undefined, params: MarketQueryParams = {}) {
  return useQuery({
    queryKey: ['analysis', symbol, params],
    queryFn: () => apiGet<TechnicalAnalysisResponse>(`/api/v1/analysis/${symbol}`, params),
    enabled: !!symbol,
    retry: false,
  })
}
