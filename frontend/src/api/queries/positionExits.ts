import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/api/client'
import type { ExitSignalResponse } from '@/api/types/positionExits'

export function useExitsByPosition(positionId: string | undefined) {
  return useQuery({
    queryKey: ['position-exits', 'by-position', positionId],
    queryFn: () => apiGet<ExitSignalResponse[]>(`/api/v1/position-exits/by-position/${positionId}`),
    enabled: !!positionId,
  })
}
