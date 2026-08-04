import type { TradePlanResponse } from './risk'

export type OrderIntentStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'SUBMITTED' | 'DUPLICATE' | 'FAILED'

export type OrderIntentTradePlanRequest = TradePlanResponse

export interface OrderIntentResponse {
  intent_id: string
  idempotency_key: string
  status: OrderIntentStatus
  symbol: string
  option_symbol: string
  side: string
  order_type: string
  quantity: number
  limit_price: string
  broker_response: Record<string, unknown> | null
}
