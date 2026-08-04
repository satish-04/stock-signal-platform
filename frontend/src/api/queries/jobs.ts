import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/api/client'
import type { BackgroundJobResponse } from '@/api/types/jobs'

export function useBackgroundJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ['background-jobs', 'detail', jobId],
    queryFn: () => apiGet<BackgroundJobResponse>(`/api/v1/background-jobs/${jobId}`),
    enabled: !!jobId,
    refetchInterval: 4_000,
  })
}
