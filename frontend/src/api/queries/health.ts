import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/api/client'
import type { HealthResponse } from '@/api/types/health'
import type { WorkerHealthResponse } from '@/api/types/jobs'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiGet<HealthResponse>('/health'),
    refetchInterval: 10_000,
  })
}

export function useWorkerHealth() {
  return useQuery({
    queryKey: ['background-jobs', 'health'],
    queryFn: () => apiGet<WorkerHealthResponse>('/api/v1/background-jobs/health'),
    refetchInterval: 10_000,
  })
}
