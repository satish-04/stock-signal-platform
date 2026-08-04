export type ExecutionStatus =
  | 'CREATED'
  | 'SUBMISSION_PENDING'
  | 'SUBMITTED'
  | 'ACKNOWLEDGED'
  | 'PARTIALLY_FILLED'
  | 'FILLED'
  | 'CANCEL_PENDING'
  | 'CANCELLED'
  | 'REJECTED'
  | 'FAILED'

export const TERMINAL_EXECUTION_STATUSES: ExecutionStatus[] = ['FILLED', 'CANCELLED', 'REJECTED', 'FAILED']

export interface OrderExecutionResponse {
  execution_id: string
  intent_id: string
  idempotency_key: string
  symbol: string
  option_symbol: string
  side: string
  order_type: string
  requested_quantity: number
  limit_price: string
  status: ExecutionStatus
  broker_order_id: string | null
  broker_status: string | null
  filled_quantity: number
  remaining_quantity: number
  average_fill_price: string | null
  submitted_at: string | null
  acknowledged_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
  status_reason: string | null
  broker_response: Record<string, unknown> | null
}

export interface ExecutionUpdateRequest {
  status: ExecutionStatus
  broker_order_id?: string | null
  broker_status?: string | null
  filled_quantity?: number | null
  remaining_quantity?: number | null
  average_fill_price?: string | null
  status_reason?: string | null
  broker_response?: Record<string, unknown> | null
}
