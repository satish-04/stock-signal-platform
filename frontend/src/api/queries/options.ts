import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/api/client'
import type { BestOptionsResponse } from '@/api/types/options'

export function useBestOptions(symbol: string | undefined) {
  return useQuery({
    queryKey: ['options', 'best', symbol],
    queryFn: () => apiGet<BestOptionsResponse>(`/api/v1/options/best/${symbol}`),
    enabled: !!symbol,
    retry: false,
  })
}
