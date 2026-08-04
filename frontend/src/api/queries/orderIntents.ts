import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '@/api/client'
import type { OrderIntentResponse, OrderIntentTradePlanRequest } from '@/api/types/orderIntents'

export function useCreateOrderIntent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: OrderIntentTradePlanRequest) =>
      apiPost<OrderIntentResponse>('/api/v1/order-intents', request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['order-intents'] }),
  })
}

export function useSubmitOrderIntent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: OrderIntentTradePlanRequest) =>
      apiPost<OrderIntentResponse>('/api/v1/order-intents/submit', request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['order-intents'] }),
  })
}
