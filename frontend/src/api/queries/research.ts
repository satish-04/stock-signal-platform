import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/api/client'
import type { ResearchArtifactListResponse } from '@/api/types/research'

export function useResearchArtifacts(symbol: string | undefined) {
  return useQuery({
    queryKey: ['research', 'artifacts', symbol],
    queryFn: () => apiGet<ResearchArtifactListResponse>('/api/v1/research/artifacts', { symbol, limit: 50 }),
    enabled: !!symbol,
  })
}
