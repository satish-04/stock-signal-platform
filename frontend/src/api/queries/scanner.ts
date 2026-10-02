import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { apiGet, apiPost } from '@/api/client'
import type {
  LatestOptionsScanResponse,
  OptionsScanResponse,
  StartOptionsScanRequest,
  StartOptionsScanResponse,
} from '@/api/types/scanner'

const LATEST_KEY = ['scanner', 'options', 'latest']

export function useLatestOptionsScan() {
  return useQuery({
    queryKey: LATEST_KEY,
    queryFn: () => apiGet<LatestOptionsScanResponse>('/api/v1/scanner/options/latest'),
  })
}

// Polls one scan while it runs. A running scan carries no results, so each poll is small;
// the full results are fetched once, through the latest query, when the scan finishes.
export function useOptionsScanProgress(scanId: string | undefined) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['scanner', 'options', 'detail', scanId],
    queryFn: () => apiGet<OptionsScanResponse>(`/api/v1/scanner/options/${scanId}`),
    enabled: !!scanId,
    refetchInterval: (current) => (current.state.data?.scan.status === 'running' ? 2_000 : false),
  })
  const status = query.data?.scan.status

  useEffect(() => {
    if (status && status !== 'running') {
      void queryClient.invalidateQueries({ queryKey: LATEST_KEY })
    }
  }, [status, queryClient])

  return query
}

export function useStartOptionsScan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: StartOptionsScanRequest) =>
      apiPost<StartOptionsScanResponse>('/api/v1/scanner/options', request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: LATEST_KEY }),
  })
}
