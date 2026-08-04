import { useMutation } from '@tanstack/react-query'
import { apiPost } from '@/api/client'
import type { TradePlanRequest, TradePlanResponse } from '@/api/types/risk'

export function useEvaluateTradePlan() {
  return useMutation({
    mutationFn: (request: TradePlanRequest) => apiPost<TradePlanResponse>('/api/v1/risk/trade-plan', request),
  })
}
