import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from '@/api/client'
import type {
  ApproveWorkflowRequest,
  CreateWorkflowRequest,
  FailWorkflowRequest,
  TradingWorkflow,
  TransitionWorkflowRequest,
} from '@/api/types/workflows'

export function useWorkflows(accountId: string) {
  return useQuery({
    queryKey: ['trading-workflows', accountId],
    queryFn: () => apiGet<TradingWorkflow[]>('/api/v1/trading-workflows', { account_id: accountId }),
    enabled: !!accountId,
    refetchInterval: 5_000,
  })
}

export function useWorkflow(workflowId: string | undefined) {
  return useQuery({
    queryKey: ['trading-workflows', 'detail', workflowId],
    queryFn: () => apiGet<TradingWorkflow>(`/api/v1/trading-workflows/${workflowId}`),
    enabled: !!workflowId,
    refetchInterval: 5_000,
  })
}

export function useCreateWorkflow(accountId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: CreateWorkflowRequest) => apiPost<TradingWorkflow>('/api/v1/trading-workflows', request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trading-workflows', accountId] }),
  })
}

function useWorkflowAction<TBody = void>(action: 'transition' | 'approve' | 'fail' | 'retry') {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ workflowId, body }: { workflowId: string; body?: TBody }) =>
      apiPost<TradingWorkflow>(`/api/v1/trading-workflows/${workflowId}/${action}`, body),
    onSuccess: (_, { workflowId }) => {
      queryClient.invalidateQueries({ queryKey: ['trading-workflows', 'detail', workflowId] })
      queryClient.invalidateQueries({ queryKey: ['trading-workflows'] })
    },
  })
}

export const useTransitionWorkflow = () => useWorkflowAction<TransitionWorkflowRequest>('transition')
export const useApproveWorkflow = () => useWorkflowAction<ApproveWorkflowRequest>('approve')
export const useFailWorkflow = () => useWorkflowAction<FailWorkflowRequest>('fail')
export const useRetryWorkflow = () => useWorkflowAction('retry')
