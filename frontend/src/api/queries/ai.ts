import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/api/client'
import type { AIRecommendationResponse } from '@/api/types/ai'

export function useAIRecommendation(symbol: string | undefined) {
  return useQuery({
    queryKey: ['ai', 'recommendation', symbol],
    queryFn: () => apiGet<AIRecommendationResponse>(`/api/v1/ai/recommendation/${symbol}`),
    enabled: !!symbol,
    retry: false,
  })
}
