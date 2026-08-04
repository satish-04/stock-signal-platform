import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from '@/api/client'
import type { OrderExecutionResponse } from '@/api/types/orderExecutions'
import { TERMINAL_EXECUTION_STATUSES as TERMINAL } from '@/api/types/orderExecutions'

export function useCreateExecutionFromIntent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (intentId: string) =>
      apiPost<OrderExecutionResponse>(`/api/v1/order-executions/from-intent/${intentId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['order-executions'] }),
  })
}

export function useExecution(executionId: string | undefined) {
  return useQuery({
    queryKey: ['order-executions', 'detail', executionId],
    queryFn: () => apiGet<OrderExecutionResponse>(`/api/v1/order-executions/${executionId}`),
    enabled: !!executionId,
    refetchInterval: (query) => {
      const data = query.state.data as OrderExecutionResponse | undefined
      if (data && TERMINAL.includes(data.status)) return false
      return 4_000
    },
  })
}

export function useSubmitExecution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (executionId: string) =>
      apiPost<OrderExecutionResponse>(`/api/v1/order-executions/${executionId}/submit`),
    onSuccess: (_, executionId) => {
      queryClient.invalidateQueries({ queryKey: ['order-executions', 'detail', executionId] })
    },
  })
}

export function useCancelExecution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (executionId: string) =>
      apiPost<OrderExecutionResponse>(`/api/v1/order-executions/${executionId}/cancel`),
    onSuccess: (_, executionId) => {
      queryClient.invalidateQueries({ queryKey: ['order-executions', 'detail', executionId] })
    },
  })
}
