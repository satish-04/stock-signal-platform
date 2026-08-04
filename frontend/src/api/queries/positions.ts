import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from '@/api/client'
import type {
  MarkPositionRequest,
  PortfolioSummaryResponse,
  PositionListResponse,
  PositionResponse,
  PositionStatus,
} from '@/api/types/positions'

export function usePositions(accountId: string, status?: PositionStatus) {
  return useQuery({
    queryKey: ['positions', accountId, status],
    queryFn: () => apiGet<PositionListResponse>('/api/v1/positions', { account_id: accountId, status }),
    enabled: !!accountId,
    refetchInterval: 5_000,
  })
}

export function usePortfolioSummary(accountId: string) {
  return useQuery({
    queryKey: ['positions', 'portfolio-summary', accountId],
    queryFn: () => apiGet<PortfolioSummaryResponse>(`/api/v1/positions/portfolio/${accountId}/summary`),
    enabled: !!accountId,
    refetchInterval: 5_000,
  })
}

export function useMarkPosition(accountId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ positionId, markPrice }: { positionId: string; markPrice: string }) =>
      apiPost<PositionResponse>(`/api/v1/positions/${positionId}/mark`, {
        mark_price: markPrice,
      } satisfies MarkPositionRequest),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions', accountId] })
      queryClient.invalidateQueries({ queryKey: ['positions', 'portfolio-summary', accountId] })
    },
  })
}
